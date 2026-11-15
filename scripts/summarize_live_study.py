"""Summarize measured conditions and receiver symptoms without training on evaluation cohorts."""

import argparse
import statistics
from pathlib import Path

from ease_rtc.features import normalize
from ease_rtc.io import read_json, read_jsonl, sha256, write_json
from ease_rtc.live_audit import audit_live


def describe(root: Path, expected_version: str):
    snapshot = read_json(root / "protocol.json")
    if snapshot["protocol"]["version"] != expected_version:
        raise ValueError("Do not mix debugging pilots with prospective frozen-v1 data")
    quality = audit_live(root)
    runs = []
    for path in sorted((root / "manifests").glob("*.json")):
        m = read_json(path)
        verdict = read_json(root / "oracle" / m["run_id"] / "verdict.json")
        raw = root / "raw" / m["run_id"]
        rows = normalize(read_jsonl(raw / "stats.jsonl"), read_jsonl(raw / "observations.jsonl"))
        phases = {}
        if m["on_ms"] is not None and m["off_ms"] is not None:
            boundaries = [
                ("before", 300, m["on_ms"] - 300),
                ("during", m["on_ms"] + 400, m["off_ms"] - 200),
                ("after", m["off_ms"] + 400, snapshot["protocol"]["duration_s"] * 1000),
            ]
            for name, start, end in boundaries:
                selected = [f for t, f in rows if start <= t < end]
                phases[name] = {}
                for field in ["decoded_fps", "receive_kbps", "video_change_fraction"]:
                    values = [getattr(f, field) for f in selected if getattr(f, field) is not None]
                    phases[name][field] = statistics.median(values) if values else None
        role = (
            {100: "training", 200: "validation", 300: "held_out_same_host"}[m["seed"]]
            if expected_version.endswith("-ci")
            else "held_out_other_host_common_conditions"
        )
        runs.append(
            {
                "session_id": m["session_id"],
                "role": role,
                "condition": m["condition"],
                "static_control": m["static_control"],
                "seed": m["seed"],
                "engine": m["engine"],
                "browser_version": m["browser_version"],
                "host_label": m["host_label"],
                "platform": m["platform"],
                "verification_status": verdict["verification_status"],
                "measured_condition": verdict.get("measurements"),
                "receiver_symptoms": phases,
                "execution_status": m["execution_status"],
                "source_commit": m["git_commit"],
                "source_tree_sha256": m["source_tree_sha256"],
                "manifest_sha256": sha256(path),
            }
        )
    return quality, runs


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--ci", type=Path, required=True)
parser.add_argument("--cloud", type=Path, required=True)
parser.add_argument("--output", type=Path, required=True)
args = parser.parse_args()
ci_audit, ci = describe(args.ci, "prospective-feasibility-freeze-v1-ci")
cloud_audit, cloud = describe(args.cloud, "prospective-feasibility-freeze-v1-cloud")
assert not ({r["session_id"] for r in ci} & {r["session_id"] for r in cloud})
report = {
    "scope": "Prospective feasibility: measured fault conditions, not diagnosis efficacy",
    "protocol_lock_sha256": sha256(Path("lab/frozen_plan_v1.json")),
    "requested_runs": 19,
    "observed_runs": len(ci) + len(cloud),
    "ci_audit": ci_audit,
    "cloud_audit": cloud_audit,
    "runs": ci + cloud,
    "no_model_fitted_or_tuned": True,
    "causal_attribution": "unestablished",
    "limitations": [
        "One Chromium engine; Firefox pilot ICE failed",
        "Same Debian12 container userland on distinct host kernels",
        "Cloud has no netem; network cross-host transfer untested",
        "Tiny cohort, no efficacy or powered main-study claim",
    ],
}
write_json(args.output, report)
print({k: report[k] for k in ["scope", "requested_runs", "observed_runs"]})
