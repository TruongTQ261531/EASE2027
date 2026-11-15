# Live-call oracle và prospective feasibility v1 — kết quả

**19/19 requested calls completed and independently verified:** 15 on the GitHub runner and
4 on Codex cloud. Both datasets passed checksum/timeline/oracle replay and receiver-only feature
reconstruction, and are sealed. No model has been fitted or tuned on these cohorts in this report.

| Cohort | Requested | Completed | Verified | Failed / ambiguous |
|---|---:|---:|---:|---:|
| GitHub: seed100 train, 200 validation, 300 held-out | 15 | 15 | 15 | 0 / 0 |
| Cloud: seed300 held-out common conditions | 4 | 4 | 4 | 0 / 0 |

Protocol was committed before collection in `lab/frozen_plan_v1.json`; runtime checks required the
locked source/dependency/protocol hash. The common observed source digest is
`3f46ebd68a27e73b3405827048720ae8f05f18e6dd940409d51b600846284184`. This is prospective feasibility, not final-study
preregistration or a powered efficacy result. See [protocol](live_protocol_v1.md).

## Measured evidence and limits

- Kernel counter oracle verifies real loss on datagrams to namespace-local TURN relay UDP ports,
  with controls/recovery; CPU oracle uses sender process-tree accounting; source-freeze observer
  uses screenshot pixels without injected flags. These are three bounded measured conditions on
  real calls, not proof of causal attribution or physical camera/encoder fault diagnosis.
- Network-loss calls retained receiver median decoded FPS near20 during intervention, despite
  positive kernel drops. This does not establish absence of all degradation: FPS is one indicator;
  do not upgrade injection success into a perceptual/QoE or causal-degradation claim.
- Source-freeze calls had median decoded FPS0 during the paused interval and recovered. Static
  benign controls also had FPS0; a low-FPS alarm alone cannot identify a source fault.
- Compute-contention calls had receiver median FPS roughly0–4 during intervention and recovered
  near20 afterward. Paired controls, clock/QC and more replicates are still needed for main claims.
- Pixel observation shares the orchestration process; OS observer is separate. This is measurement-
  path independence with an explicit remaining shared failure domain. Causal labels remain unestablished.

## Environment coverage

Observed host platforms:

- `Linux-6.18.57-x86_64-with-glibc2.36`
- `Linux-7.0.0-1017-azure-x86_64-with-glibc2.36`

Both use Debian12 container userland and Chromium159. This supports a bounded cross-host/kernel
replication of collection and measurements, not isolated OS-userland/browser-engine generalization.
Cloud kernel does not support prio/netem; network transfer to cloud is untested. Firefox launches
but ICE gathering failed in TCP and a separate UDP pilot; failed runs are retained, never relabeled.

## Data and reproducibility

- CI data: `data/releases/live-frozen-v1/ci-43723089658`.
- Cloud data: `data/releases/live-frozen-v1/cloud`.
- Full per-run measured conditions and receiver phase metrics: [live_frozen_v1_results.json](live_frozen_v1_results.json).
- Earlier successful/failed debugging attempts: `data/releases/live-pilot/`.
- CI: https://github.com/TruongTQ261531/EASE2027/actions/runs/43723089658 (completed success).

```bash
uv run --frozen python lab/freeze_plan.py
uv run --frozen python -m ease_rtc.live_audit --dataset data/releases/live-frozen-v1/ci-43723089658
uv run --frozen python -m ease_rtc.live_audit --dataset data/releases/live-frozen-v1/cloud
uv run --frozen python scripts/summarize_live_study.py \
  --ci data/releases/live-frozen-v1/ci-43723089658 \
  --cloud data/releases/live-frozen-v1/cloud --output /tmp/live-study-report.json
```

The first fetched CI derivative lacked empty `sensor.log` files because the generic *.log ignore
pattern excluded them from Git. Every missing file had the recorded SHA256 of an empty file;
the exact empty files were restored and explicitly tracked, without changing measurements or
inventory hashes. Fresh-checkout audit is verified before publication of this milestone.

**Still open:** novelty/RQ gate, final main-study precision and protocol, a second netem-capable
host for network transfer, functional Firefox/other engine, distinct OS userland and harder fault
severities/overlaps. This milestone does not establish EASE submission readiness.
