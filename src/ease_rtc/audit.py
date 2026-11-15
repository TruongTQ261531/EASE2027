from pathlib import Path

from ease_rtc.features import normalize
from ease_rtc.io import read_json, read_jsonl, safe_path, sha256, write_json
from ease_rtc.schema import OracleEvent, RunManifest
from ease_rtc.verification import verify


def audit(dataset: Path) -> dict:
    paths = sorted((dataset / "manifests").glob("*.json"))
    if not paths:
        raise ValueError("No run manifests found; an empty dataset cannot pass audit")
    result = {
        "runs": len(paths),
        "completed": 0,
        "failed": 0,
        "verified": 0,
        "ambiguous": 0,
        "failed_verification": 0,
        "sample_count": 0,
        "conditions": {},
        "max_collection_span_ms": 0.0,
    }
    sessions, runs, environments = set(), set(), set()
    for path in paths:
        manifest = RunManifest.model_validate(read_json(path))
        if manifest.session_id in sessions or manifest.run_id in runs:
            raise ValueError("Duplicate session or run identifier")
        sessions.add(manifest.session_id)
        runs.add(manifest.run_id)
        environments.add(manifest.environment_id)
        required = {
            f"raw/{manifest.run_id}/stats.jsonl",
            f"raw/{manifest.run_id}/observations.jsonl",
            f"oracle/{manifest.run_id}/source.jsonl",
            f"oracle/{manifest.run_id}.json",
        }
        if set(manifest.files) != required:
            raise ValueError("Manifest must checksum every raw and oracle evidence file")
        for relative, expected in manifest.files.items():
            if sha256(safe_path(dataset, relative)) != expected:
                raise ValueError(f"Checksum mismatch: {relative}")
        oracle = OracleEvent.model_validate(
            read_json(dataset / "oracle" / f"{manifest.run_id}.json")
        )
        if oracle.session_id != manifest.session_id or oracle.run_id != manifest.run_id:
            raise ValueError("Oracle/manifest identifier mismatch")
        raw = dataset / "raw" / manifest.run_id
        samples = read_jsonl(raw / "stats.jsonl")
        observations = read_jsonl(raw / "observations.jsonl")
        source = read_jsonl(dataset / "oracle" / manifest.run_id / "source.jsonl")
        if [r["monotonic_ms"] for r in source] != [r["monotonic_ms"] for r in samples]:
            raise ValueError("Source observer timeline does not align with the collector")
        replayed = verify(
            manifest.run_id,
            manifest.session_id,
            manifest.config,
            observations,
            source,
            oracle.actual_start_ms,
            oracle.actual_end_ms,
            manifest.execution_status == "completed",
        )
        if replayed.model_dump() != oracle.model_dump():
            raise ValueError("Oracle verdict does not match replayed observation evidence")
        if len(samples) != manifest.sample_count:
            raise ValueError("Manifest sample count mismatch")
        if manifest.execution_status == "completed":
            normalize(samples, observations)
            if not any(s["receiver_stats"] for s in samples):
                raise ValueError("Completed run contains no receiver stats")
        result[manifest.execution_status] += 1
        key = (
            "failed_verification"
            if oracle.verification_status == "failed"
            else oracle.verification_status
        )
        result[key] += 1
        result["sample_count"] += len(samples)
        result["conditions"][oracle.requested_condition] = (
            result["conditions"].get(oracle.requested_condition, 0) + 1
        )
        if samples:
            result["max_collection_span_ms"] = max(
                result["max_collection_span_ms"], max(s["collection_span_ms"] for s in samples)
            )
    result["environments"] = len(environments)
    result["verified_rate"] = result["verified"] / len(paths)
    result["scope"] = "Application-condition feasibility; causal attribution unestablished"
    write_json(dataset / "reports" / "audit.json", result)
    return result
