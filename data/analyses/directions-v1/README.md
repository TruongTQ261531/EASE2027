# Retrospective A1/B0 analysis v1

Derived from the published synthetic live-call releases; no third-party media or PDFs.
Observation-derived data and reports: CC BY 4.0, matching the source release. Code: repository MIT.
This is retrospective feasibility, not a fresh confirmatory main-study dataset or causal truth.

- `diagnostic_results.json`: all nine model/view combinations, thresholds, predictions, audits.
- `summary.csv`: compact evaluation counts; blank risk/threshold means null, never zero risk.
- `runtime.json`: one measured analysis process; excludes browser collection and imports' wall time.
- `oracle_validity_results.json`: all 77 attempts, including 45 failures; no oracle-accuracy estimate.
- `FILES.sha256.json`: hashes of these derived artifacts; source/config hashes are in the reports.

See `docs/directions_v1_results.md` and `docs/oracle_validity_v1_results.md` for interpretation,
limitations and reproduction. Training/calibration are seed100/200; seed300 never selects models
or thresholds. Evaluation observations had already been inspected before this study direction.
The v1 collector lock remains intact. The analysis lock was committed at 7fe02c2 before execution.
