"""Replay live-call oracle evidence and seal a dataset without silently excluding failures."""

import argparse
from collections import Counter
from pathlib import Path

from ease_rtc.features import mean_features, normalize
from ease_rtc.io import read_json, read_jsonl, safe_path, sha256, write_json
from ease_rtc.lab_sensors import verify_live
from ease_rtc.live_lab import LiveProtocol
from ease_rtc.schema import FeatureWindow


def inventory(root: Path) -> dict:
    return {
        str(p.relative_to(root)): sha256(p)
        for p in sorted(root.rglob("*"))
        if p.is_file() and p != root / "dataset_lock.json"
    }


def check_lock(root: Path):
    lock = root / "dataset_lock.json"
    if lock.exists() and read_json(lock)["files_sha256"] != inventory(root):
        raise ValueError("Sealed dataset changed: use a new dataset/version")


def seal(root: Path):
    if (root / "dataset_lock.json").exists():
        check_lock(root)
        return
    write_json(
        root / "dataset_lock.json",
        {"purpose": "Immutable feasibility dataset, not a DOI", "files_sha256": inventory(root)},
    )


def audit_live(root: Path) -> dict:
    check_lock(root)
    protocol = LiveProtocol.model_validate(read_json(root / "protocol.json")["protocol"])
    paths = sorted((root / "manifests").glob("*.json"))
    if not paths:
        raise ValueError("No live run manifests: no positive readiness claim")
    counts, conditions, ids, groups = Counter(), Counter(), set(), []
    for path in paths:
        m = read_json(path)
        run_id = m["run_id"]
        if m["schema_version"] != "2.0" or m["session_id"] != run_id or run_id in ids:
            raise ValueError("Invalid/duplicate live session identity")
        ids.add(run_id)
        raw, oracle = root / "raw" / run_id, root / "oracle" / run_id
        required = {
            f"raw/{run_id}/stats.jsonl",
            f"raw/{run_id}/observations.jsonl",
            f"oracle/{run_id}/os.jsonl",
            f"oracle/{run_id}/pixels.jsonl",
            f"oracle/{run_id}/request.json",
            f"oracle/{run_id}/verdict.json",
            f"features/{run_id}.jsonl",
        }
        # Failed startup may have no OS observation file, and must remain failed.
        if m["execution_status"] == "completed" and set(m["files"]) != required:
            raise ValueError("Completed run must checksum all evidence and features")
        for relative, expected in m["files"].items():
            if sha256(safe_path(root, relative)) != expected:
                raise ValueError("Evidence checksum mismatch")
        samples, observed = read_jsonl(raw / "stats.jsonl"), read_jsonl(raw / "observations.jsonl")
        if len(samples) != m["sample_count"]:
            raise ValueError("Sample count mismatch")
        normalized = normalize(samples, observed)
        os_rows = read_jsonl(oracle / "os.jsonl") if (oracle / "os.jsonl").exists() else []
        if any(
            b["monotonic_ms"] <= a["monotonic_ms"]
            for a, b in zip(os_rows, os_rows[1:], strict=False)
        ):
            raise ValueError("Non-monotonic OS observer clock")
        replay = verify_live(
            m["condition"],
            m["static_control"],
            os_rows,
            read_jsonl(oracle / "pixels.jsonl"),
            m["on_ms"],
            m["off_ms"],
            protocol.duration_s * 1000,
            m["execution_status"] == "completed",
        )
        if replay != read_json(oracle / "verdict.json"):
            raise ValueError("Oracle does not replay from independent observation evidence")
        if replay["verification_status"] != m["verification_status"]:
            raise ValueError("Oracle/manifest status mismatch")
        request = read_json(oracle / "request.json")
        if (request["condition"], request["static_control"], request["seed"]) != (
            m["condition"],
            m["static_control"],
            m["seed"],
        ):
            raise ValueError("Request/manifest mismatch")
        buckets = {}
        for t, row in normalized:
            buckets.setdefault(int(t // 1000), []).append(row)
        expected = [
            FeatureWindow(
                run_id=run_id,
                session_id=run_id,
                window_start_ms=i * 1000,
                window_end_ms=(i + 1) * 1000,
                features=mean_features(rows),
            ).model_dump()
            for i, rows in sorted(buckets.items())
        ]
        windows = [
            FeatureWindow.model_validate(w).model_dump()
            for w in read_jsonl(root / "features" / f"{run_id}.jsonl")
        ]
        if expected != windows:
            raise ValueError("Features are not reproducible solely from receiver observations")
        counts["execution_" + m["execution_status"]] += 1
        counts["oracle_" + m["verification_status"]] += 1
        conditions[
            (m["engine"], m["condition"], m["static_control"], m["verification_status"])
        ] += 1
        groups.append(
            {
                "session_id": run_id,
                "host": m["host_label"],
                "engine": m["engine"],
                "seed": m["seed"],
                "status": m["verification_status"],
                "condition": m["condition"],
                "static_control": m["static_control"],
            }
        )
    # A failure is counted separately by execution and verification; do not sum both as runs.
    return {
        "runs": len(paths),
        "completed": counts["execution_completed"],
        "execution_failed": counts["execution_failed"],
        "verified": counts["oracle_verified"],
        "verification_failed": counts["oracle_failed"],
        "ambiguous": counts["oracle_ambiguous"],
        "verification_denominator": len(paths),
        "conditions": [
            {
                "engine": k[0],
                "condition": k[1],
                "static_control": k[2],
                "verification_status": k[3],
                "runs": v,
            }
            for k, v in sorted(conditions.items())
        ],
        "sessions": groups,
        "causal_attribution": "unestablished",
        "scope": "Measured fault conditions on live calls, bounded process/container lab",
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--seal", action="store_true")
    args = parser.parse_args()
    result = audit_live(args.dataset)
    if args.seal:
        if not (args.dataset / "dataset_lock.json").exists():
            write_json(args.dataset / "reports" / "oracle_audit.json", result)
        seal(args.dataset)
    print({k: result[k] for k in ["runs", "completed", "verified", "ambiguous", "scope"]})
