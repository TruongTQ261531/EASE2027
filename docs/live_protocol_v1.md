# Prospective live-call feasibility protocol v1

Frozen after debugging pilots, **before collecting seeds 100/200/300**. The machine-readable lock
is `lab/frozen_plan_v1.json` (source tree, protocols, runner, Dockerfile and dependency hashes).
`lab/run.sh` checks it before any `live_frozen_*` collection. Do not overwrite it: changes need v2.
This freezes a feasibility collection protocol, not the final paper RQ, a powered main-study
protocol, novelty, or a promise of acceptance. The handoff explicitly left those as verification gates.

## Work already planned vs evidence still needed

The original handoff says WebRTC is not finally selected and novelty has not been audited. It
already planned oracle, controls, group splits and go/no-go checks. Executing those checks is part
of following that plan. “Chốt RQ/pivot” means choosing a defensible differentiated contribution after
checking evidence, not discarding the plan or pretending its hypotheses are established results.
The user has prioritized continuing live-oracle integration and protocol work; no topic pivot is
being performed in this milestone.

## Fixed design

- Real calls, synthetic video, separate sender and receiver browser processes, authenticated local
  TURN, private `--internal` Docker network without public egress. Shape only namespace-local relay
  UDP using container NET_ADMIN; no host tc. Three conditions: network loss 30%, sender main-thread
  contention (850ms busy/1000ms cycle), source freeze. Controls: moving sham and benign static source.
- Duration 11s, baseline to 3s, requested intervention 3–7s, recovery to 11s, requested samples 250ms.
  Actual command completion, OS samples and screenshot spans are recorded using one monotonic clock.
- Network oracle: independently observed actual kernel drops vs packets; >=0.1 during, <=0.02 before
  and after. Compute oracle: sender process-tree CPU >=55% of one core and >=25 percentage-point
  increase, then >=20 point recovery. Source oracle: screenshot changes >=0.5 before/after and
  <=0.1 during. Minimum independent sample coverage required; see locked source for exact bounds.
- These thresholds are operational pilot criteria, not validated perceptual quality thresholds.
  Independent OS observer is a separate process and never receives type/intensity/schedule. Pixel
  observation uses screenshot API, not injected flags, but shares the orchestration process.
- Receiver-only feature whitelist. Oracle/request/host/seed fields never become model columns.
  Verification concerns the measured condition, not causal attribution; `causal_root_cause` stays
  `unestablished`. Quantify degradation separately from condition verification in later analyses.

## Prospective cohorts (19 calls requested)

| Role | Host / engine | Seed | Calls | Available conditions |
|---|---|---:|---:|---|
| Training | GitHub Ubuntu runner / Chromium | 100 | 5 | 3 faults + 2 controls |
| Validation | Same runner / Chromium | 200 | 5 | Same |
| Held-out same host | Same runner / Chromium | 300 | 5 | Same |
| Held-out other host | Codex cloud / Chromium | 300 | 4 | Compute, source freeze, 2 controls |

No model or threshold tuning on seed300 or target-host data. Both normal controls map to no
requested fault; they must not be treated as two independent fault families. Session IDs never
cross partitions. Same seed across held-out hosts supports content-matched comparison; training
content seeds are different. No replacement of failed or ambiguous runs with convenient successes.
Eligible labeled samples and total attempted samples must be reported separately.

Cross-host network generalization cannot be measured because cloud kernel lacks prio/netem.
Firefox launch succeeds but ICE candidate gathering fails (TCP and a separate UDP debug attempt);
Firefox is excluded **with the failed pilot evidence retained**, not counted as successful coverage.
Both containers use Debian12 userland; cloud and GitHub have different host kernels/runner machines.
This is cross-host/kernel evidence, not an isolated OS-userland or browser-engine effect.

## Freeze and analysis boundaries

After each collection: replay checksums, clocks, independent oracle verdicts and receiver-feature
reconstruction with `python -m ease_rtc.live_audit --dataset DATASET --seal`. The inventory lock
rejects later modification. Sanitized publication is a derived dataset with new hashes and explicit
original-hash lineage; do not overwrite original observations.

The sample size is deliberately small for feasibility. No powered efficacy, multiple-fault,
confidence-calibrated diagnosis, industry usefulness or generalization claim is supported. The
final main-study protocol needs novelty/RQ resolution, precision/resource planning, stronger
baselines, richer severities/hard negatives, and a functioning second browser engine/OS setup.
