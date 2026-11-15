import pytest
from pydantic import ValidationError

from ease_rtc import live_lab
from ease_rtc.io import read_json
from ease_rtc.lab_sensors import interval_summary, verify_live
from ease_rtc.live_audit import check_lock, seal
from ease_rtc.live_lab import LiveProtocol, require_private_namespace


def evidence(family="normal", static=False):
    os_rows, pixels = [], []
    packets, drops = 0, 0
    for t in range(0, 11000, 200):
        during = 3000 < t < 7000
        packets += 10
        drops += 4 if during and family == "network_loss" else 0
        os_rows.append(
            {
                "monotonic_ms": t,
                "sender_cpu_core_percent": 95 if during and family == "compute_contention" else 10,
                "netem": {"packets": packets, "drops": drops},
            }
        )
        pixels.append(
            {
                "monotonic_ms": t,
                "source_pixel_sha256": "frozen"
                if static or (during and family == "source_freeze")
                else str(t),
            }
        )
    return os_rows, pixels


@pytest.mark.parametrize(
    "family", ["normal", "network_loss", "compute_contention", "source_freeze"]
)
def test_independent_observations_support_condition_but_never_causal_label(family):
    os_rows, pixels = evidence(family)
    result = verify_live(family, False, os_rows, pixels, 3000, 7000, 11000, True)
    assert result["verification_status"] == "verified"
    assert result["verified_condition"] == family
    assert result["causal_root_cause"] == "unestablished"


@pytest.mark.parametrize("family", ["network_loss", "compute_contention", "source_freeze"])
def test_request_and_interval_alone_cannot_verify_a_fault(family):
    rows, pixels = evidence()
    result = verify_live(family, False, rows, pixels, 3000, 7000, 11000, True)
    assert result["verified_condition"] is None
    assert verify_live(family, False, [], [], 3000, 7000, 11000, True)["verified_condition"] is None


def test_benign_static_content_is_a_control_not_a_fault():
    rows, pixels = evidence(static=True)
    assert (
        verify_live("normal", True, rows, pixels, 3000, 7000, 11000, True)["verified_condition"]
        == "normal"
    )
    assert (
        verify_live("source_freeze", False, rows, pixels, 3000, 7000, 11000, True)[
            "verified_condition"
        ]
        is None
    )


def test_failed_run_and_missing_recovery_cannot_gain_label():
    rows, pixels = evidence("network_loss")
    assert (
        verify_live("network_loss", False, rows, pixels, 3000, 7000, 11000, False)[
            "verification_status"
        ]
        == "failed"
    )
    assert (
        verify_live("network_loss", False, rows, pixels, 3000, None, 11000, True)[
            "verified_condition"
        ]
        is None
    )


def test_sensors_do_not_fabricate_loss_from_missing_packets():
    rows, pixels = evidence()
    for row in rows:
        row["netem"] = {"packets": 0, "drops": 0}
    assert interval_summary(rows, pixels, 300, 2700)["measured_drop_ratio"] is None


def test_host_network_cannot_be_used(monkeypatch):
    monkeypatch.delenv("EASE_PARENT_NETNS", raising=False)
    with pytest.raises(RuntimeError, match="distinct Docker"):
        require_private_namespace()


def test_protocol_rejects_missing_recovery_or_unsupported_engine():
    for update in [{"off_s": 10}, {"seeds": []}, {"engines": ["invented"]}]:
        with pytest.raises(ValidationError):
            LiveProtocol(**update)


def test_all_failed_calls_are_preserved_and_make_runner_fail(tmp_path, monkeypatch):
    monkeypatch.setattr(live_lab, "require_private_namespace", lambda: None)
    monkeypatch.delenv("EASE_EXPECTED_SOURCE_SHA256", raising=False)
    calls = []

    def fail_call(*args):
        calls.append(args)
        return {
            "execution_status": "failed",
            "verification_status": "failed",
            "engine": "chromium",
            "host_label": "test",
            "run_id": str(len(calls)),
        }

    monkeypatch.setattr(live_lab, "run_call", fail_call)
    protocol = LiveProtocol(
        network_backend="unimpaired", conditions=["normal"], engines=["chromium"], seeds=[42]
    )
    with pytest.raises(RuntimeError, match="calls failed"):
        live_lab.run(protocol, tmp_path)
    report = read_json(tmp_path / "summary.json")
    assert report["runs"] == report["failed"] == 2
    assert report["verified"] == 0


def test_dataset_seal_rejects_changed_or_added_observations(tmp_path):
    evidence = tmp_path / "measured.json"
    evidence.write_text('{"cpu":90}')
    seal(tmp_path)
    check_lock(tmp_path)
    evidence.write_text('{"cpu":0}')
    with pytest.raises(ValueError, match="Sealed dataset changed"):
        check_lock(tmp_path)


def test_unavailable_backend_cannot_masquerade_as_network_intervention():
    with pytest.raises(ValidationError, match="supported backend"):
        LiveProtocol(network_backend="unimpaired")
