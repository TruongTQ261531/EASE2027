import pytest

from ease_rtc.oracle_probes import verdict


@pytest.mark.parametrize("family", ["network", "compute", "media"])
def test_request_without_measurements_cannot_verify(family):
    assert verdict(family, {}, True)["status"] == "ambiguous"


@pytest.mark.parametrize(
    "family,measurement",
    [
        ("network", {"sent": 60, "unique_received": 60}),
        ("compute", {"cpu_core_percent": 0.0}),
        ("media", {"decoded_frame_hashes": [str(i) for i in range(20)]}),
    ],
)
def test_unobserved_requested_effect_fails_and_valid_sham_passes(family, measurement):
    assert verdict(family, measurement, True)["status"] == "failed"
    assert verdict(family, measurement, False)["status"] == "verified"


@pytest.mark.parametrize(
    "family,measurement",
    [
        ("network", {"sent": 60, "unique_received": 40}),
        ("compute", {"cpu_core_percent": 95.0}),
        ("media", {"decoded_frame_hashes": ["same"] * 20}),
    ],
)
def test_measurement_detects_unrequested_effect_in_sham(family, measurement):
    assert verdict(family, measurement, False)["status"] == "failed"
    assert verdict(family, measurement, True)["status"] == "verified"
