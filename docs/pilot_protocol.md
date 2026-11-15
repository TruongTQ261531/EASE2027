# Pilot protocol v0.1

Purpose: validate artifact execution and observation/label separation. This is a feasibility protocol,
not a final-study preregistration or evidence of an empirical SE contribution.

`configs/experiments/pilot.yaml` specifies 10 calls per condition, 30 total; order is shuffled with
seed 2027. Source seeds 42–51 occur once in **each** condition. Every call gets two fresh browser
contexts and UUID identities. Browser/relay processes restart between calls. This is still one
machine/browser version; no independent environment replication is implied.

Each call has 0.5 seconds of settling followed by a 6-second recording at a requested 250 ms
cadence. A command is sent near t=2 seconds and recovery near t=4 seconds. Actual dispatch
times are stored in the oracle. Closing the receiving peer is irreversible within that call;
the t=4 action only resumes the source and does not reconnect. The normal command is a no-op
sham with the same schedule. Timings are never model columns or used to select feature windows.

Conditions:

1. `normal`: live synthetic source during a no-op sham intervention. Does not prove absence
   of other degradation. Receiver degradation is recorded independently.
2. `capture_pause`: suspend canvas updates; source-image fingerprints must change before,
   remain stable during, and change after the intervention. The receiver is probed separately.
3. `connection_close`: explicitly close the receiver peer; sampled receiver state must be closed.
   This is a direct application-state readback, not independently instrumented network failure.

Observer thresholds (e.g. >0.5 source-change fraction, <0.25 receiver-change fraction) are pilot
heuristics, not validated quality thresholds. Static content, sample aliasing, freeze lag and
observations shared with model features limit oracle independence and construct validity.

The main pipeline records complete observations, hashes files, audits timelines and exports
one-second feature windows. Every session is aggregated over **all** its windows. Only verified
application-condition labels are eligible for training. Ambiguous/failed counts remain in reports.
Source observations and injection timing cannot enter the model matrix.

Eligible sessions are stratified by condition into 60% training / 20% validation / 20% test, stored
in `reports/splits.json` with a dataset fingerprint. UUID grouping prevents within-session window
leakage. Source seeds are balanced by condition but not held out; seed/environment generalization
is not measured. Re-evaluation reuses the saved partition and refuses changed datasets/seeds.

Models and feature ablations are specified before the pilot: dummy, logistic regression and
random forest on telemetry; telemetry+logs; telemetry+logs+visual change. Rules use telemetry+logs
and tune thresholds on validation only. Imputation and scaling fit training observations only.
The report includes macro-F1, balanced accuracy, class confusion matrices, Brier sum, 5-bin ECE,
fixed-threshold risk/coverage, per-session predictions and a 500-draw session-cluster bootstrap.
No winner is chosen from the test results; no paired superiority, p-value, modality utility or
generalization claim is made. Six test sessions are too few for those claims.

Next study must add independent measurement, stronger controls, symptom-equivalent causes,
network/CPU interventions in a safe lab, strong prior-work baselines, calibration assessment,
missing-modality experiments, multiple comparison handling, power/precision planning and external
validation. Collector-process CPU/RSS excludes browser and coturn; it is not total-system overhead.
