"""Export synthetic experiment results without network identifiers or browser certificates.

The original files remain untouched. Derived manifests/split fingerprints are recalculated;
release_provenance.json preserves the original hashes and documents the transformation.
"""

import argparse
import hashlib
import json
import shutil
from pathlib import Path

from ease_rtc.io import read_json, read_jsonl, sha256, write_json, write_jsonl

PRIVATE_KEYS = {
    "address",
    "ip",
    "port",
    "url",
    "usernameFragment",
    "iceLocalUsernameFragment",
    "localCertificateId",
    "remoteCertificateId",
    "base64Certificate",
    "fingerprint",
    "fingerprintAlgorithm",
}


def sanitize(value):
    if isinstance(value, dict):
        return {k: sanitize(v) for k, v in value.items() if k not in PRIVATE_KEYS}
    if isinstance(value, list):
        return [
            sanitize(v) for v in value if not isinstance(v, dict) or v.get("type") != "certificate"
        ]
    return value


def export(source: Path, destination: Path):
    if destination.exists():
        raise ValueError("Release destination must not exist")
    original = {
        str(p.relative_to(source)): sha256(p) for p in sorted(source.rglob("*")) if p.is_file()
    }
    shutil.copytree(source, destination)
    # Only browser stats are transformed; source-observer pixel fingerprints are not ICE IDs.
    for path in destination.glob("**/raw/*/stats.jsonl"):
        write_jsonl(path, [sanitize(row) for row in read_jsonl(path)])
    for path in destination.glob("**/manifests/*.json"):
        dataset = path.parent.parent
        manifest = read_json(path)
        manifest["files"] = {relative: sha256(dataset / relative) for relative in manifest["files"]}
        write_json(path, manifest)
    for path in destination.glob("**/reports/splits.json"):
        dataset = path.parent.parent
        fingerprint = hashlib.sha256(
            json.dumps(
                {
                    "features_sha256": sha256(dataset / "features/windows.jsonl"),
                    "manifests": {
                        p.name: sha256(p) for p in sorted((dataset / "manifests").glob("*.json"))
                    },
                },
                sort_keys=True,
            ).encode()
        ).hexdigest()
        split = read_json(path)
        split["dataset_sha256"] = fingerprint
        write_json(path, split)
        metrics_file = dataset / "reports/metrics.json"
        if metrics_file.exists():
            metrics = read_json(metrics_file)
            metrics["dataset_sha256"] = fingerprint
            write_json(metrics_file, metrics)
    write_json(
        destination / "release_provenance.json",
        {
            "transformation": "Remove candidate address/ip/port/url/ICE usernames and certificate "
            "records from browser stats; recalculate manifests and split fingerprint",
            "original_files_sha256": original,
            "measurements_modified": False,
            "note": "Numeric stats, features, labels and predictions are retained. "
            "Source hashes and "
            "git_dirty flags describe original collection, not this later publication commit. "
            "Nested cross-version metrics reference original datasets until re-evaluated.",
            "license": "CC-BY-4.0 for project-generated synthetic observations; source code MIT",
        },
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--destination", type=Path, required=True)
    args = parser.parse_args()
    export(args.source, args.destination)
    print(args.destination)


if __name__ == "__main__":
    main()
