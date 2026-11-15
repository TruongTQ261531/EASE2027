"""Train on frozen source sessions; evaluate fresh same-version and cross-version calls."""

import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path

from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import confusion_matrix, f1_score, recall_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from ease_rtc.audit import audit
from ease_rtc.evaluate import CLASSES, clustered_f1_interval, rule_predictions
from ease_rtc.features import FEATURE_SETS, mean_features, model_matrix
from ease_rtc.io import read_json, read_jsonl, sha256, write_json
from ease_rtc.schema import FeatureWindow, OracleEvent, RunManifest


def dataset_records(dataset: Path):
    quality = audit(dataset)
    groups, labels, environments = defaultdict(list), {}, {}
    manifests = [
        RunManifest.model_validate(read_json(p))
        for p in sorted((dataset / "manifests").glob("*.json"))
    ]
    known = {m.run_id: m for m in manifests}
    for raw in read_jsonl(dataset / "features/windows.jsonl"):
        window = FeatureWindow.model_validate(raw)
        manifest = known[window.run_id]
        oracle = OracleEvent.model_validate(read_json(dataset / "oracle" / f"{window.run_id}.json"))
        if oracle.session_id != window.session_id or manifest.session_id != window.session_id:
            raise ValueError("Session identity mismatch")
        if oracle.verified_condition is None:
            continue
        labels[window.session_id] = oracle.verified_condition
        environments[window.session_id] = manifest.environment_id
        groups[window.session_id].append(window.features)
    rows = {s: mean_features(records) for s, records in groups.items()}
    return rows, labels, environments, quality, manifests


