"""Independent measurement-path feasibility probes, NOT WebRTC causal labels.

No observer reads the requested fault flag to infer its measured outcome. These probes
exercise instrumentation before integration into an isolated browser-call experiment.
"""

import argparse
import hashlib
import random
import socket
import subprocess
import sys
import threading
import time
from pathlib import Path

import psutil

from ease_rtc.io import sha256, write_json


def verdict(family: str, measurements: dict, expected_effect: bool) -> dict:
    """Keep measured conditions separate from requests; absent evidence never verifies."""
    if family == "network":
        sent, received = measurements.get("sent"), measurements.get("unique_received")
        if not sent or received is None or not 0 <= received <= sent:
            return {"status": "ambiguous", "measured_effect": None}
        measured = received / sent < 0.8
    elif family == "compute":
        cpu = measurements.get("cpu_core_percent")
        if cpu is None or not 0 <= cpu <= 110:
            return {"status": "ambiguous", "measured_effect": None}
        measured = cpu > 50
    elif family == "media":
        hashes = measurements.get("decoded_frame_hashes", [])
        if len(hashes) < 10:
            return {"status": "ambiguous", "measured_effect": None}
        measured = len(set(hashes)) / len(hashes) < 0.5
    else:
        raise ValueError("Unknown oracle probe family")
    return {
        "status": "verified" if measured == expected_effect else "failed",
        "measured_effect": measured,
    }


def network_probe(effect: bool, seed: int) -> dict:
    """Observe unique delivered sequences on a socket separate from the dropping relay."""
    with (
        socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as relay,
        socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as receiver,
        socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sender,
    ):
        relay.bind(("127.0.0.1", 0))
        receiver.bind(("127.0.0.1", 0))
        relay.settimeout(0.2)
        receiver.settimeout(0.2)
        relay_address, target = relay.getsockname(), receiver.getsockname()
        done = threading.Event()
        delivered, errors = [], []
        # This schedule is only for intervention execution, never observer verification.
        drops = set(random.Random(seed).sample(range(60), 20)) if effect else set()

        def inject():
            try:
                while not done.is_set():
                    try:
                        payload, _ = relay.recvfrom(4096)
                    except TimeoutError:
                        continue
                    if int(payload) not in drops:
                        relay.sendto(payload, target)
            except Exception as error:
                errors.append(str(error))

        def observe():
            while not done.is_set():
                try:
                    payload, _ = receiver.recvfrom(4096)
                    delivered.append({"sequence": int(payload), "clock": time.monotonic()})
                except TimeoutError:
                    continue

        injector = threading.Thread(target=inject)
        observer = threading.Thread(target=observe)
        injector.start()
        observer.start()
        start = time.monotonic()
        try:
            for sequence in range(60):
                sender.sendto(str(sequence).encode(), relay_address)
                time.sleep(0.005)
            time.sleep(0.25)
        finally:
            done.set()
            injector.join()
            observer.join()
        return {
            "sent": 60,
            "unique_received": len({r["sequence"] for r in delivered}),
            "receiver_observations": delivered,
            "duration_s": time.monotonic() - start,
            "injector_errors": errors,
            "measurement_layer": "loopback UDP probe; not browser RTP or path packet loss",
        }


def compute_probe(effect: bool) -> dict:
    code = (
        "import time; end=time.monotonic()+3;\nwhile time.monotonic()<end: pass"
        if effect
        else "import time; time.sleep(3)"
    )
    child = subprocess.Popen([sys.executable, "-c", code])
    try:
        process = psutil.Process(child.pid)
        creation = process.create_time()
        cpu = process.cpu_percent(interval=0.8)
        return {
            "pid": child.pid,
            "process_create_time": creation,
            "cpu_core_percent": cpu,
            "rss_bytes": process.memory_info().rss,
            "measurement_layer": "OS process CPU accounting; one worker, not browser overload",
        }
    finally:
        child.terminate()
        child.wait(timeout=5)


def media_probe(effect: bool, output: Path) -> dict:
    # Generate a fixture, then use a different decoder process to observe actual decoded frames.
    video = output / "fixture.mkv"
    command = ["ffmpeg", "-v", "error", "-f", "lavfi", "-i", "testsrc2=s=64x64:r=10:d=2"]
    if effect:
        command += ["-vf", "trim=end_frame=1,tpad=stop_mode=clone:stop_duration=1.9"]
    subprocess.run(
        [*command, "-c:v", "ffv1", "-threads", "1", str(video)],
        check=True,
        capture_output=True,
        timeout=20,
    )
    result = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", str(video), "-f", "framemd5", "-"],
        check=True,
        capture_output=True,
        text=True,
        timeout=20,
    )
    hashes = [
        line.split(",")[-1].strip()
        for line in result.stdout.splitlines()
        if line and not line.startswith("#")
    ]
    return {
        "decoded_frame_hashes": hashes,
        "fixture_sha256": sha256(video),
        "measurement_layer": "separate FFmpeg decode of generated file; not live camera failure",
    }


def run_probes(output: Path, seeds: list[int]) -> dict:
    if output.exists() and any(output.iterdir()):
        raise ValueError("Use a new empty output directory; evidence must be retained")
    rows = []
    for seed in seeds:
        for family in ["network", "compute", "media"]:
            for effect in [False, True]:
                relative = Path(f"{seed}-{family}-{'intervention' if effect else 'sham'}")
                directory = output / relative
                directory.mkdir(parents=True)
                request = {"family": family, "requested_effect": effect, "seed": seed}
                write_json(directory / "request.json", request)
                try:
                    if family == "network":
                        measured = network_probe(effect, seed)
                    elif family == "compute":
                        measured = compute_probe(effect)
                    else:
                        measured = media_probe(effect, directory)
                    decision = verdict(family, measured, effect)
                except Exception as error:
                    measured = {"error": f"{type(error).__name__}: {error}"}
                    decision = {"status": "failed", "measured_effect": None}
                write_json(directory / "measurement.json", measured)
                rows.append(
                    {
                        **request,
                        **decision,
                        "request_sha256": sha256(directory / "request.json"),
                        "measurement_path": str(relative / "measurement.json"),
                        "measurement_sha256": sha256(directory / "measurement.json"),
                        "causal_root_cause": "unestablished",
                    }
                )
    report = {
        "scope": "Independent measurement paths on isolated probes, NOT WebRTC fault labels",
        "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "trials": len(rows),
        "verified": sum(r["status"] == "verified" for r in rows),
        "failed": sum(r["status"] == "failed" for r in rows),
        "ambiguous": sum(r["status"] == "ambiguous" for r in rows),
        "results": rows,
        "limitation": "No integration with browser interventions or degradation attribution; "
        "network loss is only within a local UDP relay; CPU load is not saturation; "
        "frozen file is not a failed camera. Thresholds are feasibility heuristics.",
    }
    write_json(output / "summary.json", report)
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seeds", type=int, nargs="+", default=[42, 43, 44])
    args = parser.parse_args()
    report = run_probes(args.output, args.seeds)
    print({k: report[k] for k in ["trials", "verified", "failed", "ambiguous", "scope"]})
    raise SystemExit(1 if report["failed"] or report["ambiguous"] else 0)
