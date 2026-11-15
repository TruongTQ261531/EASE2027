"""Audit request/measurement label provenance, retaining every published live-call attempt."""

import argparse
from collections import Counter
from pathlib import Path

from diagnostic_analysis import LOCK, ROOT, check_analysis_lock, verified_dataset

from ease_rtc.io import read_json, sha256, write_json


def label_policy_row(manifest, verdict):
    verified = verdict["verification_status"] == "verified"
    label = verdict["verified_condition"] if verified else None
    return {
        "session_id": manifest["session_id"],
        "request_condition": manifest["condition"],
        "static_control": manifest["static_control"],
        "execution_status": manifest["execution_status"],
        "verification_status": verdict["verification_status"],
        "reference_condition": label,
        "eligible_for_supervised_scoring": verified,
        "unsupported_if_request_always_used_as_label": not verified,
        "request_disagrees_with_verified_condition": label != manifest["condition"]
        if verified
        else None,
        "causal_attribution": "unestablished",
    }


def run(config):
    cohorts, session_ids = [], set()
    for spec in config["datasets"]:
        root, quality = verified_dataset(spec)
        rows = []
        for path in sorted((root / "manifests").glob("*.json")):
            manifest = read_json(path)
            if manifest["session_id"] in session_ids:
                raise ValueError("Duplicated attempts across release cohorts")
            session_ids.add(manifest["session_id"])
            verdict = read_json(root / "oracle" / manifest["run_id"] / "verdict.json")
            rows.append(label_policy_row(manifest, verdict))
        cohorts.append(
            {
                "dataset": spec["path"],
                "scope": spec["scope"],
                "audit": quality,
                "attempts": len(rows),
                "eligible": sum(r["eligible_for_supervised_scoring"] for r in rows),
                "unsupported_request_labels": sum(
                    r["unsupported_if_request_always_used_as_label"] for r in rows
                ),
                "verified_condition_disagreements": sum(
                    r["request_disagrees_with_verified_condition"] is True for r in rows
                ),
                "rows": rows,
            }
        )
    rows = [r for c in cohorts for r in c["rows"]]
    return {
        "scope": (
            "Label provenance audit only; not a measured false-positive/negative "
            "or calibration-bias experiment"
        ),
        "attempts": len(rows),
        "verification_counts": dict(
            sorted(Counter(r["verification_status"] for r in rows).items())
        ),
        "unsupported_request_labels": sum(
            r["unsupported_if_request_always_used_as_label"] for r in rows
        ),
        "verified_condition_disagreements": sum(
            r["request_disagrees_with_verified_condition"] is True for r in rows
        ),
        "oracle_accuracy_estimate": None,
        "label_policy_metric_bias_estimate": None,
        "why_agreement_is_not_accuracy": (
            "verify_live selects the check using the requested condition and copies that "
            "condition on pass; it cannot discover an alternative class"
        ),
        "missing_label_policy": "Unknown/failed never become normal or a confirmed false positive",
        "reference_limit": (
            "Independent measurement paths, request-conditioned verification, shared "
            "orchestrator for source pixels; causal truth unestablished"
        ),
        "pooling_limit": (
            "77 debugging/frozen attempts are an accounting total, not an i.i.d. sample "
            "or an injection-failure rate estimate"
        ),
        "needed_for_B1": [
            "Blind measurement checks for all supported conditions, join request only afterward",
            "No-op/delayed/partial interventions, missing sensors, real calls, matched controls",
            "Assess reference reliability/ambiguity before reporting policy bias",
            "Fixed-prediction paired scoring and paired retraining reported separately",
        ],
        "cohorts": cohorts,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    check_analysis_lock()
    if args.output.exists():
        raise ValueError("Never overwrite a completed result")
    report = run(read_json(ROOT / "configs/analysis/directions_v1.json"))
    report["analysis_lock_sha256"] = sha256(LOCK)
    write_json(args.output, report)
    print({k: report[k] for k in ["attempts", "verification_counts", "unsupported_request_labels"]})
