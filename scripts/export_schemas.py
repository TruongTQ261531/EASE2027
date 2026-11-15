"""Export the executable schema contract. Run from the repository root."""

from pathlib import Path

from ease_rtc.io import write_json
from ease_rtc.schema import FeatureWindow, OracleEvent, RunManifest, Scenario

for name, model in [
    ("run_manifest", RunManifest),
    ("feature_window", FeatureWindow),
    ("oracle_event", OracleEvent),
    ("scenario", Scenario),
]:
    write_json(Path("schemas") / f"{name}.schema.json", model.model_json_schema())
