"""Normalize W3C counters and construct features from observations only."""

import math
from pathlib import Path

from ease_rtc.io import read_json, read_jsonl, write_jsonl
from ease_rtc.schema import Features, FeatureWindow, RunManifest

TELEMETRY = [
    "receive_kbps",
    "decoded_fps",
    "jitter_ms",
    "rtt_ms",
    "packet_loss_ratio",
    "dropped_frame_ratio",
]
LOGS = ["connected_fraction", "closed_fraction"]
VIDEO = ["video_change_fraction"]
FEATURE_SETS = {
    "telemetry": TELEMETRY,
    "telemetry_logs": TELEMETRY + LOGS,
    "telemetry_logs_video": TELEMETRY + LOGS + VIDEO,
}


def numeric(value):
    return float(value) if isinstance(value, (int, float)) and math.isfinite(value) else None


def inbound(stats: list[dict]) -> dict:
    # This pilot negotiates exactly one video RTP stream; no arbitrary choice for multi-stream.
    matches = [
        s
        for s in stats
        if s.get("type") == "inbound-rtp" and s.get("kind", s.get("mediaType")) == "video"
    ]
    if len(matches) > 1:
        raise ValueError("Multiple inbound video streams need an explicit aggregation policy")
    return matches[0] if matches else {}


def delta(current: dict, previous: dict, key: str) -> float | None:
    a, b = numeric(current.get(key)), numeric(previous.get(key))
    if current.get("id") != previous.get("id") or a is None or b is None or a < b:
        return None  # First observation, counter reset, absent field or changed stream.
    return a - b


def normalize(samples: list[dict], observations: list[dict]) -> list[tuple[float, Features]]:
    if len(samples) != len(observations):
        raise ValueError("Stats/observation alignment mismatch")
    rows, previous, prev_time, prev_fingerprint = [], {}, None, None
    for sample, observation in zip(samples, observations, strict=True):
        t = sample["monotonic_ms"]
        if t != observation["monotonic_ms"] or t < 0 or (prev_time is not None and t <= prev_time):
            raise ValueError("Non-monotonic or misaligned observation timeline")
        current = inbound(sample["receiver_stats"])
        dt = (t - prev_time) / 1000 if prev_time is not None else None
        changes = {
            k: delta(current, previous, k)
            for k in [
                "bytesReceived",
                "framesDecoded",
                "packetsReceived",
                "packetsLost",
                "framesDropped",
            ]
        }
        values = {}
        for field, counter, scale in [
            ("receive_kbps", "bytesReceived", 8 / 1000),
            ("decoded_fps", "framesDecoded", 1),
        ]:
            if dt and changes[counter] is not None:
                values[field] = changes[counter] * scale / dt
        jitter = numeric(current.get("jitter"))
        if jitter is not None and jitter >= 0:
            values["jitter_ms"] = jitter * 1000
        transport = next(
            (
                s
                for s in sample["receiver_stats"]
                if s.get("type") == "transport" and s.get("id") == current.get("transportId")
            ),
            {},
        )
        pair = next(
            (
                s
                for s in sample["receiver_stats"]
                if s.get("id") == transport.get("selectedCandidatePairId")
            ),
            {},
        )
        rtt = numeric(pair.get("currentRoundTripTime"))
        if rtt is not None and rtt >= 0:
            values["rtt_ms"] = rtt * 1000
        for name, numerator, other in [
            ("packet_loss_ratio", "packetsLost", "packetsReceived"),
            ("dropped_frame_ratio", "framesDropped", "framesDecoded"),
        ]:
            a, b = changes[numerator], changes[other]
            if a is not None and b is not None and a + b > 0:
                values[name] = a / (a + b)
        values["connected_fraction"] = float(observation["connection_state"] == "connected")
        values["closed_fraction"] = float(observation["connection_state"] == "closed")
        fingerprint = observation["receiver_fingerprint"]
        if fingerprint is not None and prev_fingerprint is not None:
            values["video_change_fraction"] = float(fingerprint != prev_fingerprint)
        rows.append((t, Features(**values)))
        previous, prev_time, prev_fingerprint = current, t, fingerprint
    return rows


def mean_features(records: list[Features]) -> Features:
    result = {}
    for field in Features.model_fields:
        values = [getattr(row, field) for row in records if getattr(row, field) is not None]
        result[field] = sum(values) / len(values) if values else None
    return Features(**result)


def build_features(dataset: Path, window_ms: int = 1000) -> list[FeatureWindow]:
    if window_ms <= 0:
        raise ValueError("window_ms must be positive")
    windows = []
    # Manifest supplies identity and execution state only; never scenario or event timing.
    for path in sorted((dataset / "manifests").glob("*.json")):
        manifest = RunManifest.model_validate(read_json(path))
        if manifest.execution_status != "completed":
            continue
        raw = dataset / "raw" / manifest.run_id
        rows = normalize(read_jsonl(raw / "stats.jsonl"), read_jsonl(raw / "observations.jsonl"))
        buckets = {}
        for t, features in rows:
            buckets.setdefault(int(t // window_ms), []).append(features)
        for index, records in sorted(buckets.items()):
            windows.append(
                FeatureWindow(
                    run_id=manifest.run_id,
                    session_id=manifest.session_id,
                    window_start_ms=index * window_ms,
                    window_end_ms=(index + 1) * window_ms,
                    features=mean_features(records),
                )
            )
    if not windows:
        raise ValueError("No completed, nonempty runs to featurize")
    write_jsonl(dataset / "features" / "windows.jsonl", [w.model_dump() for w in windows])
    return windows


def model_matrix(records: list[Features], columns: list[str]):
    import numpy as np

    if (
        not columns
        or len(set(columns)) != len(columns)
        or set(columns) - set(Features.model_fields)
    ):
        raise ValueError("Model columns must be unique approved observation features")
    return np.array(
        [
            [getattr(row, c) if getattr(row, c) is not None else np.nan for c in columns]
            for row in records
        ],
        dtype=float,
    )
