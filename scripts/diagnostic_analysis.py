"""Retrospective, CPU-only diagnostic analysis; never modify the frozen collector/datasets."""

import argparse
import hashlib
import json
import math
import resource
import subprocess
import time
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from scipy.stats import beta
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import confusion_matrix, f1_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from ease_rtc.features import mean_features, model_matrix
from ease_rtc.io import read_json, read_jsonl, sha256, write_json
from ease_rtc.live_audit import audit_live, inventory
from ease_rtc.schema import Features, FeatureWindow

ROOT = Path(__file__).resolve().parents[1]
COLUMNS = list(Features.model_fields)
LOCK = ROOT / "configs/analysis/directions_v1.lock.json"
LOCKED_FILES = [
    "configs/analysis/directions_v1.json",
    "scripts/diagnostic_analysis.py",
    "scripts/oracle_validity_audit.py",
    "uv.lock",
]


def input_digest(path):
    return hashlib.sha256(json.dumps(inventory(path), sort_keys=True).encode()).hexdigest()


def check_analysis_lock():
    saved = read_json(LOCK)
    for filename in LOCKED_FILES:
        if saved["files_sha256"][filename] != sha256(ROOT / filename):
            raise ValueError("Analysis changed after freeze; create an explicit new version")


def verified_dataset(spec):
    path = ROOT / spec["path"]
    if input_digest(path) != spec["inventory_sha256"]:
        raise ValueError("Input differs from the analysis plan; never silently replace data")
    return path, audit_live(path)


def window_mean(windows, interval):
    start, end = interval
    selected = [w for w in windows if start <= w.window_start_ms and w.window_end_ms <= end]
    expected = set(range(start, end, 1000))
    if {w.window_start_ms for w in selected} != expected or len(selected) != len(expected):
        raise ValueError("Missing/duplicate fixed observation windows; do not impute an absent run")
    return mean_features([w.features for w in selected])


def load_records(config):
    records, audits = [], {}
    for spec in config["datasets"]:
        if spec["a_role"] is None:
            continue
        root, quality = verified_dataset(spec)
        audits[spec["path"]] = quality
        for path in sorted((root / "manifests").glob("*.json")):
            m = read_json(path)
            verdict = read_json(root / "oracle" / m["run_id"] / "verdict.json")
            if verdict["verification_status"] != "verified":
                continue  # Counts including every failure remain in audits.
            label = verdict["verified_condition"]
            if label not in config["classes"]:
                raise ValueError("Unsupported verified target")
            if spec["a_role"] == "target" and m["seed"] != 300:
                raise ValueError("Target cohort must remain evaluation-only")
            role = (
                "evaluation_other_host"
                if spec["a_role"] == "target"
                else config["seed_roles"][str(m["seed"])]
            )
            windows = [
                FeatureWindow.model_validate(w)
                for w in read_jsonl(root / "features" / f"{m['run_id']}.jsonl")
            ]
            if any(w.session_id != m["session_id"] for w in windows):
                raise ValueError("Features belong to a different session")
            stratum = (
                ("normal_static" if m["static_control"] else "normal_moving")
                if label == "normal"
                else label
            )
            records.append(
                {
                    "session_id": m["session_id"],
                    "cohort": spec["path"],
                    "role": role,
                    "seed": m["seed"],
                    "label": label,
                    "stratum": stratum,
                    "current": window_mean(windows, config["current_window_ms"]),
                    "history": window_mean(windows, config["history_window_ms"]),
                }
            )
    validate_roles(records, config["strata"])
    return records, audits


def validate_roles(records, strata):
    ids = [r["session_id"] for r in records]
    if len(ids) != len(set(ids)):
        raise ValueError("A session cannot appear twice or cross partitions")
    expected = {
        "training": 100,
        "calibration": 200,
        "evaluation": 300,
        "evaluation_other_host": 300,
    }
    for r in records:
        if r["role"] not in expected or r["seed"] != expected[r["role"]]:
            raise ValueError("Frozen roles changed; target content must not enter development")
    for role in ["training", "calibration", "evaluation"]:
        observed = [r["stratum"] for r in records if r["role"] == role]
        if Counter(observed) != Counter(strata):
            raise ValueError("This feasibility protocol requires one session per source stratum")


