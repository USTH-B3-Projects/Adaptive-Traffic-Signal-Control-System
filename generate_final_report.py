"""Generate the Seed 107 DRL comparison report from pipeline artifacts."""
import argparse
import csv
import json
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parent
SCENARIOS = ("low", "medium", "high", "imbalance")
METHODS = ("fixed_time", "rule_based", "drl_ppo")
CORE_METRICS = (
    ("waiting_time", "Waiting Time (s)", "lower"),
    ("queue_length", "Queue Length (vehicles)", "lower"),
    ("average_speed", "Average Speed (m/s)", "higher"),
    ("arrived_count", "Arrived Count (vehicles)", "higher"),
    ("vehicles_in_network", "Vehicles in Network", "lower"),
)


def load_summary(path: Path) -> dict[tuple[str, str], dict[str, float]]:
    with path.open(newline="", encoding="utf-8") as file:
        rows = csv.DictReader(file)
        result = {}
        for row in rows:
            result[(row["method"], row["scenario"])] = {
                key: float(value)
                for key, value in row.items()
                if key not in ("method", "scenario") and value != ""
            }
        return result


def load_timings(path: Path) -> dict[str, float]:
    with path.open(encoding="utf-8") as file:
        return {key: float(value) for key, value in json.load(file).items()}


def load_evaluation_summary(path: Path) -> dict[tuple[str, str], dict[str, float]]:
    with path.open(newline="", encoding="utf-8") as file:
        result = {}
        for row in csv.DictReader(file):
            result[("drl_ppo", row["scenario"])] = {
                key.removesuffix("_mean"): float(value)
                for key, value in row.items()
                if key != "scenario" and value != ""
            }
        return result


def fmt(value: float | None) -> str:
    return "N/A" if value is None else f"{value:.2f}"


def improvement(baseline: float, candidate: float, direction: str) -> float | None:
    if baseline == 0:
        return None
    if direction == "lower":
        return (baseline - candidate) / baseline * 100
    return (candidate - baseline) / baseline * 100


def runtime_text(seconds: float) -> str:
    return f"{seconds / 3600:.2f} hours ({seconds:.2f} seconds)"


def metric_table(data: dict[tuple[str, str], dict[str, float]]) -> str:
    lines = [
        "| Metric | Fixed-Time | Rule-Based | DRL PPO (800k) |",
        "|---|---:|---:|---:|",
    ]
    for scenario in SCENARIOS:
        lines.append(f"| **{scenario.title()}** |  |  |  |")
        for key, label, _ in CORE_METRICS:
            values = [
                data.get((method, scenario), {}).get(key)
                for method in METHODS
            ]
            lines.append(
                f"| {label} | {fmt(values[0])} | {fmt(values[1])} | {fmt(values[2])} |"
            )
    return "\n".join(lines)


def improvement_table(data: dict[tuple[str, str], dict[str, float]]) -> str:
    lines = [
        "| Scenario | Metric | DRL vs Fixed-Time | DRL vs Rule-Based |",
        "|---|---|---:|---:|",
    ]
    for scenario in SCENARIOS:
        for key, label, direction in CORE_METRICS[:3]:
            fixed = data.get(("fixed_time", scenario), {}).get(key)
            rule = data.get(("rule_based", scenario), {}).get(key)
            drl = data.get(("drl_ppo", scenario), {}).get(key)
            fixed_value = improvement(fixed, drl, direction) if fixed is not None and drl is not None else None
            rule_value = improvement(rule, drl, direction) if rule is not None and drl is not None else None
            lines.append(
                f"| {scenario.title()} | {label} | {fmt(fixed_value)}% | {fmt(rule_value)}% |"
            )
    return "\n".join(lines)


def execution_table(data: dict[tuple[str, str], dict[str, float]], timings: dict[str, float]) -> str:
    lines = [
        "| Method | Scenario | Execution Time (s) |",
        "|---|---|---:|",
    ]
    for method in METHODS:
        for scenario in SCENARIOS:
            if method == "drl_ppo":
                seconds = timings.get("drl_evaluation")
            else:
                seconds = timings.get(f"{method}_{scenario}")
            lines.append(f"| {method} | {scenario} | {fmt(seconds)} |")
    lines.append(f"| PPO training | all scenarios | {fmt(timings.get('drl_training'))} |")
    lines.append(f"| Total pipeline | all stages | {fmt(timings.get('total_pipeline'))} |")
    return "\n".join(lines)


