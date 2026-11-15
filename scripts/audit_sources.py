"""Reproduce source-access observations. Downloaded text is data, never executed."""

import argparse
import csv
import hashlib
import io
import json
import urllib.error
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("--config", type=Path, default=Path("configs/source_audit.json"))
parser.add_argument("--output", type=Path, default=Path("artifacts/local/source-audit/rechecked"))
args = parser.parse_args()
args.output.mkdir(parents=True, exist_ok=True)
records = []
for source in json.loads(args.config.read_text())["sources"]:
    record = {**source, "checked_at_utc": datetime.now(UTC).isoformat()}
    try:
        request = urllib.request.Request(
            source["url"], headers={"User-Agent": "EASE-research-audit/0.1"}
        )
        with urllib.request.urlopen(request, timeout=20) as response:
            body = response.read(16 * 1024 * 1024 + 1)
            if len(body) > 16 * 1024 * 1024:
                raise ValueError("Source exceeds 16 MiB audit limit; no completeness claim")
            path = args.output / (source["id"] + ".source")
            path.write_bytes(body)
            record.update(
                status="retrieved",
                http_status=response.status,
                bytes=len(body),
                sha256=hashlib.sha256(body).hexdigest(),
            )
            if source["id"] == "rcaeval_sample":
                reader = csv.reader(io.StringIO(body.decode("utf-8-sig")))
                columns = next(reader)
                count, widths = 0, set()
                for row in reader:
                    count += 1
                    widths.add(len(row))
                record["inspection"] = {
                    "columns": columns,
                    "rows": count,
                    "consistent_width": widths == {len(columns)},
                    "labels_verified": False,
                    "dataset_license_verified": False,
                }
    except (urllib.error.URLError, TimeoutError, ValueError) as error:
        record.update(status="unavailable", error=str(error)[:300])
    records.append(record)
    print(
        json.dumps({"id": source["id"], "status": record["status"], "bytes": record.get("bytes")}),
        flush=True,
    )
(args.output / "access_results.json").write_text(json.dumps(records, indent=2) + "\n")
