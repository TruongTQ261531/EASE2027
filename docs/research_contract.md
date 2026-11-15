# Research contract — provisional, 2026-11-15

This project targets an empirical software engineering contribution for EASE 2027 Main Research
Track. The attached handoff is a planning input, not evidence of novelty, venue rules, data access,
causal labels, or acceptance. The WebRTC candidate remains provisional. Conference ranking is a
user-stated target; the official 2027 CFP/deadline is now verified in venue_verification.md.
The homepage states CORE A; the ranking edition has not been independently checked.

**Current user-directed priority, 16 November Bangkok:** diagnostic identifiability and selective
prediction (A), followed by independent-oracle validity (B). The authoritative current RQs,
milestones and claim boundaries are in directions_a_b_plan.md. The table below describes the
original feasibility contract, not the current implementation status; see research_progress.json.

Intended users are RTC developers and reliability/QA engineers diagnosing degraded calls. The
engineering task is to distinguish plausible fault conditions and present traceable evidence.
Models must support that task; model accuracy alone is not the contribution.

## Boundaries

- CPU-first, compatible in ambition with a 6 GB GPU budget; no GPU or paid API in this pilot.
- No participant recruitment, surveys, MOS/ACR collection, or large manual annotation campaign.
- No tourism, eKYC, or dashboard data-fidelity topic. No dashboard before trustworthy data.
- Synthetic media only initially. Add audio/raw media only after a measurable utility argument.
- Keep requested intervention, measured condition, observed degradation and causal attribution
  distinct. The pilot always records causal attribution as `unestablished`.
- Never report requested fault settings as verified labels. Failed and ambiguous runs remain in
  the audit denominator; their exclusion from supervised scoring must be reported.
- Features exclude scenario/seed/host/file identifiers, intervention times, source-observer
  fingerprints, oracle fields and labels. Only explicitly allowed observation features reach ML.
- Fit preprocessing on training sessions. Tune on validation sessions. Preserve frozen test
  partitions and group by environment/configuration in the eventual main study.
- Report negative/neutral outcomes. No first-ever, SOTA, causal-diagnosis, real-world-generalization
  or conference-readiness claims without appropriate sources and experiments.

## RQs and evidence required

| RQ | Evidence required before an answer | Current implementation |
|---|---|---|
| RQ0 label validity | Independently measured interventions, controls, ambiguous/failed rates | Limited application-condition observers and checksum audit |
| RQ1 diagnosis | Strong rules/tabular/prior-work baselines on held-out sessions | Rules, dummy, logistic regression, random forest; condition classification only |
| RQ2 modality utility | Fair ablations, paired session estimates, costs and missingness | Telemetry / telemetry+logs / telemetry+logs+visual-change plumbing |
| RQ3 generalization | Held-out browser/machine/configuration, unseen intensity and overlapping faults | Not implemented; current runs use one environment |
| RQ4 engineering utility | Detection delay, false alarms/hour, localization and collection cost | Raw timestamps and collector-only CPU/RSS recorded; no usefulness claim |

Video change probes and receiver telemetry originate from the same stream. They do not establish
independent modalities or a novel fusion method. The injected capture pause and explicit receiver
closure are deliberately easy feasibility cases; neither approximates verified network loss or CPU
overload. `normal` denotes a sham protocol, not proof of a fault-free environment.

## Exit gates

Continue only the feasibility work until the official CFP and a closest-work matrix are audited.
W4 requires controls and at least three **fault families** with independent verification, not three
class names including the control. W8 requires defensible labels and a meaningful baseline;
otherwise pivot to a verified backup. The repository contains no final-study preregistration.
Future protocol changes require a new experiment output directory, a decision memo, and an
updated claim-to-evidence record.
