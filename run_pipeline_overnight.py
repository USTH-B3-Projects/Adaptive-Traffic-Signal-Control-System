"""Run baselines, multi-scenario PPO training, evaluation, and aggregation."""
import argparse
import csv
import json
import logging
import math
import os
from pathlib import Path
import statistics
import subprocess
import sys
import time


ROOT = Path(__file__).resolve().parent
SCENARIOS = ("low", "medium", "high", "imbalance")
SEED = 107
TIMESTEPS = 800_000
METRICS = (
    "queue_length",
    "waiting_time",
    "average_speed",
    "arrived_count",
    "vehicles_in_network",
    "total_travel_time",
    "average_delay_per_vehicle",
    "throughput",
)


def configure_logging(path: Path) -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[logging.FileHandler(path, encoding="utf-8"), logging.StreamHandler()],
    )


def run_command(command: list[str], timings: dict, key: str) -> bool:
    start = time.perf_counter()
    logging.info("START %s: %s", key, " ".join(command))
    try:
        with (ROOT / "overnight_subprocess.log").open("a", encoding="utf-8") as output:
            completed = subprocess.run(
                command,
                cwd=ROOT,
                env=os.environ.copy(),
                stdout=output,
                stderr=subprocess.STDOUT,
                check=False,
            )
        timings[key] = time.perf_counter() - start
        if completed.returncode:
            logging.error("FAIL %s: exit code %s", key, completed.returncode)
            return False
        logging.info("DONE %s in %.2fs", key, timings[key])
        return True
    except Exception:
        timings[key] = time.perf_counter() - start
        logging.exception("EXCEPTION %s", key)
        return False


def read_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as file:
        return [json.loads(line) for line in file if line.strip()]


def aggregate_records(records: list[dict], method: str, scenario: str, runtime: float) -> dict:
    rows = []
    for record in records:
        queue = sum(record["queues"].values())
        rows.append(
            {
                "queue_length": queue,
                "waiting_time": float(record["total_waiting_time"]),
                "average_speed": float(record.get("average_speed", 0.0)),
                "arrived_count": float(record.get("arrived_count", 0)),
                "vehicles_in_network": float(record.get("vehicles_in_network", 0)),
                "simulation_time": float(record["simulation_time"]),
            }
        )
    duration = max(rows[-1]["simulation_time"], 0.1)
    travel_time = sum(
        (current["simulation_time"] - previous["simulation_time"]) * current["vehicles_in_network"]
        for previous, current in zip(rows, rows[1:])
    )
    arrived = rows[-1]["arrived_count"]
    waiting = sum(row["waiting_time"] for row in rows) / len(rows)
    return {
        "method": method,
        "scenario": scenario,
        "queue_length": statistics.fmean(row["queue_length"] for row in rows),
        "waiting_time": waiting,
        "average_speed": statistics.fmean(row["average_speed"] for row in rows),
        "arrived_count": arrived,
        "vehicles_in_network": statistics.fmean(row["vehicles_in_network"] for row in rows),
        "total_travel_time": travel_time,
        "average_delay_per_vehicle": waiting / arrived if arrived else 0.0,
        "throughput": arrived / duration * 3600.0,
        "execution_seconds": runtime,
    }


def read_drl_rows(path: Path, runtime: float) -> list[dict]:
    grouped = {scenario: [] for scenario in SCENARIOS}
    with path.open(newline="", encoding="utf-8") as file:
        for row in csv.DictReader(file):
            grouped[row["scenario"]].append(row)
    output = []
    for scenario, rows in grouped.items():
        if not rows:
            raise RuntimeError(f"DRL evaluation has no rows for {scenario}")
        values = {metric: [float(row[metric]) for row in rows] for metric in (
            "queue_length", "waiting_time", "average_speed",
            "arrived_count", "vehicles_in_network",
        )}
        duration = max(float(rows[-1]["simulation_time"]), 0.1)
        travel_time = sum(
            (float(current["simulation_time"]) - float(previous["simulation_time"]))
            * float(current["vehicles_in_network"])
            for previous, current in zip(rows, rows[1:])
        )
        arrived = values["arrived_count"][-1]
        waiting = statistics.fmean(values["waiting_time"])
        output.append(
            {
                "method": "drl_ppo",
                "scenario": scenario,
                **{metric: statistics.fmean(values[metric]) for metric in values},
                "total_travel_time": travel_time,
                "average_delay_per_vehicle": waiting / arrived if arrived else 0.0,
                "throughput": arrived / duration * 3600.0,
                "execution_seconds": runtime,
            }
        )
    return output


