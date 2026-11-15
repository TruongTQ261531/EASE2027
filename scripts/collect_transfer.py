"""Collect randomized cross-version calls; no changes to shared host networking."""

import argparse
import os
import random
from pathlib import Path

from ease_rtc.audit import audit
from ease_rtc.collect import collect
from ease_rtc.features import build_features
from ease_rtc.io import write_json
from ease_rtc.schema import Scenario

parser = argparse.ArgumentParser()
parser.add_argument("--source-browser", type=Path, required=True)
parser.add_argument("--target-browser", type=Path, required=True)
parser.add_argument("--output", type=Path, required=True)
parser.add_argument("--runs-per-condition", type=int, default=5)
args = parser.parse_args()
if args.runs_per_condition < 1:
    parser.error("--runs-per-condition must be positive")
if args.source_browser.resolve() == args.target_browser.resolve():
    parser.error("Browser executable paths must differ")
if args.output.exists() and any(args.output.iterdir()):
    parser.error("Use an empty output directory")
schedule = [
    (engine, condition, seed)
    for seed in range(1042, 1042 + args.runs_per_condition)
    for condition in ["normal", "capture_pause", "connection_close"]
    for engine in ["source", "target"]
]
random.Random(20271115).shuffle(schedule)
write_json(
    args.output / "protocol.json",
    {
        "scope": "Cross-version on one host only, not causal multi-environment generalization",
        "source_executable": str(args.source_browser),
        "target_executable": str(args.target_browser),
        "order_seed": 20271115,
        "schedule": schedule,
        "models": [
            "source-validation rules",
            "most_frequent",
            "logistic_regression",
            "random_forest",
        ],
        "training": "Existing pilot-v0.1 frozen train sessions only; no target tuning",
    },
)
prior = os.environ.get("EASE_CHROMIUM_EXECUTABLE")
try:
    for index, (engine, condition, seed) in enumerate(schedule, 1):
        browser = args.source_browser if engine == "source" else args.target_browser
        os.environ["EASE_CHROMIUM_EXECUTABLE"] = str(browser.resolve())
        manifest = collect(
            Scenario(name=condition, intervention=condition, seed=seed),
            args.output / engine,
            Path.cwd(),
        )
        print(
            index,
            len(schedule),
            engine,
            condition,
            manifest.browser_version,
            manifest.run_id,
            flush=True,
        )
finally:
    if prior is None:
        os.environ.pop("EASE_CHROMIUM_EXECUTABLE", None)
    else:
        os.environ["EASE_CHROMIUM_EXECUTABLE"] = prior
for engine in ["source", "target"]:
    print(engine, audit(args.output / engine))
    build_features(args.output / engine)
