import json
from pathlib import Path

import jsonschema
import pytest
from pydantic import ValidationError

from ease_rtc.schema import Features, FeatureWindow, OracleEvent, RunManifest, Scenario

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize(
    "name,model",
    [
        ("run_manifest", RunManifest),
        ("feature_window", FeatureWindow),
        ("oracle_event", OracleEvent),
        ("scenario", Scenario),
    ],
)
def test_exported_schema_matches_executable_contract(name, model):
    assert (
        json.loads((ROOT / "schemas" / f"{name}.schema.json").read_text())
        == model.model_json_schema()
    )


def test_json_schema_accepts_observation_and_rejects_oracle_fields():
    schema = FeatureWindow.model_json_schema()
    record = FeatureWindow(
        run_id="r",
        session_id="s",
        window_start_ms=0,
        window_end_ms=1000,
        features=Features(decoded_fps=20),
    ).model_dump()
    jsonschema.validate(record, schema)
    record["injection_type"] = "packet_loss"
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(record, schema)


def test_invalid_intervention_timing_rejected():
    with pytest.raises(ValidationError):
        Scenario(name="bad", intervention="normal", intervention_start_s=4, intervention_end_s=2)


def test_historical_failed_run_keeps_its_actual_no_stun_transport():
    directory = ROOT / "data/releases/2026-11-15/development-smoke/manifests"
    manifest = RunManifest.model_validate(json.loads(next(directory.glob("*.json")).read_text()))
    assert manifest.network_profile == "local_host_candidates_no_stun"
    assert manifest.execution_status == "failed"
    assert manifest.sample_count == 0
