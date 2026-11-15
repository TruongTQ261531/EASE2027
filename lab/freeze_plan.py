"""Write/check the prospective feasibility lock before collecting any frozen-v1 sessions."""

import argparse
from datetime import UTC, datetime
from pathlib import Path

from ease_rtc.io import read_json, sha256, source_provenance, write_json
from ease_rtc.live_lab import LiveProtocol

ROOT = Path(__file__).resolve().parents[1]
LOCK = ROOT / "lab/frozen_plan_v1.json"
FILES = [
    "configs/experiments/live_frozen_ci_v1.json",
    "configs/experiments/live_frozen_cloud_v1.json",
    "lab/Dockerfile",
    "lab/build.sh",
    "lab/run.sh",
    "lab/freeze_plan.py",
    "uv.lock",
]


def current():
    for filename in FILES[:2]:
        LiveProtocol.model_validate(read_json(ROOT / filename))
    return {
        "source_tree_sha256": source_provenance(ROOT)["source_tree_sha256"],
        "files_sha256": {name: sha256(ROOT / name) for name in FILES},
    }


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--write", action="store_true")
args = parser.parse_args()
snapshot = current()
if args.write:
    if LOCK.exists():
        raise ValueError("Do not overwrite a frozen plan; create a new version")
    write_json(
        LOCK,
        {
            **snapshot,
            "frozen_at_utc": datetime.now(UTC).isoformat(),
            "scope": "Prospective feasibility collection, NOT final-study preregistration",
            "roles": {
                "ci_chromium_seed_100": "training",
                "ci_chromium_seed_200": "validation",
                "ci_chromium_seed_300": "held_out_same_host",
                "cloud_chromium_seed_300": "held_out_other_host_common_conditions",
            },
            "rules": [
                "No training/tuning on seed300 or target host",
                "Retain failed and ambiguous sessions in audit denominator",
                "Only independently verified conditions eligible for classification",
                "No network transfer claim for cloud without netem",
                "Firefox is a failed feasibility case, not an achieved holdout",
                "Changes require a new protocol and dataset version",
            ],
        },
    )
else:
    saved = read_json(LOCK)
    if any(saved[key] != snapshot[key] for key in snapshot):
        raise ValueError("Frozen protocol/source/dependencies changed; use a new version")
print("Prospective feasibility plan", "written" if args.write else "verified")
