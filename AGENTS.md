# Research delivery instructions

- The user requires completed work to be committed and pushed to GitHub after each meaningful
  milestone. This authorizes ordinary fast-forward pushes of reviewed project results; do not
  force-push, rewrite shared history, or mark incomplete research gates as complete.
- Before pushing, run checks appropriate to the changes, inspect the staged diff, and exclude
  credentials, local browser profiles, internal network identifiers and third-party files whose
  redistribution rights have not been established.
- Publish code, protocols, measured results including failures, decisions, limitations and source
  references. Export sanitized synthetic observations with `scripts/export_results.py` where
  applicable. Keep original measurements immutable under ignored `data/local/`.
- After a push, verify the remote branch SHA. Report the commit/link, locations of results, and
  any actual push or CI blocker. Do not ask for GitHub tokens merely because token variables
  are absent; use the existing HTTPS proxy authentication.
- Continue to follow `docs/research_contract.md`. Distinguish requested intervention, measured
  condition, observed degradation and causal attribution. Never claim novelty or submission
  readiness without evidence. Each cloud task is isolated; use the existing checkout.
