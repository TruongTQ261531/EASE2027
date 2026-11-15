import hashlib
import json
from types import SimpleNamespace

import numpy as np
import pytest

from ease_rtc import transfer
from ease_rtc.evaluate import CLASSES
from ease_rtc.io import sha256, write_json
from ease_rtc.schema import Features


def test_transfer_fits_only_frozen_source_train_and_rejects_session_overlap(tmp_path, monkeypatch):
    source, control, target = [tmp_path / n for n in ["training", "control", "target"]]
    for directory in [source, control, target]:
        (directory / "manifests").mkdir(parents=True)
        write_json(directory / "manifests/a.json", {"test_fixture": True})
    (source / "features").mkdir()
    (source / "features/windows.jsonl").write_text("test fixture\n")
    fingerprint = hashlib.sha256(
        json.dumps(
            {
                "features_sha256": sha256(source / "features/windows.jsonl"),
                "manifests": {"a.json": sha256(source / "manifests/a.json")},
            },
            sort_keys=True,
        ).encode()
    ).hexdigest()
    partitions = {
        part: [f"{part}-{c}" for c in CLASSES] for part in ["train", "validation", "test"]
    }
    write_json(
        source / "reports/splits.json", {"dataset_sha256": fingerprint, "partitions": partitions}
    )

    def records(directory):
        ids = (
            [s for p in partitions.values() for s in p]
            if directory == source
            else [f"{directory.name}-{c}" for c in CLASSES]
        )
        # Evaluation observations differ substantially; none may enter estimator.fit.
        value = 20 if directory == source else 1000
        rows = {
            s: Features(decoded_fps=value, closed_fraction=0, connected_fraction=1) for s in ids
        }
        labels = {s: next(c for c in CLASSES if s.endswith(c)) for s in ids}
        return (
            rows,
            labels,
            {s: directory.name for s in ids},
            {"verified": len(ids)},
            [SimpleNamespace(browser_version="A" if directory != target else "B")],
        )

    monkeypatch.setattr(transfer, "dataset_records", records)
    # Avoid hundreds of bootstrap draws in this focused training-boundary test.
    monkeypatch.setattr(transfer, "clustered_f1_interval", lambda *_args: [0.0, 1.0])
    from sklearn.pipeline import Pipeline

    original_fit, fitted = Pipeline.fit, []

    def observed_fit(self, x, y, **kwargs):
        fitted.append(np.array(x))
        assert len(x) == 3
        assert len(y) == 3
        assert np.nanmax(x) <= 20
        return original_fit(self, x, y, **kwargs)

    monkeypatch.setattr(Pipeline, "fit", observed_fit)
    result = transfer.evaluate_transfer(source, control, target, tmp_path / "metrics.json")
    assert len(fitted) == 9
    assert result["source_test_sessions_used_for_training_or_tuning"] == 0
    assert len(result["results"]) == 20
    assert result["evaluation_versions"]["fresh_other_version"] == ["B"]

    def overlapping_records(directory):
        return records(source if directory == target else directory)

    monkeypatch.setattr(transfer, "dataset_records", overlapping_records)
    with pytest.raises(ValueError, match="more than one cohort"):
        transfer.evaluate_transfer(source, control, target, tmp_path / "bad.json")


def test_transfer_does_not_overwrite_prior_results(tmp_path):
    output = tmp_path / "result.json"
    output.write_text("preserve")
    with pytest.raises(ValueError, match="overwrite"):
        transfer.evaluate_transfer(tmp_path, tmp_path, tmp_path, output)
    assert output.read_text() == "preserve"