def observation_matrix(records, view):
    # Only typed receiver measurements are accessible to this transformation.
    current = [r["current"] for r in records]
    if view == "fps_current":
        return model_matrix(current, ["decoded_fps"])
    if view == "receiver_current":
        return model_matrix(current, COLUMNS)
    if view == "receiver_history":
        history = [r["history"] for r in records]
        return np.hstack([model_matrix(current, COLUMNS), model_matrix(history, COLUMNS)])
    raise ValueError("Unknown observation view")


def risk_upper(errors, accepted, alpha):
    """One-sided exact binomial bound, conditional on an i.i.d. accepted sample."""
    if not isinstance(errors, int) or not isinstance(accepted, int):
        raise ValueError("Binomial counts must be integers")
    if not 0 <= errors <= accepted or not 0 < alpha < 1:
        raise ValueError("Invalid binomial inputs")
    if accepted == 0 or errors == accepted:
        return 1.0
    return float(beta.ppf(1 - alpha, errors + 1, accepted - errors))


def minimum_zero_error_count(risk, alpha):
    if not 0 < risk < 1 or not 0 < alpha < 1:
        raise ValueError("Risk/alpha must lie strictly between zero and one")
    return math.ceil(math.log(alpha) / math.log1p(-risk))


def calibrate(records, probabilities, config):
    """Receives calibration only, never target data; fixed candidates, no model refitting."""
    if not records or any(r["role"] != "calibration" for r in records):
        raise ValueError("Policy selection must use only the frozen calibration partition")
    labels = np.array(config["classes"])
    predicted = labels[probabilities.argmax(axis=1)]
    confidence = probabilities.max(axis=1)
    truth = np.array([r["label"] for r in records])
    strata = np.array([r["stratum"] for r in records])
    multiplicity = (
        len(config["models"])
        * len(config["views"])
        * len(config["thresholds"])
        * len(config["strata"])
    )
    alpha = config["familywise_alpha"] / multiplicity
    candidates = []
    for threshold in config["thresholds"]:
        accepted = confidence >= threshold
        by_stratum = {}
        for name in config["strata"]:
            selected = accepted & (strata == name)
            n = int(selected.sum())
            k = int(((predicted != truth) & selected).sum())
            by_stratum[name] = {"accepted": n, "errors": k, "upper_bound": risk_upper(k, n, alpha)}
        n = int(accepted.sum())
        k = int(((predicted != truth) & accepted).sum())
        candidates.append(
            {
                "threshold": threshold,
                "accepted": n,
                "errors": k,
                "coverage": n / len(records),
                "empirical_risk": k / n if n else None,
                "max_stratum_upper_bound": max(r["upper_bound"] for r in by_stratum.values()),
                "strata": by_stratum,
            }
        )

    def choose(key):
        eligible = [c for c in candidates if c["accepted"] > 0 and c[key] <= config["risk_target"]]
        return max(eligible, key=lambda c: (c["coverage"], -c["threshold"])) if eligible else None

    empirical, bounded = choose("empirical_risk"), choose("max_stratum_upper_bound")
    return {
        "candidate_count_including_strata": multiplicity,
        "alpha_per_bound": alpha,
        "candidates": candidates,
        "empirical_threshold": empirical["threshold"] if empirical else None,
        "bound_rule_threshold": bounded["threshold"] if bounded else None,
        "deployment_risk_certified": False,
        "qualification": (
            "Illustrative bounds only: old pilot data, one calibration seed, "
            "untested sampling assumptions"
        ),
    }


def fit_model(training, calibration, view, name, config):
    # Evaluation records are deliberately not an argument.
    if any(r["role"] != "training" for r in training):
        raise ValueError("Training must not include calibration or evaluation records")
    settings = config["model_settings"]
    models = {
        "dummy": DummyClassifier(strategy="most_frequent"),
        "logistic_regression": LogisticRegression(
            C=settings["lr_C"],
            max_iter=settings["lr_max_iter"],
            class_weight="balanced",
            random_state=settings["random_seed"],
        ),
        "random_forest": RandomForestClassifier(
            n_estimators=settings["rf_n_estimators"],
            max_depth=settings["rf_max_depth"],
            class_weight="balanced",
            random_state=settings["random_seed"],
            n_jobs=settings["n_jobs"],
        ),
    }
    pipeline = make_pipeline(
        SimpleImputer(strategy="median", add_indicator=True, keep_empty_features=True),
        StandardScaler(),
        models[name],
    )
    pipeline.fit(observation_matrix(training, view), [r["label"] for r in training])
    probabilities = predict(pipeline, calibration, view, config["classes"])
    return pipeline, calibrate(calibration, probabilities, config)


