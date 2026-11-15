import argparse
import json
import random
from pathlib import Path

import yaml

from ease_rtc.audit import audit
from ease_rtc.collect import collect
from ease_rtc.features import build_features
from ease_rtc.io import write_json
from ease_rtc.schema import Scenario


def load_scenario(path: Path) -> Scenario:
    return Scenario.model_validate(yaml.safe_load(path.read_text()))


def pilot(config_path: Path, output: Path, repo: Path) -> dict:
    from ease_rtc.evaluate import evaluate

    config = yaml.safe_load(config_path.read_text())
    if output.exists() and any(output.iterdir()):
        raise ValueError(
            "Pilot output must be empty; preserve existing experiments in separate directories"
        )
    if config["target"] != "verified_application_condition":
        raise ValueError("This pilot does not establish root-cause labels")
    scenarios = [load_scenario(repo / p) for p in config["scenario_files"]]
    schedule = []
    for seed_offset in range(config["runs_per_condition"]):
        # Source seeds are balanced across conditions; ordering is randomized, not label-sorted.
        for scenario in scenarios:
            schedule.append(scenario.model_copy(update={"seed": scenario.seed + seed_offset}))
    random.Random(config["seed"]).shuffle(schedule)
    # Schedule and intervention metadata are not accessible to feature/model extraction.
    write_json(
        output / "protocol" / "schedule.json",
        {
            "experiment": config,
            "schedule": [s.model_dump() for s in schedule],
            "note": "Pilot protocol, not a final-study preregistration",
        },
    )
    for index, scenario in enumerate(schedule, 1):
        manifest = collect(scenario, output, repo)
        print(
            json.dumps(
                {
                    "run": index,
                    "total": len(schedule),
                    "run_id": manifest.run_id,
                    "condition": scenario.intervention,
                    "samples": manifest.sample_count,
                }
            ),
            flush=True,
        )
    audit(output)
    build_features(output, config["window_ms"])
    return evaluate(output, config["seed"], config["bootstrap_repetitions"])


def main():
    parser = argparse.ArgumentParser(description="EASE WebRTC feasibility artifact")
    sub = parser.add_subparsers(dest="command", required=True)
    collect_parser = sub.add_parser("collect", help="Record real local WebRTC calls")
    collect_parser.add_argument("--config", type=Path, required=True)
    collect_parser.add_argument("--output", type=Path, required=True)
    collect_parser.add_argument("--runs", type=int, default=1)
    pilot_parser = sub.add_parser(
        "pilot", help="Collect, audit, featurize and evaluate a new pilot"
    )
    pilot_parser.add_argument("--config", type=Path, default=Path("configs/experiments/pilot.yaml"))
    pilot_parser.add_argument("--output", type=Path, required=True)
    for name in ["audit", "features", "evaluate"]:
        command = sub.add_parser(name)
        command.add_argument("--dataset", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "collect":
        if args.runs < 1:
            parser.error("--runs must be positive")
        scenario = load_scenario(args.config)
        for offset in range(args.runs):
            manifest = collect(
                scenario.model_copy(update={"seed": scenario.seed + offset}),
                args.output,
                Path.cwd(),
            )
            print(
                json.dumps({"run_id": manifest.run_id, "samples": manifest.sample_count}),
                flush=True,
            )
    elif args.command == "pilot":
        result = pilot(args.config, args.output, Path.cwd())
        print(
            json.dumps(
                {
                    "report": str(args.output / "reports" / "report.md"),
                    "splits": result["split_counts"],
                }
            )
        )
    elif args.command == "audit":
        print(json.dumps(audit(args.dataset), indent=2))
    elif args.command == "features":
        print(json.dumps({"windows": len(build_features(args.dataset))}))
    elif args.command == "evaluate":
        from ease_rtc.evaluate import evaluate

        result = evaluate(args.dataset)
        print(json.dumps({"splits": result["split_counts"], "models": len(result["results"])}))
