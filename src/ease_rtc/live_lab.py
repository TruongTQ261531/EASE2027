"""Real browser-call fault experiment in a private, loopback-only Docker network namespace."""

import argparse
import hashlib
import json
import os
import platform
import random
import socket
import subprocess
import sys
import time
import uuid
from pathlib import Path
from typing import Literal

import psutil
from playwright.sync_api import sync_playwright
from pydantic import Field, model_validator

from ease_rtc.collect import local_server
from ease_rtc.features import mean_features, normalize
from ease_rtc.io import read_json, read_jsonl, sha256, source_provenance, write_json, write_jsonl
from ease_rtc.lab_sensors import verify_live
from ease_rtc.relay import local_turn
from ease_rtc.schema import ClosedModel, FeatureWindow


class LiveProtocol(ClosedModel):
    version: str = "live-feasibility-v1"
    duration_s: float = Field(default=11, ge=8)
    on_s: float = Field(default=3, ge=2)
    off_s: float = Field(default=7, ge=4)
    network_loss_percent: float = Field(default=30, ge=1, le=80)
    busy_ms: int = Field(default=850, ge=500, le=950)
    sample_interval_ms: int = Field(default=250, ge=100, le=500)
    seeds: list[int] = [42, 43, 44]
    engines: list[str] = ["chromium", "firefox"]
    schedule_seed: int = 20271116
    network_backend: Literal["netem", "unimpaired"] = "netem"
    conditions: list[Literal["normal", "network_loss", "compute_contention", "source_freeze"]] = [
        "normal",
        "network_loss",
        "compute_contention",
        "source_freeze",
    ]

    @model_validator(mode="after")
    def valid_design(self):
        if not self.on_s + 2 <= self.off_s <= self.duration_s - 2:
            raise ValueError("Require observation and recovery intervals >=2 seconds")
        if not self.seeds or len(set(self.seeds)) != len(self.seeds):
            raise ValueError("Require nonempty unique source seeds")
        if not self.engines or set(self.engines) - {"chromium", "firefox"}:
            raise ValueError("Unsupported browser engine")
        if self.network_backend == "unimpaired" and "network_loss" in self.conditions:
            raise ValueError("Cannot request a network fault without a supported backend")
        if not self.conditions or len(set(self.conditions)) != len(self.conditions):
            raise ValueError("Require nonempty unique conditions")
        return self


def require_private_namespace():
    expected_parent = os.environ.get("EASE_PARENT_NETNS")
    current = os.readlink("/proc/self/ns/net")
    if not Path("/.dockerenv").exists() or not expected_parent or current == expected_parent:
        raise RuntimeError("Must run in the lab's distinct Docker network namespace")
    allowed = {"lo", "eth0"} if os.environ.get("EASE_PRIVATE_INTERNAL_NETWORK") == "1" else {"lo"}
    if not set(psutil.net_if_addrs()).issubset(allowed):
        raise RuntimeError("Unexpected interface outside the private lab namespace")


def tc(*arguments):
    require_private_namespace()
    return subprocess.run(["tc", *arguments], check=True, capture_output=True, text=True, timeout=3)


def setup_network():
    # The classifier selects only internal TURN relay UDP ports. CDP/signaling stay unshaped.
    tc("qdisc", "add", "dev", "lo", "root", "handle", "1:", "prio", "bands", "3")
    tc("qdisc", "add", "dev", "lo", "parent", "1:3", "handle", "30:", "netem", "loss", "0%")
    tc(
        "filter",
        "add",
        "dev",
        "lo",
        "protocol",
        "ip",
        "parent",
        "1:",
        "prio",
        "1",
        "u32",
        "match",
        "ip",
        "protocol",
        "17",
        "0xff",
        "match",
        "ip",
        "dport",
        "49152",
        "0xffc0",
        "flowid",
        "1:3",
    )


def set_loss(percent):
    tc(
        "qdisc",
        "change",
        "dev",
        "lo",
        "parent",
        "1:3",
        "handle",
        "30:",
        "netem",
        "loss",
        f"{percent}%",
    )


