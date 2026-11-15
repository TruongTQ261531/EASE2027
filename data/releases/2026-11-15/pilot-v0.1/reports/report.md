# Pilot report — feasibility only

FEASIBILITY ONLY: synthetic application conditions, one host/browser; not RCA accuracy

Sessions: {'train': 18, 'validation': 6, 'test': 6}. Target: verified application condition.

| Model | Inputs | Macro-F1 | Balanced accuracy |
|---|---|---:|---:|
| rules | telemetry_logs | 1.000 | 1.000 |
| dummy | telemetry | 0.167 | 0.333 |
| logistic_regression | telemetry | 1.000 | 1.000 |
| random_forest | telemetry | 0.667 | 0.667 |
| dummy | telemetry_logs | 0.167 | 0.333 |
| logistic_regression | telemetry_logs | 1.000 | 1.000 |
| random_forest | telemetry_logs | 1.000 | 1.000 |
| dummy | telemetry_logs_video | 0.167 | 0.333 |
| logistic_regression | telemetry_logs_video | 1.000 | 1.000 |
| random_forest | telemetry_logs_video | 1.000 | 1.000 |

These scores validate plumbing only. No novelty, causal, external-validity,
multimodal benefit or conference-readiness claim follows from this pilot.
