"""Create a compact, traceable record without committing raw observations."""

import argparse
from pathlib import Path

from ease_rtc.io import read_json, read_jsonl, sha256, write_json

parser = argparse.ArgumentParser()
parser.add_argument("--dataset", type=Path, required=True)
parser.add_argument("--output", type=Path, required=True)
args = parser.parse_args()
metrics_file = args.dataset / "reports" / "metrics.json"
metrics = read_json(metrics_file)
manifests = [read_json(p) for p in sorted((args.dataset / "manifests").glob("*.json"))]
summary = {
    "scope": metrics["scope"],
    "dataset_directory": str(args.dataset),
    "raw_data_archived": False,
    "raw_data_location": "Current workspace only; recreate with scripts/reproduce_pilot.sh",
    "metrics_sha256": sha256(metrics_file),
    "dataset_sha256": metrics["dataset_sha256"],
    "source_tree_sha256": sorted({m["source_tree_sha256"] for m in manifests}),
    "browser_versions": sorted({m["browser_version"] for m in manifests}),
    "git_heads": sorted({m["git_commit"] for m in manifests}),
    "git_dirty_during_collection": any(m["git_dirty"] for m in manifests),
    "dependency_lock_sha256": sorted({m["dependency_lock_sha256"] for m in manifests}),
    "audit": metrics["audit"],
    "feature_windows": len(read_jsonl(args.dataset / "features" / "windows.jsonl")),
    "split_counts": metrics["split_counts"],
    "collection_wall_seconds_sum": sum(m["collection_duration_s"] for m in manifests),
    "results": [
        {
            k: result[k]
            for k in [
                "model",
                "feature_set",
                "macro_f1",
                "balanced_accuracy",
                "macro_f1_session_bootstrap_95_interval",
                "confusion_matrix",
            ]
        }
        for result in metrics["results"]
    ],
    "limitation": (
        "Easy synthetic application conditions; one host/browser; only six test sessions. "
        "No inference about novelty, causal root cause, modality value or external validity."
    ),
}
write_json(args.output, summary)
print(args.output)
