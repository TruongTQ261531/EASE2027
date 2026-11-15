import numpy as np
import pytest
from pydantic import ValidationError

from ease_rtc.features import model_matrix, normalize
from ease_rtc.schema import Features, FeatureWindow


def sample(t, byte_count, frames, packets=100, lost=0, stream="video-1"):
    return {
        "monotonic_ms": t,
        "receiver_stats": [
            {
                "type": "inbound-rtp",
                "kind": "video",
                "id": stream,
                "transportId": "transport",
                "bytesReceived": byte_count,
                "framesDecoded": frames,
                "packetsReceived": packets,
                "packetsLost": lost,
                "framesDropped": 0,
                "jitter": 0.003,
            },
            {"type": "transport", "id": "transport", "selectedCandidatePairId": "pair"},
            {"type": "candidate-pair", "id": "pair", "currentRoundTripTime": 0.012},
        ],
    }


def obs(t, fingerprint="abc"):
    return {"monotonic_ms": t, "connection_state": "connected", "receiver_fingerprint": fingerprint}


def test_units_counter_deltas_and_first_sample_missing():
    rows = normalize(
        [sample(0, 1000, 10), sample(1000, 2000, 30, 190, 10)], [obs(0), obs(1000, "def")]
    )
    assert rows[0][1].decoded_fps is None
    values = rows[1][1]
    assert values.receive_kbps == 8
    assert values.decoded_fps == 20
    assert values.jitter_ms == 3
    assert values.rtt_ms == 12
    assert values.packet_loss_ratio == 0.1
    assert values.video_change_fraction == 1


@pytest.mark.parametrize("second", [sample(1000, 0, 0), sample(1000, 2000, 30, stream="new")])
def test_counter_resets_and_stream_switch_are_missing(second):
    result = normalize([sample(0, 1000, 10), second], [obs(0), obs(1000)])[1][1]
    assert result.receive_kbps is None
    assert result.decoded_fps is None


def test_missing_field_is_not_zero_and_zero_increment_is_zero():
    first, second = sample(0, 1000, 10), sample(1000, 1000, 10)
    del second["receiver_stats"][0]["jitter"]
    result = normalize([first, second], [obs(0), obs(1000)])[1][1]
    assert result.jitter_ms is None
    assert result.receive_kbps == 0
    assert result.decoded_fps == 0
    assert result.packet_loss_ratio is None


@pytest.mark.parametrize("times", [(0, 0), (1000, 500), (0, -100)])
def test_nonmonotonic_timestamps_rejected(times):
    with pytest.raises(ValueError, match="timeline"):
        normalize([sample(t, 1000, 10) for t in times], [obs(t) for t in times])


def test_misaligned_streams_rejected():
    with pytest.raises(ValueError, match="timeline"):
        normalize([sample(0, 100, 10)], [obs(5)])


@pytest.mark.parametrize(
    "name",
    [
        "scenario_id",
        "seed",
        "injection_start_ms",
        "label",
        "fault_injected",
        "source_fingerprint",
        "run_id",
        "filename",
    ],
)
def test_unknown_model_fields_rejected(name):
    with pytest.raises(ValidationError):
        Features(**{name: 1})
    with pytest.raises(ValueError, match="approved"):
        model_matrix([Features(decoded_fps=20)], [name])


def test_identifier_changes_do_not_change_model_inputs():
    records = [
        FeatureWindow(
            run_id=run_id,
            session_id=run_id,
            window_start_ms=0,
            window_end_ms=1000,
            features=Features(decoded_fps=20),
        )
        for run_id in ["normal-looking-name", "fault-looking-name"]
    ]
    matrix = model_matrix([r.features for r in records], ["decoded_fps", "rtt_ms"])
    np.testing.assert_equal(matrix[0], matrix[1])


def test_nonfinite_and_invalid_units_rejected():
    for fields in [{"rtt_ms": float("nan")}, {"jitter_ms": -1}, {"packet_loss_ratio": 1.1}]:
        with pytest.raises(ValidationError):
            Features(**fields)
