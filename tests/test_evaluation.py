import pytest

from ease_rtc.evaluate import CLASSES, clustered_f1_interval, split_sessions, validate_split
from ease_rtc.io import safe_path


def test_splits_partition_sessions_and_keep_all_conditions():
    labels = {f"{c}-{i}": c for c in CLASSES for i in range(10)}
    splits = split_sessions(labels, 42)
    assert splits == split_sessions(labels, 42)
    assert {k: len(v) for k, v in splits.items()} == {"train": 18, "validation": 6, "test": 6}
    for partition in splits.values():
        assert {labels[s] for s in partition} == set(CLASSES)


def test_split_overlap_and_incomplete_coverage_rejected():
    for splits in [
        {"train": ["a"], "validation": ["b"], "test": ["a"]},
        {"train": ["a"], "validation": ["b"], "test": ["c"]},
    ]:
        with pytest.raises(ValueError, match="overlaps|cover"):
            validate_split(splits, {"a", "b", "c", "d"})


def test_insufficient_sessions_cannot_produce_a_score():
    with pytest.raises(ValueError, match="at least"):
        split_sessions({f"{c}-{i}": c for c in CLASSES for i in range(4)}, 42)


def test_bootstrap_resamples_whole_sessions():
    y = CLASSES * 3
    prediction = ["normal"] * len(y)
    sessions = [f"s-{i}" for i in range(len(y))]
    interval = clustered_f1_interval(y, prediction, sessions, 42, 100)
    # Duplicating every row within a session must not fake a larger effective sample size.
    repeated = clustered_f1_interval(y * 2, prediction * 2, sessions * 2, 42, 100)
    assert interval == repeated


def test_paths_cannot_escape_dataset(tmp_path):
    with pytest.raises(ValueError, match="escapes"):
        safe_path(tmp_path, "../outside")
