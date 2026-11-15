# Assumption ledger

| Item | Status on 2026-11-15 | Evidence / next action |
|---|---|---|
| EASE 2027 deadline, page limits, open science and artifact rules | UNVERIFIED | Requests to candidate `conf.researchr.org` pages denied by environment proxy (403); verify official CFP after access is enabled |
| EASE ranking | USER-STATED TARGET | Verify against the ranking edition relevant to the institution; no claim in this artifact |
| WebRTC as final research direction | ASSUMPTION | Requires closest-work and dataset audit before W4 |
| 24-week timeline fits deadline | UNVERIFIED | Never infer deadline from planning dates |
| Locally isolated Chromium calls work | VERIFIED IN SMOKE | Three actual calls over local TURN/TCP, each with 24 samples |
| Host netem/CPU isolation available | FAILED CAPABILITY CHECK | No effective capabilities; user/network namespace creation denied; no host network commands attempted |
| Local TURN/TCP allowed | VERIFIED IN SMOKE | Loopback relay, peers restricted to 127.0.0.1, managed browser policy retained |
| Intervention observer is independent external ground truth | FALSE | Separate observation code in the same testbed; limited condition validation only |
| Public dataset with aligned media, traces and causal labels | UNVERIFIED | No such dataset is claimed |
| Cross-environment generalization | UNTESTED | New browser/machine/configuration splits needed |
| Added media information helps | UNTESTED | Pilot ablations check execution only; no scientific utility claim |

The cloud Chromium disables non-proxied UDP. The initial host-candidate call timed out and was
retained under `data/local/development-smoke`. A separate successful TURN smoke dataset is under
`data/local/turn-smoke`. Failed exploratory runs are not silently relabeled or mixed into the
subsequent, explicitly scoped pilot. Package installation used verified Debian metadata and archive
checksums, without system package modifications or changing Chromium policy.

## Superseding verification on 2026-11-15 after publication

Runtime public Internet is now unrestricted/enforced. Official 2027 CFP/home retrieved (HTTP200);
abstract 15 January 2027 AoE, full paper 22 January 2027 AoE, notification 12 March 2027 AoE.
See venue_verification.md/json. Earlier network-block/unknown-deadline entries above are historical.
The 24-week plan is superseded by ~68 calendar days to full paper. Homepage states CORE A; the
ranking database edition is not independently checked. Novelty initial audit is in novelty_audit.md;
claims remain provisional. Independent probe measurements do not validate live WebRTC causal labels.