def predict(pipeline, records, view, classes):
    raw = pipeline.predict_proba(observation_matrix(records, view))
    return raw[:, [list(pipeline.classes_).index(c) for c in classes]]


def policy_metrics(records, probabilities, threshold, classes):
    predicted = np.array(classes)[probabilities.argmax(axis=1)]
    truth = np.array([r["label"] for r in records])
    accepted = (
        probabilities.max(axis=1) >= threshold
        if threshold is not None
        else np.zeros(len(records), dtype=bool)
    )
    errors = predicted != truth

    def summarize(mask):
        n, a = int(mask.sum()), int((mask & accepted).sum())
        e = int((mask & accepted & errors).sum())
        return {
            "sessions": n,
            "accepted": a,
            "abstained": n - a,
            "errors": e,
            "coverage": a / n if n else None,
            "selective_risk": e / a if a else None,
        }

    controls = truth == "normal"
    strata = np.array([r["stratum"] for r in records])
    return {
        **summarize(np.ones(len(records), dtype=bool)),
        "by_true_class": {name: summarize(truth == name) for name in classes},
        "by_design_stratum": {name: summarize(strata == name) for name in sorted(set(strata))},
        "false_fault_alarms_per_all_controls": (
            float((accepted & controls & (predicted != "normal")).sum() / controls.sum())
            if controls.any()
            else None
        ),
        "decisions": [
            {
                "session_id": r["session_id"],
                "reference_condition": r["label"],
                "prediction": str(p),
                "accepted": bool(a),
            }
            for r, p, a in zip(records, predicted, accepted, strict=True)
        ],
    }


def evaluate_records(records, probabilities, selection, config):
    classes = config["classes"]
    truth = np.array([r["label"] for r in records])
    predictions = np.array(classes)[probabilities.argmax(axis=1)]
    present = [c for c in classes if c in truth]
    targets = np.array([[float(y == c) for c in classes] for y in truth])
    # Entire equal-confidence groups enter together, avoiding label-dependent tie breaking.
    curve = []
    for threshold in sorted(set(probabilities.max(axis=1)), reverse=True):
        result = policy_metrics(records, probabilities, threshold, classes)
        curve.append({k: result[k] for k in ["accepted", "errors", "coverage", "selective_risk"]})
    return {
        "sessions": len(records),
        "present_classes": present,
        "forced_accuracy": float((truth == predictions).mean()),
        "macro_f1_present_classes": float(
            f1_score(truth, predictions, labels=present, average="macro", zero_division=0)
        ),
        "confusion_matrix_class_order": classes,
        "confusion_matrix": confusion_matrix(truth, predictions, labels=classes).tolist(),
        "multiclass_brier_sum": float(np.mean(np.sum((probabilities - targets) ** 2, axis=1))),
        "empirical_risk_coverage": curve,
        "policies": {
            name: policy_metrics(records, probabilities, threshold, classes)
            for name, threshold in {
                "always_predict": 0.0,
                "always_abstain": None,
                "calibration_empirical": selection["empirical_threshold"],
                "calibration_bound_rule": selection["bound_rule_threshold"],
            }.items()
        },
        "probabilities": [
            {"session_id": r["session_id"], "values": p.tolist()}
            for r, p in zip(records, probabilities, strict=True)
        ],
    }