def launch(engine, playwright):
    names = {"chrome", "chromium", "chrome-headless-shell", "firefox", "firefox-bin"}

    def is_browser(process):
        try:
            return Path(process.exe()).name in names
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            return False

    before = psutil.Process().children(recursive=True)
    prior_browsers = {p.pid for p in before if is_browser(p)}
    before = {p.pid for p in before}
    browser_type = getattr(playwright, engine)
    browser = browser_type.launch(
        headless=True,
        **(
            {
                "args": [
                    "--no-sandbox",
                    "--disable-background-timer-throttling",
                    "--disable-renderer-backgrounding",
                ]
            }
            if engine == "chromium"
            else {"firefox_user_prefs": {"media.peerconnection.ice.loopback": True}}
        ),
    )
    children = [p for p in psutil.Process().children(recursive=True) if p.pid not in before]
    candidates = [
        p
        for p in children
        if is_browser(p) and not any(parent.pid in prior_browsers for parent in p.parents())
    ]
    ids = {p.pid for p in candidates}
    roots = [p for p in candidates if not any(parent.pid in ids for parent in p.parents())]
    if len(roots) != 1:
        browser.close()
        raise RuntimeError(
            f"Cannot establish a unique browser process identity: "
            f"candidates={len(candidates)}, roots={len(roots)}"
        )
    return browser, roots[0].pid, browser_type.executable_path


