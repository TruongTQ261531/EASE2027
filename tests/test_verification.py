from ease_rtc.schema import Scenario
from ease_rtc.verification import verify


def observations(paused=False, closed=False):
    source, receiver = [], []
    for i, t in enumerate(range(0, 6000, 250)):
        fingerprint = "frozen" if paused and 2000 <= t <= 4000 else str(i)
        source.append({"monotonic_ms": t, "fingerprint": fingerprint})
        receiver.append(
            {
                "monotonic_ms": t,
                "receiver_fingerprint": fingerprint,
                "connection_state": "closed" if closed and t >= 2000 else "connected",
            }
        )
    return source, receiver


def test_requested_intervention_without_observed_effect_is_not_verified():
    source, receiver = observations()
    result = verify(
        "r",
        "s",
        Scenario(name="pause", intervention="capture_pause"),
        receiver,
        source,
        2000,
        4000,
        True,
    )
    assert result.verification_status == "ambiguous"
    assert result.verified_condition is None


def test_source_pause_requires_motion_before_and_after():
    source, receiver = observations(paused=True)
    config = Scenario(name="pause", intervention="capture_pause")
    result = verify("r", "s", config, receiver, source, 2000, 4000, True)
    assert result.verification_status == "verified"
    assert result.observed_degradation == "yes"
    assert result.causal_root_cause == "unestablished"
    for row in source:
        row["fingerprint"] = "static-from-start"
    result = verify("r", "s", config, receiver, source, 2000, 4000, True)
    assert result.verification_status == "ambiguous"


def test_failed_execution_and_undispatched_commands_never_get_labels():
    source, receiver = observations(paused=True)
    config = Scenario(name="pause", intervention="capture_pause")
    for completed, start in [(False, 2000), (True, None)]:
        result = verify("r", "s", config, receiver, source, start, 4000, completed)
        assert result.verified_condition is None


def test_condition_is_not_synonymous_with_degradation():
    source, receiver = observations()
    for row in receiver:
        row["receiver_fingerprint"] = "stuck"
    result = verify(
        "r", "s", Scenario(name="normal", intervention="normal"), receiver, source, 2000, 4000, True
    )
    assert result.verified_condition == "normal"
    assert result.observed_degradation == "yes"
    assert result.causal_root_cause == "unestablished"