def collisions(records, config):
    buckets = defaultdict(list)
    for r in records:
        fps = r["current"].decoded_fps
        bucket = (
            "missing"
            if fps is None
            else str(sum(fps >= x for x in config["collision_fps_bucket_edges"]))
        )
        buckets[bucket].append(r)
    result = []
    for bucket, rows in sorted(buckets.items()):
        counts = Counter(r["label"] for r in rows)
        result.append(
            {
                "bucket": bucket,
                "sessions": len(rows),
                "condition_counts": dict(sorted(counts.items())),
                "minimum_empirical_errors_for_one_label_per_bucket": len(rows)
                - max(counts.values()),
                "members": [
                    {
                        "session_id": r["session_id"],
                        "role": r["role"],
                        "stratum": r["stratum"],
                        "fps": r["current"].decoded_fps,
                    }
                    for r in rows
                ],
            }
        )
    return {
        "scope": config["collision_claim"],
        "fps_edges": config["collision_fps_bucket_edges"],
        "buckets": result,
        "not_a_population_error_bound": True,
    }


def run(config):
    records, audits = load_records(config)
    train = [r for r in records if r["role"] == "training"]
    calibration = [r for r in records if r["role"] == "calibration"]
    fitted = []
    # Freeze every policy using training/calibration before evaluating either cohort.
    for view in config["views"]:
        for name in config["models"]:
            pipeline, selected = fit_model(train, calibration, view, name, config)
            fitted.append((view, name, pipeline, selected))
    results = []
    for view, name, pipeline, selected in fitted:
        cohorts = {}
        for role in ["evaluation", "evaluation_other_host"]:
            target = [r for r in records if r["role"] == role]
            cohorts[role] = evaluate_records(
                target, predict(pipeline, target, view, config["classes"]), selected, config
            )
        results.append(
            {"view": view, "model": name, "calibration": selected, "evaluation": cohorts}
        )
    multiplicity = (
        len(config["models"])
        * len(config["views"])
        * len(config["thresholds"])
        * len(config["strata"])
    )
    return {
        "scope": config["scope"],
        "causal_attribution": "unestablished",
        "roles": dict(sorted(Counter(r["role"] for r in records).items())),
        "audits": audits,
        "class_order": config["classes"],
        "diagnostic_target": "bounded verified condition, not causal root cause or QoE",
        "observation_columns": COLUMNS,
        "request_conditioned_oracle": True,
        "deployment_risk_certified": False,
        "collision_analysis": collisions(records, config),
        "zero_error_calibration_planning": [
            {
                "risk_target": risk,
                "fixed_policy_accepted_minimum": minimum_zero_error_count(
                    risk, config["familywise_alpha"]
                ),
                "family_checks": multiplicity,
                "family_corrected_minimum_per_stratum": minimum_zero_error_count(
                    risk, config["familywise_alpha"] / multiplicity
                ),
            }
            for risk in [0.05, 0.1, 0.2]
        ],
        "results": results,
        "limitations": [
            "Previously inspected data: retrospective feasibility only",
            "One content seed each for training and calibration; five sessions each",
            "Same engine/userland; network absent in target host; host effect not isolated",
            "Window timing is fixed/offline; no online detection or latency validation",
            "No population identifiability, calibration or cross-distribution risk guarantee",
            "Present-class macro-F1 on different class supports is not a paired transfer estimate",
            "Oracle checks are request-conditioned, not independent causal truth",
        ],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=ROOT / "configs/analysis/directions_v1.json")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.config.resolve() != ROOT / "configs/analysis/directions_v1.json":
        raise ValueError("Use the frozen config for this analysis version")
    check_analysis_lock()
    args.output.mkdir(parents=True, exist_ok=False)
    started = time.perf_counter()
    report = run(read_json(args.config))
    report["provenance"] = {
        "config_sha256": sha256(args.config),
        "analysis_lock_sha256": sha256(LOCK),
        "collector_lock_sha256": sha256(ROOT / "lab/frozen_plan_v1.json"),
        "code_commit": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
    }
    write_json(args.output / "diagnostic_results.json", report)
    write_json(
        args.output / "runtime.json",
        {
            "wall_seconds_analysis_after_imports": time.perf_counter() - started,
            "process_peak_rss_mib_including_imports_linux": resource.getrusage(
                resource.RUSAGE_SELF
            ).ru_maxrss
            / 1024,
            "GPU_used": False,
            "model_fit_count": len(report["results"]),
            "model_threads": 1,
            "scope": "Analysis process only, not browser collection or machine total",
        },
    )
    print(
        json.dumps(
            {
                "roles": report["roles"],
                "models_and_views": len(report["results"]),
                "deployment_risk_certified": False,
            }
        )
    )


if __name__ == "__main__":
    main()
