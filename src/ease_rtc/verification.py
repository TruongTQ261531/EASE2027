"""Conservative application-condition verification; never a causal root-cause oracle."""

from ease_rtc.schema import OracleEvent, Scenario


def change_fraction(rows: list[dict], key: str) -> float | None:
    pairs = [(a.get(key), b.get(key)) for a, b in zip(rows, rows[1:], strict=False)]
    values = [float(a != b) for a, b in pairs if a is not None and b is not None]
    return sum(values) / len(values) if values else None


def verify(
    run_id: str,
    session_id: str,
    config: Scenario,
    observations: list[dict],
    source_observations: list[dict],
    actual_start_ms: float | None,
    actual_end_ms: float | None,
    completed: bool,
) -> OracleEvent:
    start = actual_start_ms if actual_start_ms is not None else float("inf")
    end = actual_end_ms if actual_end_ms is not None else config.duration_s * 1000
    # Ignore a sample interval at boundaries: browser command execution is asynchronous.
    margin = config.sample_interval_ms
    before = [r for r in source_observations if r["monotonic_ms"] < start - margin]
    during = [r for r in source_observations if start + margin < r["monotonic_ms"] < end]
    after = [r for r in source_observations if r["monotonic_ms"] > end + margin]
    source_before = change_fraction(before, "fingerprint")
    source_during = change_fraction(during, "fingerprint")
    source_after = change_fraction(after, "fingerprint")
    receive_during = [r for r in observations if start + margin < r["monotonic_ms"] < end]
    receiver_change = change_fraction(receive_during, "receiver_fingerprint")
    closed = [r["connection_state"] == "closed" for r in receive_during]
    closed_fraction = sum(closed) / len(closed) if closed else None
    verified = False
    if completed and actual_start_ms is not None and len(during) >= 3:
        if config.intervention == "normal":
            # A completed sham command with live source; does NOT prove absence of faults.
            verified = source_before is not None and source_before > 0.5
            verified = verified and source_during is not None and source_during > 0.5
        elif config.intervention == "capture_pause":
            verified = source_before is not None and source_before > 0.5
            verified = verified and source_during == 0.0
            verified = verified and source_after is not None and source_after > 0.5
        elif config.intervention == "connection_close":
            verified = closed_fraction == 1.0
    degradation = "unknown"
    if receiver_change is not None:
        degradation = "yes" if receiver_change < 0.25 else "no"
    if closed_fraction == 1.0:
        degradation = "yes"
    status = "verified" if verified else ("ambiguous" if completed else "failed")
    return OracleEvent(
        run_id=run_id,
        session_id=session_id,
        requested_condition=config.intervention,
        verification_status=status,
        verified_condition=config.intervention if verified else None,
        observed_degradation=degradation,
        label_confidence="medium" if verified else "low",
        requested_start_ms=config.intervention_start_s * 1000,
        requested_end_ms=config.intervention_end_s * 1000,
        actual_start_ms=actual_start_ms,
        actual_end_ms=actual_end_ms,
        measurements={
            "source_before_change_fraction": source_before,
            "source_during_change_fraction": source_during,
            "source_after_change_fraction": source_after,
            "receiver_during_change_fraction": receiver_change,
            "receiver_closed_fraction": closed_fraction,
            "during_observations": len(during),
        },
        evidence_paths=[f"oracle/{run_id}/source.jsonl", f"raw/{run_id}/observations.jsonl"],
        limitation=(
            "Application-condition check from a separate observation path in the same testbed. "
            "Not external instrumentation or independent causal attribution. Receiver pc.close "
            "is an explicit closure, not ICE/network failure. No-fault is a sham protocol label."
        ),
    )
