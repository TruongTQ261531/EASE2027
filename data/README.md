# Data boundaries

Generated experiments belong under ignored `data/local/<experiment>/`:

```
protocol/schedule.json         intervention schedule; never model inputs
manifests/<run UUID>.json      provenance and file checksums; not model inputs
raw/<run UUID>/stats.jsonl     actual sender/receiver WebRTC stats
raw/<run UUID>/observations.jsonl  receiver states and visual observation
oracle/<run UUID>/source.jsonl source observer evidence; inaccessible to feature builder
oracle/<run UUID>.json         request, verification, degradation and separate condition label
features/windows.jsonl        closed-schema observations, identity used only for grouping
reports/audit.json             verified/ambiguous/failed counts and integrity result
reports/splits.json            frozen session partitions and dataset fingerprint
reports/metrics.json           baselines, predictions, confusion matrices and intervals
reports/report.md              generated feasibility summary
```

Source code uses MIT under the repository LICENSE. External data retain their own licensing;
no benchmark license is inferred from a code license. Synthetic observations contain local network
metadata and should be reviewed before publication. The initial artifact commits neither generated
traces nor raw media. A future release must provide an audited dataset manifest and archival DOI.

## Published derivative

The initial local-only boundary above is superseded for reviewed synthetic releases by
[data/releases](releases/README.md). Original local files remain untouched and ignored.
Use scripts/export_results.py for sanitized derivatives; keep transformation lineage and audit them.
