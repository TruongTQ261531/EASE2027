"""Session-level pilot evaluation. Test scores are descriptive, never model-selection inputs."""

import hashlib
import json
from collections import defaultdict
from pathlib import Path

import numpy as np
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix, f1_score, recall_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from ease_rtc.audit import audit
from ease_rtc.features import FEATURE_SETS, mean_features, model_matrix
from ease_rtc.io import read_json, read_jsonl, sha256, write_json
from ease_rtc.schema import FeatureWindow, OracleEvent

CLASSES = ["capture_pause", "connection_close", "normal"]


def split_sessions(labels: dict[str, str], seed: int) -> dict[str, list[str]]:
    grouped = defaultdict(list)
    for session, label in sorted(labels.items()):
        grouped[label].append(session)
    if set(grouped) != set(CLASSES):
        raise ValueError("Pilot evaluation requires all three verified application conditions")
    rng = np.random.default_rng(seed)
    splits = {"train": [], "validation": [], "test": []}
    for label, sessions in sorted(grouped.items()):
        if len(sessions) < 5:
            raise ValueError(
                f"Need at least 5 verified sessions for {label}; found {len(sessions)}"
            )
        shuffled = list(rng.permutation(sessions))
        holdout = max(1, int(len(sessions) * 0.2))
        splits["test"].extend(shuffled[:holdout])
        splits["validation"].extend(shuffled[holdout : holdout * 2])
        splits["train"].extend(shuffled[holdout * 2 :])
    validate_split(splits, set(labels))
    return splits


def validate_split(splits: dict, sessions: set[str]) -> None:
    if set(splits) != {"train", "validation", "test"}:
        raise ValueError("Expected train, validation and test partitions")
    all_ids = [s for partition in splits.values() for s in partition]
    if len(all_ids) != len(set(all_ids)) or set(all_ids) != sessions:
        raise ValueError("Session split overlaps or does not cover the eligible dataset")
    if any(not partition for partition in splits.values()):
        raise ValueError("Empty partition")


def clustered_f1_interval(y, prediction, sessions, seed: int, repetitions: int) -> list[float]:
    """Resample independent sessions, retaining all their rows together."""
    y, prediction, sessions = np.asarray(y), np.asarray(prediction), np.asarray(sessions)
    if repetitions < 1 or len(y) == 0 or len(y) != len(sessions) or len(y) != len(prediction):
        raise ValueError("Bootstrap requires nonempty aligned inputs and positive repetitions")
    groups = np.unique(sessions)
    rng, scores = np.random.default_rng(seed), []
    for _ in range(repetitions):
        chosen = rng.choice(groups, size=len(groups), replace=True)
        idx = np.concatenate([np.flatnonzero(sessions == group) for group in chosen])
        scores.append(
            f1_score(y[idx], prediction[idx], labels=CLASSES, average="macro", zero_division=0)
        )
    return [float(v) for v in np.quantile(scores, [0.025, 0.975])]


def calibration(y, probabilities: np.ndarray) -> dict:
    targets = np.array([[float(label == c) for c in CLASSES] for label in y])
    confidence = probabilities.max(axis=1)
    prediction = np.array(CLASSES)[probabilities.argmax(axis=1)]
    correct = prediction == np.asarray(y)
    bins, ece = np.minimum((confidence * 5).astype(int), 4), 0.0
    for index in range(5):
        mask = bins == index
        if mask.any():
            ece += float(mask.mean() * abs(correct[mask].mean() - confidence[mask].mean()))
    curve = []
    for threshold in [0.0, 0.5, 0.7, 0.9]:
        accepted = confidence >= threshold
        curve.append(
            {
                "threshold": threshold,
                "coverage": float(accepted.mean()),
                "risk": float(1 - correct[accepted].mean()) if accepted.any() else None,
            }
        )
    return {
        "multiclass_brier_sum": float(np.mean(np.sum((probabilities - targets) ** 2, axis=1))),
        "ece_5_bins": ece,
        "risk_coverage": curve,
    }


def rule_predictions(records, closed_threshold: float, fps_threshold: float) -> np.ndarray:
    # No scenario identifiers, event clocks or source fingerprints are available here.
    result = []
    for row in records:
        if row.closed_fraction is not None and row.closed_fraction > closed_threshold:
            result.append("connection_close")
        elif row.decoded_fps is not None and row.decoded_fps < fps_threshold:
            result.append("capture_pause")
        else:
            result.append("normal")
    return np.array(result)


