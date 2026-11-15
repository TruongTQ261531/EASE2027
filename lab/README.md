# Isolated live-call lab (feasibility stage)

The handoff is an execution blueprint with explicit verification gates, not proof that novelty,
oracle validity or cross-environment performance are already established. We are executing
its live-oracle and protocol stages without silently treating those gates as completed.

```bash
bash lab/build.sh
bash lab/run.sh configs/experiments/live_cloud_pilot.json data/local/NEW-cloud-pilot codex-cloud
# On an isolated Linux machine/runner whose kernel supports prio/netem:
bash lab/run.sh configs/experiments/live_pilot.json data/local/NEW-full-pilot my-linux-lab
uv run --frozen python -m ease_rtc.live_audit --dataset data/local/NEW-full-pilot --seal
```

Build: pinned Python dependency lock, Playwright browser revisions, system packages, TLS and
APT signature verification intact. The session CA is a BuildKit secret and is not retained.
Only our newly created Docker container receives NET_ADMIN/NET_RAW. Every invocation creates
and removes its own `--internal` Docker network (no public egress). Browser ICE requires a
non-loopback interface; TURN control/signaling use loopback; the relay binds only its own private container address. Do not use host networking.
No tc command executes before checking a distinct container network namespace and expected
interface names. Qdisc is attached only to container loopback; filter selects the private TURN
relay UDP port range. CDP/signaling TCP are not intentionally shaped. Two separate browser
instances are used; no shared sender/receiver process. No camera, microphone or external TURN.

## Conditions and independent measurement paths

- **Network loss:** change container netem qdisc; a separate OS observer reads actual kernel
  packet/drop counters before/during/after. Requested percentage is not a measured label.
- **Compute contention:** block the sender browser main thread periodically. Separate OS observer
  reads sender process-tree CPU deltas, requires an increase and recovery. This is sender browser
  contention, not proof of host/encoder saturation.
- **Source freeze:** pause synthetic source updates. Browser screenshot pixels are hashed through
  a separate capture API, without reading pause flags or generator counters; require motion before,
  stability during and motion after. This is a source freeze, not hardware-camera diagnosis.
- **Controls:** moving-content sham and intentionally static benign content. Static content must
  not become a capture-failure label. Degradation metrics are distinct from fault verification.

The OS observer gets a process identity and common monotonic clock, **not** injection type,
intensity or schedule. Source pixel capture shares the orchestration process, so measurement-path
independence is stronger than the first pilot but is not complete failure-domain independence.
All inference feature files are reconstructed only from receiver observations. Injection metadata,
OS oracle observations and source screenshots remain in separate oracle files. Every causal root
cause field remains `unestablished`.

## Pilot first; freeze before main experiments

Current configuration is a debugging/feasibility pilot, not a final-study preregistration. Failed
startup, ambiguous verification and missing evidence remain in the denominator and on disk.
`live_audit` replays oracle decisions and validates numeric feature reconstruction. `--seal`
writes an inventory lock which rejects later dataset modification. A protocol/source/dependency
lock and grouped partitions must be recorded before collecting a prospective frozen dataset.
No promise of a main-track-ready dataset or powered statistical study follows from smoke tests.

## Runtime observations so far

The restored cloud has a working rootless Docker daemon. NET_ADMIN exists inside our private
container, but its host kernel does not provide prio/netem (`Specified qdisc kind is unknown`).
The cloud configuration therefore explicitly excludes network faults and declares an unimpaired
backend; it never invents a zero-loss measurement. Full-network pilot runs in the separate
GitHub Ubuntu runner through `.github/workflows/live-lab.yml`. A runtime failure still produces
retained evidence and a failing exit status; it cannot count as successful injection.

GitHub pilot evidence is sanitized, uploaded as an Actions artifact and committed under
`data/releases/live-pilot/ci-<run-id>/` using the user's standing instruction. It is a named
development repository, not an anonymized paper supplement. Kernel/image/browser/host labels and
source hashes distinguish environments. A CI run is only claimed successful after its outcome
and dataset audit are inspected.
