import os
from pathlib import Path

import pytest

from ease_rtc.audit import audit
from ease_rtc.collect import collect
from ease_rtc.features import build_features
from ease_rtc.io import read_json
from ease_rtc.schema import Scenario

pytestmark = [
    pytest.mark.browser,
    pytest.mark.skipif(
        os.environ.get("EASE_RUN_BROWSER") != "1",
        reason="Set EASE_RUN_BROWSER=1 for actual Chromium + coturn calls",
    ),
]


@pytest.mark.parametrize("condition", ["normal", "capture_pause", "connection_close"])
def test_real_call_verified_condition_and_trace_integrity(tmp_path, condition):
    manifest = collect(
        Scenario(name=condition, intervention=condition),
        tmp_path,
        Path(__file__).resolve().parents[1],
    )
    assert manifest.execution_status == "completed"
    assert manifest.sample_count >= 15
    assert manifest.codecs
    oracle = read_json(tmp_path / "oracle" / f"{manifest.run_id}.json")
    assert oracle["verification_status"] == "verified"
    assert oracle["verified_condition"] == condition
    assert oracle["causal_root_cause"] == "unestablished"
    assert audit(tmp_path)["verified_rate"] == 1
    windows = build_features(tmp_path)
    assert len(windows) >= 5
    # A changed raw observation invalidates the manifest, even if JSON still parses.
    stats = tmp_path / "raw" / manifest.run_id / "stats.jsonl"
    stats.write_text(stats.read_text() + "\n")
    with pytest.raises(ValueError, match="Checksum mismatch"):
        audit(tmp_path)
