# Candidate decision — no final topic selection

| Candidate | SE task | Evidence now | Critical unresolved gate | Decision |
|---|---|---|---|---|
| WebRTC | Help RTC engineers distinguish degraded-call conditions | Real two-context call, collector and limited application observers work | Closest prior art; >=3 verified fault families; harder symptom-equivalent cases; cross-environment validity | Continue a bounded feasibility pilot |
| Microservices RCA | Localize a service from telemetry | RCAEval official code/license accessible and dataset locations identified | Dataset license, case labels and baseline replay; crowded prior art | Keep as backup; not selected |
| Issue/failure localization | Locate relevant code from issue/CI evidence | SWE-bench official repository accessible | Issue-fix labels are not automatically fault-location ground truth; dataset access; temporal leakage; harness budget | Keep as independent backup; not selected |

The literature matrix is a **citation discovery queue**, not an audited closest-work table. At least
five adjacent 2024–2026 references were observed in author repositories; publisher metadata and
full text remain unchecked. None establishes WebRTC novelty. Source copies and SHA256 access
records are under `artifacts/local/source-audit/`; `scripts/audit_sources.py` reproduces the checks.

Before committing to a paper: verify official CFP/deadline and open science rules; find the closest
direct WebRTC diagnosis/QoE studies; read their task/oracle/splits/results; retrieve licensed labeled
samples for both backups; run one baseline for each feasible alternative. A lack of access is not
evidence that a dataset or conference does not exist. Do not make quantitative candidate rankings
until those facts are available.

## Direct-prior-work update after public Internet became available

CFP verified: 22 January 2027 AoE. Direct WebRTC RCA/QoE/testing prior art now identified.
See novelty_audit.md for per-work evidence levels (two PDFs retrieved/read in selected sections,
others abstract/metadata only). Novelty gate remains open, with substantial overlap risk.
No final topic or strongest prior-work baseline is declared verified. The earlier discovery queue
above has been augmented, not retroactively treated as a completed full-text review.
