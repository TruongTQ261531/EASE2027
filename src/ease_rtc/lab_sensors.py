"""OS-side observer. Receives process identity and clock, never an intervention schedule."""

import argparse
import json
import statistics
import subprocess
import time
from pathlib import Path

import psutil


def netem_counters() -> dict:
    result = subprocess.run(
        ["tc", "-s", "-j", "qdisc", "show", "dev", "lo"],
        capture_output=True,
        text=True,
        check=True,
        timeout=2,
    )
    matches = [
        row
        for row in json.loads(result.stdout)
        if row.get("kind") == "netem" and row.get("handle") == "30:"
    ]
    if len(matches) != 1:
        raise ValueError("Expected exactly one lab netem qdisc")
    return {key: matches[0][key] for key in ["packets", "drops", "bytes", "qlen"]}


def observe(
    sender_pid: int, start: float, stop_file: Path, destination: Path, without_netem: bool = False
):
    root = psutil.Process(sender_pid)
    birth = root.create_time()
    previous, last = {}, time.monotonic()
    with destination.open("w", buffering=1) as stream:
        while not stop_file.exists():
            now = time.monotonic()
            row = {
                "monotonic_ms": (now - start) * 1000,
                "sender_cpu_core_percent": None,
                "sensor": "OS process accounting + kernel qdisc counters",
            }
            try:
                if psutil.Process(sender_pid).create_time() != birth:
                    raise RuntimeError("Sender process identity changed")
                current = {}
                for process in [root, *root.children(recursive=True)]:
                    try:
                        cpu = process.cpu_times()
                        current[(process.pid, process.create_time())] = cpu.user + cpu.system
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
                # Newly observed processes get no fabricated zero baseline.
                if previous and now > last:
                    row["sender_cpu_core_percent"] = (
                        100
                        * sum(
                            max(0, value - previous[key])
                            for key, value in current.items()
                            if key in previous
                        )
                        / (now - last)
                    )
                row["sender_process_count"] = len(current)
                row["netem"] = None if without_netem else netem_counters()
                previous, last = current, now
            except Exception as error:
                row["sensor_error"] = f"{type(error).__name__}: {error}"
            stream.write(json.dumps(row, allow_nan=False) + "\n")
            time.sleep(max(0, 0.2 - (time.monotonic() - now)))


def change_rate(rows: list[dict]) -> float | None:
    hashes = [r["source_pixel_sha256"] for r in rows if r.get("source_pixel_sha256")]
    if len(hashes) < 3:
        return None
    return sum(a != b for a, b in zip(hashes, hashes[1:], strict=False)) / (len(hashes) - 1)


def interval_summary(os_rows: list[dict], pixels: list[dict], start: float, end: float) -> dict:
    rows = [r for r in os_rows if start <= r["monotonic_ms"] < end and "sensor_error" not in r]
    cpu = [
        r["sender_cpu_core_percent"] for r in rows if r.get("sender_cpu_core_percent") is not None
    ]
    loss = None
    if len(rows) >= 3:
        first, last = rows[0]["netem"], rows[-1]["netem"]
        if first is not None and last is not None:
            sent, drops = last["packets"] - first["packets"], last["drops"] - first["drops"]
            if sent >= 0 and drops >= 0 and sent + drops > 0:
                loss = drops / (sent + drops)
    return {
        "valid_os_samples": len(rows),
        "cpu_core_percent_median": statistics.median(cpu) if len(cpu) >= 3 else None,
        "measured_drop_ratio": loss,
        "source_pixel_change_fraction": change_rate(
            [r for r in pixels if start <= r["monotonic_ms"] < end]
        ),
    }


def verify_live(
    condition: str,
    static_control: bool,
    os_rows: list[dict],
    pixels: list[dict],
    on_ms: float | None,
    off_ms: float | None,
    duration_ms: float,
    completed: bool,
) -> dict:
    base = {
        "verification_status": "ambiguous",
        "verified_condition": None,
        "causal_root_cause": "unestablished",
        "condition": condition,
        "static_control": static_control,
    }
    if not completed:
        return {**base, "verification_status": "failed", "reason": "Execution failed"}
    if on_ms is None or off_ms is None or not 0 < on_ms < off_ms < duration_ms:
        return {**base, "reason": "No complete intervention interval"}
    summaries = {
        "before": interval_summary(os_rows, pixels, 300, on_ms - 300),
        "during": interval_summary(os_rows, pixels, on_ms + 400, off_ms - 200),
        "after": interval_summary(os_rows, pixels, off_ms + 400, duration_ms),
    }
    before, during, after = [summaries[k] for k in ["before", "during", "after"]]
    base["measurements"] = summaries
    if any(
        row["valid_os_samples"] < 3 or row["cpu_core_percent_median"] is None
        for row in summaries.values()
    ):
        return {**base, "reason": "Insufficient OS observation coverage"}
    measured_loss = during["measured_drop_ratio"]
    before_cpu, during_cpu = before["cpu_core_percent_median"], during["cpu_core_percent_median"]
    moving = [row["source_pixel_change_fraction"] for row in [before, during, after]]
    if condition == "network_loss":
        verified = measured_loss is not None and measured_loss >= 0.1
        verified = verified and all(
            row["measured_drop_ratio"] is not None and row["measured_drop_ratio"] <= 0.02
            for row in [before, after]
        )
    elif condition == "compute_contention":
        verified = during_cpu >= 55 and during_cpu - before_cpu >= 25
        verified = verified and after["cpu_core_percent_median"] < during_cpu - 20
    elif condition == "source_freeze":
        verified = all(value is not None for value in moving)
        verified = verified and moving[0] >= 0.5 and moving[1] <= 0.1 and moving[2] >= 0.5
    elif condition == "normal":
        verified = all(row["measured_drop_ratio"] in [None, 0.0] for row in summaries.values())
        verified = verified and during_cpu - before_cpu < 25
        verified = verified and all(value is not None for value in moving)
        verified = verified and (
            all(value <= 0.1 for value in moving)
            if static_control
            else all(value >= 0.5 for value in moving)
        )
    else:
        raise ValueError("Unsupported live condition")
    return {
        **base,
        "verification_status": "verified" if verified else "ambiguous",
        "verified_condition": condition if verified else None,
        "reason": "Measured condition check, not causal attribution",
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sender-pid", type=int, required=True)
    parser.add_argument("--start", type=float, required=True)
    parser.add_argument("--stop-file", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--without-netem", action="store_true")
    args = parser.parse_args()
    observe(args.sender_pid, args.start, args.stop_file, args.output, args.without_netem)
