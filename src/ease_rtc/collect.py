import functools
import hashlib
import http.server
import os
import platform
import shutil
import threading
import time
import uuid
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path

import psutil
from playwright.sync_api import sync_playwright

from ease_rtc.io import sha256, source_provenance, write_json, write_jsonl
from ease_rtc.relay import local_turn
from ease_rtc.schema import RunManifest, Scenario
from ease_rtc.verification import verify

WEB = Path(__file__).parent / "web"


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *_args):
        pass


@contextmanager
def local_server():
    handler = functools.partial(QuietHandler, directory=str(WEB))
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    worker = threading.Thread(target=server.serve_forever, daemon=True)
    worker.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}/peer.html"
    finally:
        server.shutdown()
        server.server_close()
        worker.join()


def browser_path() -> str | None:
    configured = os.environ.get("EASE_CHROMIUM_EXECUTABLE")
    if configured:
        if not Path(configured).is_file():
            raise ValueError("EASE_CHROMIUM_EXECUTABLE does not name an existing executable")
        return configured
    return shutil.which("chromium") or shutil.which("google-chrome")


def collect(config: Scenario, output: Path, repo: Path) -> RunManifest:
    run_id, session_id = str(uuid.uuid4()), str(uuid.uuid4())
    raw_dir, oracle_dir = output / "raw" / run_id, output / "oracle" / run_id
    raw_dir.mkdir(parents=True, exist_ok=False)
    oracle_dir.mkdir(parents=True, exist_ok=False)
    observations, source_observations, samples = [], [], []
    actual_start, actual_end, error = None, None, None
    browser_version, executable = "unavailable", browser_path()
    process = psutil.Process()
    cpu_before = sum(process.cpu_times()[:2])
    peak_rss = process.memory_info().rss
    wall_start, start_utc = time.perf_counter(), datetime.now(UTC).isoformat()
    codecs = {}
    turn_hash = None
    try:
        with (
            local_turn() as (rtc_config, turn_hash),
            local_server() as url,
            sync_playwright() as playwright,
        ):
            # Container lacks user namespaces. This browser loads only our local synthetic page.
            browser = playwright.chromium.launch(
                executable_path=executable,
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-background-timer-throttling",
                    "--disable-renderer-backgrounding",
                ],
            )
            browser_version = browser.version
            executable = executable or playwright.chromium.executable_path
            sender_context, receiver_context = browser.new_context(), browser.new_context()
            sender, receiver = sender_context.new_page(), receiver_context.new_page()
            for role, page in [("sender", sender), ("receiver", receiver)]:
                page.goto(url)
                page.evaluate(
                    "options => window.initialize(options)",
                    {
                        "role": role,
                        "seed": config.seed,
                        "width": config.width,
                        "height": config.height,
                        "fps": config.fps,
                        "rtcConfiguration": rtc_config,
                    },
                )
            offer = sender.evaluate("window.offer()")
            answer = receiver.evaluate("offer => window.answer(offer)", offer)
            sender.evaluate("answer => window.accept(answer)", answer)
            receiver.wait_for_function("window.isReady()", timeout=15000)
            sender.wait_for_function("window.isReady()", timeout=15000)
            # Settling time is identical for all conditions; it is not included in features.
            time.sleep(0.5)
            t0, index = time.perf_counter(), 0
            while True:
                elapsed = time.perf_counter() - t0
                if elapsed >= config.duration_s:
                    break
                if actual_start is None and elapsed >= config.intervention_start_s:
                    target = receiver if config.intervention == "connection_close" else sender
                    target.evaluate("kind => window.intervene(kind)", config.intervention)
                    actual_start = (time.perf_counter() - t0) * 1000
                if actual_start is not None and actual_end is None:
                    if elapsed >= config.intervention_end_s:
                        sender.evaluate("window.recover()")
                        actual_end = (time.perf_counter() - t0) * 1000
                sample_start = time.perf_counter()
                tx, rx = sender.evaluate("window.observe()"), receiver.evaluate("window.observe()")
                sample_end = time.perf_counter()
                mono_ms = ((sample_start + sample_end) / 2 - t0) * 1000
                samples.append(
                    {
                        "monotonic_ms": mono_ms,
                        "collection_span_ms": (sample_end - sample_start) * 1000,
                        "sender_stats": tx["stats"],
                        "receiver_stats": rx["stats"],
                    }
                )
                observations.append(
                    {
                        "monotonic_ms": mono_ms,
                        "connection_state": rx["connection_state"],
                        "ice_connection_state": rx["ice_connection_state"],
                        "receiver_fingerprint": rx["receiver_fingerprint"],
                    }
                )
                source_observations.append(
                    {
                        "monotonic_ms": mono_ms,
                        "fingerprint": tx["source_fingerprint"],
                    }
                )
                for item in rx["stats"]:
                    if item["type"] == "codec":
                        codecs[item["id"]] = item
                peak_rss = max(peak_rss, process.memory_info().rss)
                index += 1
                deadline = t0 + index * config.sample_interval_ms / 1000
                time.sleep(max(0.0, deadline - time.perf_counter()))
            browser.close()
    except Exception as exc:
        error = f"{type(exc).__name__}: {exc}"
    stats_file, obs_file = raw_dir / "stats.jsonl", raw_dir / "observations.jsonl"
    source_file, oracle_file = oracle_dir / "source.jsonl", output / "oracle" / f"{run_id}.json"
    write_jsonl(stats_file, samples)
    write_jsonl(obs_file, observations)
    write_jsonl(source_file, source_observations)
    oracle = verify(
        run_id,
        session_id,
        config,
        observations,
        source_observations,
        actual_start,
        actual_end,
        error is None,
    )
    write_json(oracle_file, oracle.model_dump())
    environment = f"{platform.platform()}|{browser_version}|{platform.machine()}|{os.cpu_count()}"
    manifest = RunManifest(
        run_id=run_id,
        session_id=session_id,
        environment_id=hashlib.sha256(environment.encode()).hexdigest()[:16],
        started_at_utc=start_utc,
        config=config,
        browser_version=browser_version,
        browser_executable=executable or "unavailable",
        platform=platform.platform(),
        python_version=platform.python_version(),
        cpu_count=os.cpu_count() or 1,
        **source_provenance(repo),
        media_source_sha256=sha256(WEB / "peer.html"),
        turn_binary_sha256=turn_hash,
        clock=(
            "Python perf_counter midpoint around sequential sender/receiver getStats calls; "
            "collection_span_ms bounds sampling skew. Browser timestamp fields stay raw."
        ),
        codecs=list(codecs.values()),
        sample_count=len(samples),
        collection_duration_s=time.perf_counter() - wall_start,
        process_cpu_s=sum(process.cpu_times()[:2]) - cpu_before,
        process_peak_rss_bytes=peak_rss,
        execution_status="completed" if error is None else "failed",
        failure_reason=error,
        files={
            str(p.relative_to(output)): sha256(p)
            for p in [stats_file, obs_file, source_file, oracle_file]
        },
    )
    write_json(output / "manifests" / f"{run_id}.json", manifest.model_dump())
    if error:
        raise RuntimeError(f"Run {run_id} failed; evidence preserved in {output}: {error}")
    return manifest
