# Published synthetic research observations

`2026-11-15/` contains the completed local pilot, transfer, instrumentation probes, and exploratory
successes/failures. This is a **sanitized derivative** of `data/local/`, not a new collection.

- Browser candidate addresses/IPs/ports/TURN URLs/ICE usernames and certificates are removed.
- Numeric measurements, timelines, source observer fingerprints, features, labels and predictions
  are retained. Normalized observation features were compared with originals and match exactly.
- File checksums in manifests and frozen-split dataset fingerprints were recalculated. Original
  file hashes and transformation details are retained in `release_provenance.json`.
- Manifests preserve the original Git HEAD, dirty flag and source hash. Collection preceded the
  first implementation commit; do not misrepresent that initial HEAD as containing the full code.
- `transfer-v1/metrics.json` is the original report, with original dataset references;
  `transfer-v1/release_metrics.json` is re-evaluation from the sanitized published datasets.
- No labels have been upgraded to causal root causes. Keep ambiguous/failed runs in denominator.
- Generated probes include synthetic frozen/moving FFV1 fixtures, not recordings of people.

The code supports the original failed no-STUN transport profile to preserve historical evidence;
new collection defaults to loopback TURN/TCP. The failed exploratory run remains failed.

Re-evaluate the published data without a camera, microphone or browser:

```bash
uv sync --frozen
uv run --frozen ease-rtc audit --dataset data/releases/2026-11-15/pilot-v0.1
uv run --frozen ease-rtc evaluate --dataset data/releases/2026-11-15/pilot-v0.1
uv run --frozen python -m ease_rtc.transfer \
  --training data/releases/2026-11-15/pilot-v0.1 \
  --fresh-source data/releases/2026-11-15/transfer-v1/source \
  --target data/releases/2026-11-15/transfer-v1/target \
  --output /tmp/new-transfer-evaluation.json
```

Use an output filename that does not exist. Reproducing *new observations* needs Chromium/coturn
and will not produce identical timing, UUIDs or scores. GitHub is not an archival DOI.

Project-generated synthetic observations/fixtures in this release are licensed under
[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Attribution: EASE2027 research project,
https://github.com/TruongTQ261531/EASE2027, release directory and associated commit. Source code
remains MIT under the top-level LICENSE. No third-party paper PDF or benchmark data is included.
