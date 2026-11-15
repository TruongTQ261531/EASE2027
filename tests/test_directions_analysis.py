"""Scientific failure modes: leakage, unsupported certainty, ties and missing labels."""

import copy
import importlib.util
import sys
from pathlib import Path

import numpy as np
import pytest

from ease_rtc.io import read_json
from ease_rtc.schema import Features, FeatureWindow

ROOT = Path(__file__).resolve().parents[1]


def module(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    result = importlib.util.module_from_spec(spec)
    sys.modules[name] = result
    spec.loader.exec_module(result)
    return result


analysis = module("diagnostic_analysis")
oracle = module("oracle_validity_audit")
CONFIG = read_json(ROOT / "configs/analysis/directions_v1.json")


def rows(role="calibration", seed=200):
    return [
        {
            "session_id": f"{role}-{i}",
            "role": role,
            "seed": seed,
            "label": "normal" if stratum.startswith("normal") else stratum,
            "stratum": stratum,
            "current": Features(decoded_fps=float(i), receive_kbps=float(i * 10)),
            "history": Features(decoded_fps=20.0),
        }
        for i, stratum in enumerate(CONFIG["strata"])
    ]


def correct_probabilities(records):
    return np.array([[float(r["label"] == c) for c in CONFIG["classes"]] for r in records])


def test_exact_zero_error_bound_does_not_certify_tiny_sample():
    assert analysis.risk_upper(0, 5, 0.05) == pytest.approx(1 - 0.05 ** (1 / 5))
    assert analysis.risk_upper(0, 0, 0.05) == 1
    assert analysis.risk_upper(5, 5, 0.05) == 1
    assert analysis.risk_upper(1, 5, 0.05) > analysis.risk_upper(0, 5, 0.05)
    assert analysis.minimum_zero_error_count(0.1, 0.05) == 29
    assert analysis.minimum_zero_error_count(0.05, 0.05) == 59
    assert analysis.minimum_zero_error_count(0.1, 0.05 / 225) == 80
    assert analysis.minimum_zero_error_count(0.05, 0.05 / 225) == 164
    for risk in [0.05, 0.1, 0.2]:
        n = analysis.minimum_zero_error_count(risk, 0.05 / 225)
        assert analysis.risk_upper(0, n, 0.05 / 225) <= risk
        assert analysis.risk_upper(0, n - 1, 0.05 / 225) > risk


@pytest.mark.parametrize("errors,n,alpha", [(-1, 2, 0.05), (3, 2, 0.05), (0, 2, 0), (0.5, 2, 0.05)])
def test_bad_bound_arguments_rejected(errors, n, alpha):
    with pytest.raises(ValueError):
        analysis.risk_upper(errors, n, alpha)


def test_zero_validation_errors_still_abstain_when_evidence_is_insufficient():
    records = rows()
    selected = analysis.calibrate(records, correct_probabilities(records), CONFIG)
    assert selected["candidate_count_including_strata"] == 225
    assert selected["empirical_threshold"] == 0
    assert selected["bound_rule_threshold"] is None
    assert not selected["deployment_risk_certified"]
    assert selected["candidates"][0]["max_stratum_upper_bound"] > 0.99


def test_missing_stratum_cannot_gain_a_certified_policy():
    records = rows()[:1]
    selected = analysis.calibrate(records, correct_probabilities(records), CONFIG)
    assert all(c["max_stratum_upper_bound"] == 1 for c in selected["candidates"])
    assert selected["bound_rule_threshold"] is None


def test_target_rows_are_rejected_by_calibration_and_training():
    target = rows("evaluation_other_host", 300)
    with pytest.raises(ValueError, match="calibration"):
        analysis.calibrate(target, correct_probabilities(target), CONFIG)
    with pytest.raises(ValueError, match="Training"):
        analysis.fit_model(target, rows(), "fps_current", "dummy", CONFIG)


def test_oracle_metadata_and_labels_never_enter_observation_matrix():
    original = rows()
    changed = copy.deepcopy(original)
    for r in changed:
        r.update(label="forged", seed=-999, session_id="leak", requested_condition="leak")
        r["oracle"] = {"condition": "leak", "on_ms": 999999}
    for view in CONFIG["views"]:
        np.testing.assert_equal(
            analysis.observation_matrix(original, view), analysis.observation_matrix(changed, view)
        )


def test_preprocessing_fit_uses_training_only():
    train, cal = rows("training", 100), rows()
    extreme = copy.deepcopy(cal)
    for r in extreme:
        r["current"] = Features(decoded_fps=1e9)
    first, _ = analysis.fit_model(train, cal, "fps_current", "logistic_regression", CONFIG)
    second, _ = analysis.fit_model(train, extreme, "fps_current", "logistic_regression", CONFIG)
    np.testing.assert_equal(first[0].statistics_, second[0].statistics_)
    np.testing.assert_equal(first[1].mean_, [2.0])
    np.testing.assert_equal(first[-1].coef_, second[-1].coef_)


def test_zero_coverage_is_null_risk_and_confidence_ties_are_not_split():
    target = rows("evaluation", 300)
    probabilities = np.full((len(target), len(CONFIG["classes"])), 0.25)
    result = analysis.evaluate_records(
        target, probabilities, {"empirical_threshold": None, "bound_rule_threshold": None}, CONFIG
    )
    policy = result["policies"]["always_abstain"]
    assert policy["coverage"] == 0
    assert policy["selective_risk"] is None
    assert policy["errors"] == 0 and policy["abstained"] == len(target)
    assert len(result["empirical_risk_coverage"]) == 1
    assert result["empirical_risk_coverage"][0]["coverage"] == 1


def test_static_control_misclassification_counts_as_false_alarm():
    target = rows("evaluation", 300)
    probabilities = np.array([[0, 0, 0, 1]] * len(target))
    result = analysis.policy_metrics(target, probabilities, 0, CONFIG["classes"])
    assert result["false_fault_alarms_per_all_controls"] == 1
    assert result["by_design_stratum"]["normal_static"]["errors"] == 1


def test_window_selection_requires_full_fixed_coverage():
    windows = [
        FeatureWindow(
            run_id="x",
            session_id="x",
            window_start_ms=4000,
            window_end_ms=5000,
            features=Features(decoded_fps=0),
        )
    ]
    with pytest.raises(ValueError, match="Missing"):
        analysis.window_mean(windows, [4000, 6000])
    windows.append(
        FeatureWindow(
            run_id="x",
            session_id="x",
            window_start_ms=5000,
            window_end_ms=6000,
            features=Features(decoded_fps=20),
        )
    )
    assert analysis.window_mean(windows, [4000, 6000]).decoded_fps == 10


def test_partition_validation_rejects_duplicate_and_target_content_in_train():
    all_rows = rows("training", 100) + rows() + rows("evaluation", 300)
    analysis.validate_roles(all_rows, CONFIG["strata"])
    with pytest.raises(ValueError, match="twice"):
        analysis.validate_roles(all_rows + [all_rows[0]], CONFIG["strata"])
    all_rows[0]["seed"] = 300
    with pytest.raises(ValueError, match="Frozen roles"):
        analysis.validate_roles(all_rows, CONFIG["strata"])


def test_missing_reference_is_unknown_not_normal_or_proven_mislabel():
    manifest = {
        "session_id": "x",
        "condition": "source_freeze",
        "static_control": False,
        "execution_status": "failed",
    }
    row = oracle.label_policy_row(
        manifest, {"verification_status": "failed", "verified_condition": None}
    )
    assert row["reference_condition"] is None
    assert row["unsupported_if_request_always_used_as_label"]
    assert row["request_disagrees_with_verified_condition"] is None
    assert not row["eligible_for_supervised_scoring"]
