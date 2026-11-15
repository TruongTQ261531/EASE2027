# Next project work — updated 2026-11-15

## Current decision

CFP verified; full paper 22 January 2027 AoE. Topic lock remains **NO-GO** until the novelty and
live-call oracle gates have defensible evidence. Technical probes and cross-version pilot are
completed feasibility results, not a finished main-track study.

## Ordered priorities

1. **Close the direct-prior-work audit (internal target 22 November).** Read full methods,
   labels, splits and artifacts for transport-aware QoE, WebRTC-QoE, Wi-Fi QoE and Machination;
   compare directly to Domino. Update a claim/oracle/evaluation overlap matrix. Deliver one
   bounded SE research question with evidence of differentiation, or an explicit pivot decision.
2. **Integrate independent measurement into live WebRTC calls (target 29 November).** Prepare
   an isolated Linux lab with scoped network administration and independent packet/process/media
   sensors. Collect >=3 fault families plus sham/normal controls; preserve failed and ambiguous
   interventions. Probe results alone cannot label browser faults. Current cloud cannot create
   the required network namespaces or apply scoped netem.
3. **Freeze a defensible study protocol and dataset (target 6 December).** Include symptom-equivalent
   cases, benign adaptation/static content, severity holdouts, training-only preprocessing,
   session/environment/configuration splits, strong baselines and a precision/resource plan.
4. **Expand external validation.** Use a second machine/OS and browser engine. Chromium 156/159
   results on one host are already available; retain Firefox launch failure. No retuning on
   evaluation cohorts already inspected.
5. **Main runs, failure analysis, manuscript and anonymized artifact.** Follow the shortened
   roadmap only if the gates pass; otherwise pivot or publish an honest technical report.

## Where completed work is stored

| Material | Repository path |
|---|---|
| Entry point and reproduction | README.md |
| Stage status | docs/research_progress.json |
| CFP/deadline and evidence | docs/venue_verification.md / .json |
| Novelty findings and sources | docs/novelty_audit.md, literature_matrix.csv, research_source_manifest.json |
| Independent probe report | docs/oracle_independence.md, oracle_probe_results.json |
| Cross-version report | docs/cross_environment.md, transfer_results.json |
| Code, configs, schemas, tests, CI | src/, configs/, schemas/, tests/, .github/ |
| Sanitized synthetic observations and full per-session results | data/releases/2026-11-15/ |
| Immutable originals on the current machine | data/local/ (ignored, never pushed directly) |
| Third-party source copies for local reading | artifacts/local/ (ignored); URLs/hashes documented |

Completed milestones are committed and pushed under the standing user instruction in AGENTS.md.
Publication on GitHub does not mean an unverified research gate is completed, or that GitHub alone
is a long-term archived research artifact. A later anonymized submission package needs its own
identity review; this named development repository is not an anonymous supplement.

## Live-lab milestone update

Independent measurement is now integrated with real calls for three bounded families in the
GitHub pilot, with controls and failed Firefox attempts retained. The code and prospective
feasibility protocol are pushed to main. See live_protocol_v1.md, lab/frozen_plan_v1.json and
live_cloud_capabilities.json. The cloud prospective cohort has four measured-condition verifications;
the CI cohort is collected separately before audit/sealing. Do not confuse this feasibility freeze
with final-study preregistration. Still needed: novelty/RQ decision, stronger precision/design,
network transfer to a second capable host, a working non-Chromium engine and OS-userland coverage.

## Prospective-v1 collection completed

19/19 calls completed and verified, sealed on CI and cloud; see live_frozen_v1_results.md.
Keep seed300/target host untouched by model tuning. Next: independently review the evidence and
resolve novelty/RQ, then specify adequate sample size/precision for a new main-study protocol;
repair Firefox ICE on a suitable environment and add a second netem-capable host/distinct OS
userland. Do not silently expand or retune the frozen-v1 protocol.