def run_call(
    output: Path, engine: str, condition: str, static: bool, seed: int, protocol: LiveProtocol
) -> dict:
    run_id = str(uuid.uuid4())
    raw, oracle = output / "raw" / run_id, output / "oracle" / run_id
    raw.mkdir(parents=True)
    oracle.mkdir(parents=True)
    samples, observations, pixels, events = [], [], [], []
    on_ms, off_ms, failure, version = None, None, None, "unavailable"
    sensor, browsers, executable, turn_hash = None, [], "unavailable", None
    wall = time.monotonic()
    try:
        with (
            local_turn(
                relay_ports=(49152, 49215),
                relay_ip=next(
                    a.address for a in psutil.net_if_addrs()["eth0"] if a.family == socket.AF_INET
                ),
            ) as (configuration, turn_hash),
            local_server() as url,
            sync_playwright() as playwright,
        ):
            sender_browser, sender_pid, executable = launch(engine, playwright)
            browsers.append(sender_browser)
            receiver_browser, _, _ = launch(engine, playwright)
            browsers.append(receiver_browser)
            version = sender_browser.version
            sender, receiver = sender_browser.new_page(), receiver_browser.new_page()
            for role, page in [("sender", sender), ("receiver", receiver)]:
                page.goto(url)
                page.evaluate(
                    "o => window.initialize(o)",
                    {
                        "role": role,
                        "seed": seed,
                        "width": 320,
                        "height": 180,
                        "fps": 20,
                        "rtcConfiguration": configuration,
                    },
                )
            answer = receiver.evaluate("o => window.answer(o)", sender.evaluate("window.offer()"))
            sender.evaluate("a => window.accept(a)", answer)
            receiver.wait_for_function("window.isReady()", timeout=15000)
            if static:
                sender.evaluate("window.intervene('capture_pause')")
            time.sleep(0.5)
            start = time.monotonic()
            stop_file = oracle / "stop-observer"
            sensor = subprocess.Popen(
                [
                    sys.executable,
                    "-m",
                    "ease_rtc.lab_sensors",
                    "--sender-pid",
                    str(sender_pid),
                    "--start",
                    str(start),
                    "--stop-file",
                    str(stop_file),
                    "--output",
                    str(oracle / "os.jsonl"),
                ]
                + (["--without-netem"] if protocol.network_backend == "unimpaired" else []),
                stdout=subprocess.DEVNULL,
                stderr=(oracle / "sensor.log").open("w"),
            )
            index = 0
            while (elapsed := time.monotonic() - start) < protocol.duration_s:
                if on_ms is None and elapsed >= protocol.on_s:
                    if condition == "network_loss":
                        set_loss(protocol.network_loss_percent)
                    elif condition == "source_freeze":
                        sender.evaluate("window.intervene('capture_pause')")
                    elif condition == "compute_contention":
                        sender.evaluate(
                            """busy => {
                          window.loadTimer = setInterval(() => {
                            const end=performance.now()+busy;
                            while(performance.now()<end) { Math.sqrt(Math.random()); }
                          }, 1000);
                        }""",
                            protocol.busy_ms,
                        )
                    on_ms = (time.monotonic() - start) * 1000
                    events.append({"command": condition, "actual_ms": on_ms})
                if on_ms is not None and off_ms is None and elapsed >= protocol.off_s:
                    if protocol.network_backend == "netem":
                        set_loss(0)
                    if condition == "compute_contention":
                        sender.evaluate("clearInterval(window.loadTimer)")
                    if condition == "source_freeze":
                        sender.evaluate("window.recover()")
                    off_ms = (time.monotonic() - start) * 1000
                    events.append({"command": "recover", "actual_ms": off_ms})
                a = time.monotonic()
                rx = receiver.evaluate("window.observe()")
                b = time.monotonic()
                timestamp = ((a + b) / 2 - start) * 1000
                samples.append(
                    {
                        "monotonic_ms": timestamp,
                        "collection_span_ms": (b - a) * 1000,
                        "sender_stats": [],
                        "receiver_stats": rx["stats"],
                    }
                )
                observations.append(
                    {
                        "monotonic_ms": timestamp,
                        "connection_state": rx["connection_state"],
                        "receiver_fingerprint": rx["receiver_fingerprint"],
                    }
                )
                # Pixel observer does not read generator state, pause flags or injection logs.
                p0 = time.monotonic()
                try:
                    image = sender.screenshot(
                        clip={"x": 8, "y": 8, "width": 320, "height": 180}, timeout=180
                    )
                    pixels.append(
                        {
                            "monotonic_ms": (time.monotonic() - start) * 1000,
                            "source_pixel_sha256": hashlib.sha256(image).hexdigest(),
                            "capture_span_ms": (time.monotonic() - p0) * 1000,
                        }
                    )
                except Exception:
                    pixels.append(
                        {
                            "monotonic_ms": (time.monotonic() - start) * 1000,
                            "source_pixel_sha256": None,
                            "capture_span_ms": (time.monotonic() - p0) * 1000,
                        }
                    )
                index += 1
                time.sleep(
                    max(0, start + index * protocol.sample_interval_ms / 1000 - time.monotonic())
                )
            stop_file.touch()
            sensor.wait(timeout=5)
            for browser in browsers:
                browser.close()
            browsers.clear()
    except Exception as error:
        failure = f"{type(error).__name__}: {error}"
    finally:
        if protocol.network_backend == "netem":
            set_loss(0)
        if sensor is not None and sensor.poll() is None:
            (oracle / "stop-observer").touch()
            sensor.wait(timeout=5)
    os_rows = read_jsonl(oracle / "os.jsonl") if (oracle / "os.jsonl").exists() else []
    verdict = verify_live(
        condition,
        static,
        os_rows,
        pixels,
        on_ms,
        off_ms,
        protocol.duration_s * 1000,
        failure is None,
    )
    rows = normalize(samples, observations)
    write_jsonl(raw / "stats.jsonl", samples)
    write_jsonl(raw / "observations.jsonl", observations)
    write_jsonl(oracle / "pixels.jsonl", pixels)
    write_json(
        oracle / "request.json",
        {
            "condition": condition,
            "static_control": static,
            "seed": seed,
            "protocol": protocol.model_dump(),
            "events": events,
        },
    )
    write_json(oracle / "verdict.json", verdict)
    windows = []
    buckets = {}
    for t, features in rows:
        buckets.setdefault(int(t // 1000), []).append(features)
    for index, features in sorted(buckets.items()):
        windows.append(
            FeatureWindow(
                run_id=run_id,
                session_id=run_id,
                window_start_ms=index * 1000,
                window_end_ms=(index + 1) * 1000,
                features=mean_features(features),
            ).model_dump()
        )
    write_jsonl(output / "features" / f"{run_id}.jsonl", windows)
    evidence = [
        *raw.glob("*.jsonl"),
        *oracle.glob("*.jsonl"),
        oracle / "request.json",
        oracle / "verdict.json",
        output / "features" / f"{run_id}.jsonl",
    ]
    provenance = source_provenance(Path.cwd())
    provenance["git_commit"] = os.environ.get("EASE_CODE_COMMIT")
    provenance["git_dirty"] = os.environ.get("EASE_CODE_DIRTY", "true") == "true"
    manifest = {
        "schema_version": "2.0",
        "run_id": run_id,
        "session_id": run_id,
        "engine": engine,
        "browser_version": version,
        "browser_executable": executable,
        "condition": condition,
        "static_control": static,
        "seed": seed,
        "host_label": os.environ.get("EASE_HOST_LABEL", "unidentified"),
        "platform": platform.platform(),
        "os_release": platform.freedesktop_os_release(),
        "network_namespace": os.readlink("/proc/self/ns/net"),
        "isolation": "separate browser processes; internal Docker netns; media uses loopback TURN",
        "turn_binary_sha256": turn_hash,
        **provenance,
        "clock": "shared Linux monotonic clock, separate OS sensor process",
        "sample_count": len(samples),
        "on_ms": on_ms,
        "off_ms": off_ms,
        "wall_seconds": time.monotonic() - wall,
        "execution_status": "completed" if failure is None else "failed",
        "failure_reason": failure,
        "verification_status": verdict["verification_status"],
        "files": {str(p.relative_to(output)): sha256(p) for p in evidence},
    }
    write_json(output / "manifests" / f"{run_id}.json", manifest)
    return manifest


def run(protocol: LiveProtocol, output: Path):
    require_private_namespace()
    expected = os.environ.get("EASE_EXPECTED_SOURCE_SHA256")
    if expected and source_provenance(Path.cwd())["source_tree_sha256"] != expected:
        raise ValueError("Container code does not match the source checkout; rebuild the image")
    if output.exists() and any(output.iterdir()):
        raise ValueError("Use a new empty output directory")
    output.mkdir(parents=True, exist_ok=True)
    schedule = [
        (engine, condition, static, seed)
        for seed in protocol.seeds
        for engine in protocol.engines
        for condition, static in [
            ("normal", False),
            ("normal", True),
            ("network_loss", False),
            ("compute_contention", False),
            ("source_freeze", False),
        ]
        if condition in protocol.conditions
    ]
    random.Random(protocol.schedule_seed).shuffle(schedule)
    write_json(output / "protocol.json", {"protocol": protocol.model_dump(), "schedule": schedule})
    manifests = []
    if protocol.network_backend == "netem":
        try:
            setup_network()
        except subprocess.CalledProcessError as error:
            write_json(
                output / "capability_failure.json",
                {
                    "status": "failed",
                    "command": error.cmd,
                    "stderr": error.stderr,
                    "reason": "No successful injection or fault label from capability failure",
                },
            )
            raise
    try:
        for index, (engine, condition, static, seed) in enumerate(schedule, 1):
            manifest = run_call(output, engine, condition, static, seed, protocol)
            manifests.append(manifest)
            print(
                index,
                len(schedule),
                engine,
                condition,
                static,
                manifest["execution_status"],
                manifest["verification_status"],
                flush=True,
            )
    finally:
        if protocol.network_backend == "netem":
            tc("qdisc", "del", "dev", "lo", "root")
    summary = {
        "scope": "live-call measured fault conditions, causal attribution unestablished",
        "runs": len(manifests),
        "completed": sum(m["execution_status"] == "completed" for m in manifests),
        "verified": sum(m["verification_status"] == "verified" for m in manifests),
        "failed": sum(m["execution_status"] == "failed" for m in manifests),
        "ambiguous": sum(m["verification_status"] == "ambiguous" for m in manifests),
        "engines": sorted({m["engine"] for m in manifests}),
        "host_labels": sorted({m["host_label"] for m in manifests}),
        "run_ids": [m["run_id"] for m in manifests],
    }
    write_json(output / "summary.json", summary)
    print(json.dumps(summary), flush=True)
    if summary["failed"]:
        raise RuntimeError("One or more live calls failed; evidence and summary were preserved")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    run(LiveProtocol.model_validate(read_json(args.protocol)), args.output)
