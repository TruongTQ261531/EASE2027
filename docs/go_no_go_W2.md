# Initial W2-readiness memo — 2026-11-15

**Decision: GO for bounded feasibility work; NO-GO for topic lock, main-study claims or submission.**
This is the first implementation checkpoint, not a claim that two weeks of research or the whole
W2 gate are complete. The WebRTC candidate is still provisional.

| VERIFIED | ASSUMED | FAILED / unresolved | NEXT TEST |
|---|---|---|---|
| Actual WebRTC between two Chromium contexts through loopback TURN/TCP | Synthetic moving canvas is useful for initial instrumentation | Direct host-candidate call timed out under managed UDP policy; its failed manifest is retained | Add content diversity and benign/static-motion controls |
| 30 pilot calls, 10 each normal/pause/explicit-close; 720 samples and 180 windows | These simple conditions expose collection/evaluation defects | They do not satisfy >=3 fault families or independent causal validation | Add verified bandwidth/loss/CPU interventions in isolated lab |
| 30/30 pilot application conditions pass observer checks; all oracle verdicts replay from evidence | Pilot observer thresholds are adequate for a smoke test | Shared testbed and observer signals limit oracle independence; no calibrated label confidence | Independent instrumentation and negative/sham cases |
| 18/6/6 session split; frozen dataset fingerprint; strict model input whitelist | Session holdout suffices to check plumbing | Source seeds/environments/configurations not held out; six test calls have low precision | Freeze cross-condition/environment/source partitions for main study |
| Rules, dummy, logistic regression and random forest run; three feature sets; confusion matrices and session bootstrap exported | Ordinary models are sufficient starting points | No strongest prior-work/XGBoost baseline, missing-modality study, or calibrated superiority evidence | Audit prior work and add justified baselines |
| 36 local tests passed, including 3 actual browser calls; lint/format passed | GitHub-hosted CI setup is portable | CI has not run remotely; no second-machine reproduction | Run workflow after source review/push and reproduce on a second machine |
| Rootless signed Debian coturn setup exercised in a fresh prefix; Python dependencies locked | Snapshot restoration will retain prepared files | No published/new-task restoration verified | Review/save draft and publish when appropriate, then test a new task |
| W3C primary source retrieved; adjacent RCA/SWE citations and code licenses inspected | Those leads can inform the literature search | Closest WebRTC work and novelty remain unaudited | Read >=5 truly close papers with claim/evaluation comparisons |
| RCAEval-linked CSV downloaded: 721 rows, 58 columns, consistent shape | Small tabular backup is resource-feasible | Dataset license/labels not verified; SWE-bench data-card and RCAEval case-index requests denied | Download labeled licensed samples and replay backup baselines |
| CFP requests returned proxy 403; network-domain draft additions saved | Candidate Researchr routes may be the correct official pages | Official site/CFP/deadline/page limits/artifact rules and venue ranking unverified | Enable sources and verify official pages; re-plan schedule |

Evidence: `data/local/pilot-v0.1/reports/{audit,metrics,splits}.json`, the generated
[pilot summary](pilot_results.json), [source access log](source_access_audit.json), and
[protocol](pilot_protocol.md). Source files were uncommitted during collection; manifests record
the initial Git HEAD, dirty status and the actual source-tree SHA256. No claim of a reproducible
published Git revision is made. Raw observations remain local and Git-ignored.

Re-running evaluation on the frozen dataset reproduced `metrics.json`, `splits.json` and
`report.md` byte-for-byte. Python wheel build also passed; the wheel contains the required browser
HTML asset and excludes observations. This verifies current-instance repeatability and packaging,
not new-machine data reproduction. Total recorded collection wall time was 248.56 seconds.

Several models and rules score 1.0 on this deliberately easy six-session test set. This does not
show media utility: rules and telemetry-only logistic regression already separate these cases.
Do not tune a new model to this test set or use those scores in an EASE abstract as evidence of
real root-cause performance. Prepare harder experiments and a new frozen dataset instead.

Early failed host-candidate smoke: one run, zero samples, failed verification. Separate TURN smoke:
three successful calls. The 30-call pilot is a new protocol-scoped dataset; its 30/30 figure does not
include or conceal these exploratory attempts. Browser tests use independent temporary datasets.

Configuration draft saved: `install_script`, `start_skill`, and six custom source domains
(`conf.researchr.org`, `www.w3.org`, `huggingface.co`, `dl.acm.org`, `arxiv.org`, `api.crossref.org`).
The existing package-manager preset is preserved. Saving the draft does not apply access or
publish the environment. No required credentials or paid service were introduced.

## Subsequent verification (same date, new published runtime)

Earlier CFP/network-block statements above are historical. CFP verified; see venue_verification.md.
Full paper 22 January 2027 AoE, not 24 weeks away. Novelty remains unestablished after direct
prior-work discovery (novelty_audit.md). Independent oracle-probe results are separate from
the original application-condition pilot (oracle_independence.md). No causal labels were upgraded.