def evaluate_transfer(training: Path, fresh_source: Path, target: Path, output: Path):
    if output.exists():
        raise ValueError("Do not overwrite a previous transfer evaluation")
    original, source_labels, _, _, source_manifests = dataset_records(training)
    saved = read_json(training / "reports/splits.json")
    fingerprint = hashlib.sha256(
        json.dumps(
            {
                "features_sha256": sha256(training / "features/windows.jsonl"),
                "manifests": {
                    p.name: sha256(p) for p in sorted((training / "manifests").glob("*.json"))
                },
            },
            sort_keys=True,
        ).encode()
    ).hexdigest()
    if fingerprint != saved["dataset_sha256"]:
        raise ValueError("Training dataset no longer matches the frozen split")
    train_ids, validation_ids = saved["partitions"]["train"], saved["partitions"]["validation"]
    if set(train_ids) & set(validation_ids) or set(train_ids) & set(saved["partitions"]["test"]):
        raise ValueError("Source partition leakage")
    validation = [original[s] for s in validation_ids]
    y_validation = [source_labels[s] for s in validation_ids]
    candidates = [(c, f) for c in [0.1, 0.3, 0.5] for f in [8.0, 12.0, 16.0, 18.0]]
    thresholds = max(
        candidates,
        key=lambda t: f1_score(
            y_validation,
            rule_predictions(validation, *t),
            labels=CLASSES,
            average="macro",
            zero_division=0,
        ),
    )
    cohorts = {}
    prior_ids = set(original)
    for name, path in [("fresh_same_version", fresh_source), ("fresh_other_version", target)]:
        rows, labels, env, quality, manifests = dataset_records(path)
        if set(rows) & prior_ids:
            raise ValueError("A session appears in more than one cohort")
        prior_ids.update(rows)
        if set(labels.values()) != set(CLASSES):
            raise ValueError("Every evaluation cohort requires all three conditions")
        cohorts[name] = (rows, labels, env, quality, manifests)
    versions = {
        name: sorted({m.browser_version for m in data[4]}) for name, data in cohorts.items()
    }
    original_versions = sorted({m.browser_version for m in source_manifests})
    if versions["fresh_same_version"] != original_versions:
        raise ValueError("Same-version control does not match the source browser version")
    if set(versions["fresh_other_version"]) & set(original_versions):
        raise ValueError("Target browser version is not held out")
    results = []

    def score(name, model_name, feature_set, ids, labels, prediction):
        truth = [labels[s] for s in ids]
        results.append(
            {
                "cohort": name,
                "model": model_name,
                "feature_set": feature_set,
                "sessions": len(ids),
                "macro_f1": float(
                    f1_score(truth, prediction, labels=CLASSES, average="macro", zero_division=0)
                ),
                "balanced_accuracy": float(
                    recall_score(
                        truth, prediction, labels=CLASSES, average="macro", zero_division=0
                    )
                ),
                "session_bootstrap_95_interval": clustered_f1_interval(
                    truth, prediction, ids, 2027, 500
                ),
                "confusion_matrix": confusion_matrix(truth, prediction, labels=CLASSES).tolist(),
                "predictions": [
                    {"session_id": s, "condition": labels[s], "prediction": str(p)}
                    for s, p in zip(ids, prediction, strict=True)
                ],
            }
        )

    for name, (rows, labels, _, _, _) in cohorts.items():
        ids = sorted(rows)
        score(
            name,
            "rules",
            "telemetry_logs",
            ids,
            labels,
            rule_predictions([rows[s] for s in ids], *thresholds),
        )
    for feature_set, columns in FEATURE_SETS.items():
        x = model_matrix([original[s] for s in train_ids], columns)
        y = [source_labels[s] for s in train_ids]
        for name, estimator in [
            ("dummy", DummyClassifier(strategy="most_frequent")),
            (
                "logistic_regression",
                LogisticRegression(max_iter=2000, class_weight="balanced", random_state=2027),
            ),
            (
                "random_forest",
                RandomForestClassifier(
                    n_estimators=100,
                    max_depth=5,
                    class_weight="balanced",
                    random_state=2027,
                    n_jobs=2,
                ),
            ),
        ]:
            model = make_pipeline(
                SimpleImputer(strategy="median", add_indicator=True, keep_empty_features=True),
                StandardScaler(),
                estimator,
            )
            model.fit(x, y)
            for cohort, (rows, labels, _, _, _) in cohorts.items():
                ids = sorted(rows)
                prediction = model.predict(model_matrix([rows[s] for s in ids], columns))
                score(cohort, name, feature_set, ids, labels, prediction)
    report = {
        "scope": "Cross-Chromium-version feasibility, ONE host/OS; application conditions only",
        "training_dataset_sha256": fingerprint,
        "source_train_sessions": len(train_ids),
        "source_validation_sessions": len(validation_ids),
        "source_test_sessions_used_for_training_or_tuning": 0,
        "source_versions": original_versions,
        "evaluation_versions": versions,
        "rule_thresholds_source_validation_only": list(thresholds),
        "cohorts": {
            name: {
                "audit": data[3],
                "environment_ids": sorted(set(data[2].values())),
                "dataset_sha256": hashlib.sha256(
                    json.dumps(
                        {p.name: sha256(p) for p in sorted((path / "manifests").glob("*.json"))},
                        sort_keys=True,
                    ).encode()
                ).hexdigest(),
            }
            for name, path, data in [
                ("fresh_same_version", fresh_source, cohorts["fresh_same_version"]),
                ("fresh_other_version", target, cohorts["fresh_other_version"]),
            ]
        },
        "results": results,
        "class_order": CLASSES,
        "limitations": [
            "No tuning on target labels or source test sessions",
            "Small exploratory cohorts, not independent-machine replication",
            "Pre-existing easy source tasks and shared testbed oracle remain limited",
            "No network/compute fault diagnosis or causal-generalization claim",
        ],
    }
    write_json(output, report)
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--training", type=Path, required=True)
    parser.add_argument("--fresh-source", type=Path, required=True)
    parser.add_argument("--target", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = evaluate_transfer(args.training, args.fresh_source, args.target, args.output)
    print(result["scope"], len(result["results"]), "model/cohort evaluations")
