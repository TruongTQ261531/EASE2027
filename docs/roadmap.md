# Evidence-driven roadmap

Start date: 2026-11-15 (Asia/Bangkok). These are internal planning dates, **not conference
deadlines**. A 24-week plan is not assumed to fit EASE 2027. Re-plan immediately after obtaining
the official CFP. No participant studies, large manual labeling or paid-model dependency.

Execution order confirmed by the user on 2026-11-15: (1) verify CFP/deadline,
(2) audit novelty, (3) independent oracles for multiple fault families,
(4) evaluate across environments. Stage 1 CFP verification is now complete;
see [the verification record](venue_verification.md). Do not mark later stages complete on the
basis of the existing feasibility pilot.

| Gate | Planning date | Evidence required |
|---|---|---|
| W2 | 2026-11-29 | Reproducible collector, >=10 clean sessions, schemas/QC, initial audited closest-work list |
| W4 | 2026-12-13 | >=3 fault families plus controls with independent verification; actual backup samples/license/labels; topic decision |
| W6 | 2026-12-27 | Data schema/QC freeze; ambiguous-label report; modality keep/drop decision |
| W8 | 2027-01-10 | Meaningful held-out baseline and defensible oracle; otherwise hard pivot |
| W12 | 2027-02-07 | Final-study protocol before test, fair ablations, resource costs, precision/power rationale |
| W16 | 2027-03-07 | Main experiments, multiple seeds, environment/configuration holdouts, uncertainty and failure analysis |
| W20 | 2027-04-04 | Manuscript claims trace to sources/experiments; artifact audit and reviewer challenge checklist |
| W24 | 2027-05-02 | Submission package only if official schedule and evidence support it |

## Next executable work

1. Enable the pending research-source domains and rerun `scripts/audit_sources.py`. Confirm the
   actual official conference site/track, dates, page limits, anonymization and open-science rules.
2. Search 2024–2026 direct WebRTC fault diagnosis/QoE work; read at least five truly close works.
   Replace citation leads with claim/evaluation overlap backed by full text. The current adjacent
   RCA references do not complete this step.
3. Prepare an isolated Linux network namespace/container lab with explicit NET_ADMIN scope.
   Verify measured packet loss, bandwidth and CPU utilization independently of the commands.
   Keep unsuccessful injections and sham/normal controls. Current cloud cannot provide this.
4. Introduce symptom-equivalent pairs, benign pauses/static video, adaptation, injected-but-no-
   degradation cases and unrequested degradation. Investigate observer/feature circularity.
5. Add strong tree/prior-work baselines, per-modality and missing-modality tests, calibration,
   inference/detection latency, and total browser+relay collection costs. Freeze partitions by
   session **and** independent environment/fault configuration before the main study.
6. Download a labeled licensed sample for RCAEval and issue/failure localization; independently
   reproduce one baseline for each viable backup. Do not commit a topic on repository access alone.

Every gate gets VERIFIED / ASSUMED / FAILED / NEXT TEST entries and an explicit go/no-go result.
If defensible labels and novelty never materialize, release an honest artifact/technical report
instead of presenting the feasibility classifier as a conference-ready study.

## Schedule correction after official CFP verification

The 24-week dates above are superseded historical planning assumptions. Full paper is due
22 January 2027 AoE, only 68 calendar days from 15 November 2026. See venue_verification.md.

| Internal gate | Target | Decision evidence |
|---|---|---|
| Topic/novelty decision | 22 November 2026 | Closest direct work + defensible differentiated RQ; otherwise pivot |
| Oracle feasibility | 29 November 2026 | Independently observed interventions, controls, ambiguity rates |
| Dataset/protocol freeze | 6 December 2026 | Grouped environment/configuration splits, precision plan, strong baselines |
| Main experiments | 7–27 December 2026 | Resource-feasible runs and cross-environment failures retained |
| Manuscript and artifact | 28 December–10 January | Claims traced to evidence, anonymization and reproduction |
| Internal abstract | 12 January 2027 | Submit before official 15 January AoE |
| Internal full paper | 19 January 2027 | Submit before official 22 January AoE |

These targets are conditional on novelty and oracle gates, not an acceptance or readiness promise.