def evaluate(dataset: Path, seed: int = 2027, bootstrap_repetitions: int = 500) -> dict:
    quality = audit(dataset)
    windows_path = dataset / "features" / "windows.jsonl"
    windows = [FeatureWindow.model_validate(w) for w in read_jsonl(windows_path)]
    grouped, labels, session_runs = defaultdict(list), {}, {}
    excluded = defaultdict(int)
    for window in windows:
        oracle = OracleEvent.model_validate(read_json(dataset / "oracle" / f"{window.run_id}.json"))
        if window.session_id != oracle.session_id:
            raise ValueError("Feature/oracle session mismatch")
        if oracle.verification_status != "verified":
            excluded[oracle.verification_status] += 1
            continue
        if window.session_id in session_runs and session_runs[window.session_id] != window.run_id:
            raise ValueError("Multiple runs per session require an explicit aggregation policy")
        session_runs[window.session_id] = window.run_id
        labels[window.session_id] = oracle.verified_condition
        grouped[window.session_id].append(window.features)
    records = {s: mean_features(rows) for s, rows in grouped.items()}
    fingerprint = hashlib.sha256(
        json.dumps(
            {
                "features_sha256": sha256(windows_path),
                "manifests": {
                    p.name: sha256(p) for p in sorted((dataset / "manifests").glob("*.json"))
                },
            },
            sort_keys=True,
        ).encode()
    ).hexdigest()
    split_file = dataset / "reports" / "splits.json"
    if split_file.exists():
        saved = read_json(split_file)
        if saved["dataset_sha256"] != fingerprint or saved["seed"] != seed:
            raise ValueError(
                "Frozen split differs from current dataset/seed; use a new output directory"
            )
        splits = saved["partitions"]
        validate_split(splits, set(labels))
    else:
        splits = split_sessions(labels, seed)
        write_json(split_file, {"seed": seed, "dataset_sha256": fingerprint, "partitions": splits})
    y = {key: np.array([labels[s] for s in ids]) for key, ids in splits.items()}
    split_records = {key: [records[s] for s in ids] for key, ids in splits.items()}
    all_results = []

    def record(name, feature_set, predictions, probabilities, settings):
        result = {
            "model": name,
            "feature_set": feature_set,
            "settings": settings,
            "macro_f1": float(
                f1_score(y["test"], predictions, labels=CLASSES, average="macro", zero_division=0)
            ),
            "balanced_accuracy": float(
                recall_score(
                    y["test"], predictions, labels=CLASSES, average="macro", zero_division=0
                )
            ),
            "macro_f1_session_bootstrap_95_interval": clustered_f1_interval(
                y["test"], predictions, splits["test"], seed, bootstrap_repetitions
            ),
            "confusion_matrix": confusion_matrix(y["test"], predictions, labels=CLASSES).tolist(),
            "per_class": classification_report(
                y["test"], predictions, labels=CLASSES, output_dict=True, zero_division=0
            ),
            **calibration(y["test"], probabilities),
            "predictions": [
                {
                    "session_id": sid,
                    "observed_condition": labels[sid],
                    "prediction": str(pred),
                    "probabilities": prob.tolist(),
                }
                for sid, pred, prob in zip(splits["test"], predictions, probabilities, strict=True)
            ],
        }
        all_results.append(result)

    # Thresholds selected using validation sessions only; test data remain untouched.
    candidates = [(closed, fps) for closed in [0.1, 0.3, 0.5] for fps in [8.0, 12.0, 16.0, 18.0]]

    def validation_score(params):
        return f1_score(
            y["validation"],
            rule_predictions(split_records["validation"], *params),
            labels=CLASSES,
            average="macro",
            zero_division=0,
        )

    thresholds = max(candidates, key=validation_score)
    prediction = rule_predictions(split_records["test"], *thresholds)
    probability = np.array([[float(p == c) for c in CLASSES] for p in prediction])
    record(
        "rules",
        "telemetry_logs",
        prediction,
        probability,
        {
            "closed_threshold": thresholds[0],
            "fps_threshold": thresholds[1],
            "probabilities": "hard decisions; not calibrated",
        },
    )
    for feature_set, columns in FEATURE_SETS.items():
        matrices = {key: model_matrix(rows, columns) for key, rows in split_records.items()}
        models = {
            "dummy": DummyClassifier(strategy="most_frequent"),
            "logistic_regression": LogisticRegression(
                max_iter=2000, class_weight="balanced", random_state=seed
            ),
            "random_forest": RandomForestClassifier(
                n_estimators=100, max_depth=5, class_weight="balanced", n_jobs=2, random_state=seed
            ),
        }
        for name, model in models.items():
            pipeline = make_pipeline(
                SimpleImputer(strategy="median", add_indicator=True, keep_empty_features=True),
                StandardScaler(),
                model,
            )
            pipeline.fit(matrices["train"], y["train"])
            prediction = pipeline.predict(matrices["test"])
            raw_probability = pipeline.predict_proba(matrices["test"])
            probability = raw_probability[:, [list(pipeline.classes_).index(c) for c in CLASSES]]
            record(name, feature_set, prediction, probability, {"columns": columns, "seed": seed})
    report = {
        "scope": (
            "FEASIBILITY ONLY: synthetic application conditions, one host/browser; not RCA accuracy"
        ),
        "target": "verified_application_condition",
        "seed": seed,
        "dataset_sha256": fingerprint,
        "class_order": CLASSES,
        "audit": quality,
        "unit_of_analysis": (
            "One aggregate per independent browser-call session, all recording windows"
        ),
        "split_counts": {key: len(ids) for key, ids in splits.items()},
        "excluded_windows_by_status": dict(excluded),
        "failed_runs": quality["failed"],
        "bootstrap_repetitions": bootstrap_repetitions,
        "uncertainty_limit": (
            "Tiny pilot; session bootstrap is not cross-environment uncertainty or power analysis"
        ),
        "model_selection": "Predefined models/ablations; only rule thresholds tuned on validation",
        "results": all_results,
    }
    write_json(dataset / "reports" / "metrics.json", report)
    lines = [
        "# Pilot report — feasibility only",
        "",
        report["scope"],
        "",
        f"Sessions: {report['split_counts']}. Target: verified application condition.",
        "",
        "| Model | Inputs | Macro-F1 | Balanced accuracy |",
        "|---|---|---:|---:|",
    ]
    for r in all_results:
        lines.append(
            f"| {r['model']} | {r['feature_set']} | {r['macro_f1']:.3f} | "
            f"{r['balanced_accuracy']:.3f} |"
        )
    lines += [
        "",
        "These scores validate plumbing only. No novelty, causal, external-validity,",
        "multimodal benefit or conference-readiness claim follows from this pilot.",
        "",
    ]
    (dataset / "reports" / "report.md").write_text("\n".join(lines), encoding="utf-8")
    return report