def build_report(data: dict[tuple[str, str], dict[str, float]], timings: dict[str, float]) -> str:
    total = timings.get("total_pipeline", 0.0)
    training = timings.get("drl_training", 0.0)
    checkpoint = ROOT / "models" / "checkpoints" / "ppo_multiscenario_500000_steps.zip"
    has_20k = any(
        re.search(r"(?<!\d)(?:20k|20000)(?!\d)", str(path), re.IGNORECASE)
        for path in ROOT.glob("**/*")
        if path.is_file()
    )
    report = [
        "# DRL Seed 107 Experimental Report",
        "",
        "**Status:** Completed Seed 107 multi-scenario PPO experiment.",
        "",
        "## 1. Objective",
        "",
        "Compare Fixed-Time, Rule-Based, and a single PPO agent trained across "
        "the four SUMO demand scenarios.",
        "",
        "## 2. Experimental Setup",
        "",
        "| Parameter | Configuration |",
        "|---|---|",
        "| Simulator | SUMO 1.28.0 |",
        "| Algorithm | PPO (Stable-Baselines3) |",
        "| Training scenarios | Low; Medium; High; Imbalance |",
        "| Seed | 107 |",
        "| Timesteps | 800,000 |",
        "| Simulation step | 0.1 s |",
        "| Decision interval | 5 s (50 simulation steps) |",
        "| GUI | Disabled |",
        f"| Total pipeline runtime | {runtime_text(total)} |",
        f"| PPO training runtime | {runtime_text(training)} |",
        "",
        "## 3. Evaluation Metrics",
        "",
        "The report uses the pipeline's measured values for queue length, "
        "waiting time, average speed, arrived count, and vehicles remaining. "
        "For waiting time and queue length, lower is better; for speed and "
        "arrivals, higher is better.",
        "",
        "## 4. Results — Seed 107",
        "",
        metric_table(data),
        "",
        "## 5. DRL PPO Improvement",
        "",
        "Improvement (%) = (baseline - DRL) / baseline x 100 for metrics where "
        "lower is better. For average speed, the numerator is DRL - baseline.",
        "",
        improvement_table(data),
        "",
        "## 6. Execution Time",
        "",
        execution_table(data, timings),
        "",
        "## 7. Advanced Performance Metrics",
        "",
        "| Method | Scenario | Total Travel Time | Average Delay / Vehicle | Throughput |",
        "|---|---|---:|---:|---:|",
    ]
    for method in METHODS:
        for scenario in SCENARIOS:
            row = data.get((method, scenario), {})
            report.append(
                f"| {method} | {scenario} | {fmt(row.get('total_travel_time'))} | "
                f"{fmt(row.get('average_delay_per_vehicle'))} | {fmt(row.get('throughput'))} |"
            )
    report.extend(
        [
            "",
            "## 8. Analysis",
            "",
            "### Heavy and Imbalanced Traffic",
            "",
            "The high and imbalance scenarios are the most demanding tests. "
            "The tables above should be read together: queue and waiting-time "
            "reductions indicate congestion relief, while speed and throughput "
            "indicate whether that relief translates into useful traffic flow.",
            "",
            "### Single Multi-Scenario Agent",
            "",
            "The PPO policy is one agent trained while sampling all four scenarios. "
            "This improves deployment simplicity and tests transfer across demand "
            "patterns, but it can trade peak performance in one scenario for "
            "robustness across the full distribution.",
            "",
            "### Computation Cost",
            "",
            f"The recorded PPO training time was {runtime_text(training)} and the "
            f"complete pipeline took {runtime_text(total)}. Checkpointing provides "
            "recovery points during long runs.",
            "",
            "### Learning Curve and Checkpoint",
            "",
            f"The recommended deployment checkpoint is "
            f"`models/checkpoints/ppo_multiscenario_500000_steps.zip` "
            f"({'present' if checkpoint.is_file() else 'not found in the workspace'}).",
            "",
            "The requested peak-reward and policy-degradation claims must be "
            "verified against the TensorBoard event file before being treated as "
            "measured findings; this report does not fabricate values that are "
            "not present in the CSV/JSON inputs.",
            "",
            "### Comparison with a 20k Single-Scenario Model",
            "",
            (
                "A 20k single-scenario artifact was not found in the workspace; "
                "therefore a numerical comparison is not reported."
                if not has_20k
                else
                "A 20k artifact exists in the workspace and should be compared "
                "using the same seed, scenario, and metric definitions."
            ),
            "",
            "## 9. Data Sources",
            "",
            "- `results/summary_final.csv`",
            "- `evaluation/summary.csv`",
            "- `results/pipeline_timings.json`",
            "- `results/comparison_result/baseline_comparsion_seed57.md` "
            "(format reference)",
        ]
    )
    return "\n".join(report) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--summary", type=Path, default=ROOT / "results" / "summary_final.csv")
    parser.add_argument("--evaluation", type=Path, default=ROOT / "evaluation" / "summary.csv")
    parser.add_argument("--timings", type=Path, default=ROOT / "results" / "pipeline_timings.json")
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "results" / "comparison_result" / "drl_seed107_report.md",
    )
    args = parser.parse_args()
    data = load_summary(args.summary)
    if args.evaluation.is_file():
        data.update(load_evaluation_summary(args.evaluation))
    timings = load_timings(args.timings)
    missing = [
        (method, scenario)
        for method in METHODS
        for scenario in SCENARIOS
        if (method, scenario) not in data
    ]
    if missing:
        raise ValueError(f"Missing summary rows: {missing}")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(build_report(data, timings), encoding="utf-8")
    print(f"Generated report: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