def write_summary(rows: list[dict], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=("method", "scenario", *METRICS, "execution_seconds"))
        writer.writeheader()
        writer.writerows(rows)


def plot_summary(rows: list[dict], output: Path) -> None:
    import matplotlib.pyplot as plt

    output.parent.mkdir(parents=True, exist_ok=True)
    metrics = ("queue_length", "waiting_time", "average_speed", "arrived_count", "vehicles_in_network")
    methods = sorted({row["method"] for row in rows})
    figure, axes = plt.subplots(3, 2, figsize=(14, 12), constrained_layout=True)
    for axis, metric in zip(axes.flat, (*metrics, "execution_seconds")):
        for method in methods:
            values = [row[metric] for row in rows if row["method"] == method]
            labels = [row["scenario"] for row in rows if row["method"] == method]
            axis.plot(labels, values, marker="o", label=method)
        axis.set_title(metric.replace("_", " ").title())
        axis.grid(alpha=0.3)
        axis.tick_params(axis="x", rotation=25)
    axes.flat[0].legend()
    axes.flat[-1].set_xlabel("Scenario")
    figure.savefig(output, dpi=150)
    plt.close(figure)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=SEED)
    parser.add_argument("--timesteps", type=int, default=TIMESTEPS)
    args = parser.parse_args()
    log_path = ROOT / "overnight_execution.log"
    configure_logging(log_path)
    pipeline_start = time.perf_counter()
    timings = {}
    logging.info("Pipeline started: seed=%s timesteps=%s", args.seed, args.timesteps)

    for method, script in (
        ("fixed_time", ROOT / "FixedTime" / "run_fixed_time.py"),
        ("rule_based", ROOT / "RuleBased" / "run_rule_based.py"),
    ):
        for scenario in SCENARIOS:
            run_command(
                [sys.executable, str(script), "--scenario", scenario, "--seed", str(args.seed)],
                timings,
                f"{method}_{scenario}",
            )

    training_ok = run_command(
        [
            sys.executable, "-m", "TraCI.train_multiscenario",
            "--seed", str(args.seed), "--timesteps", str(args.timesteps),
        ],
        timings,
        "drl_training",
    )
    evaluation_ok = training_ok and run_command(
        [
            sys.executable, "-m", "TraCI.evaluate",
            "--model", "models/ppo_final.zip", "--output-dir", "evaluation",
            "--seed", str(args.seed),
        ],
        timings,
        "drl_evaluation",
    )

    rows = []
    for method, directory, prefix in (
        ("fixed_time", ROOT / "FixedTime" / "logs", "fixed_time"),
        ("rule_based", ROOT / "RuleBased" / "logs", "rule_based"),
    ):
        for scenario in SCENARIOS:
            path = directory / f"seed{args.seed}" / f"{prefix}_{scenario}_seed{args.seed}.jsonl"
            key = f"{method}_{scenario}"
            if path.is_file():
                rows.append(aggregate_records(read_jsonl(path), method, scenario, timings.get(key, math.nan)))
            else:
                logging.error("Missing baseline log: %s", path)
    if evaluation_ok:
        rows.extend(read_drl_rows(ROOT / "evaluation" / "metrics.csv", timings["drl_evaluation"]))
    else:
        logging.error("Skipping DRL summary because training/evaluation failed")

    write_summary(rows, ROOT / "results" / "summary_final.csv")
    if rows:
        plot_summary(rows, ROOT / "results" / "comparison_final.png")
    timings["total_pipeline"] = time.perf_counter() - pipeline_start
    (ROOT / "results" / "pipeline_timings.json").write_text(
        json.dumps(timings, indent=2), encoding="utf-8"
    )
    logging.info("Pipeline completed in %.2fs", timings["total_pipeline"])
    return 0 if training_ok and evaluation_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
