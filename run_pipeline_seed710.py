"""Run the complete Seed 710 CUDA PPO experiment."""
import argparse
import csv
import json
import logging
import os
from pathlib import Path
import subprocess
import sys
import time

from run_pipeline_seed107 import aggregate_records, read_drl_rows


ROOT = Path(__file__).resolve().parent
SCENARIOS = ("low", "medium", "high", "imbalance")


def run(command: list[str], output: Path, timings: dict, name: str) -> None:
    started = time.perf_counter()
    logging.info("START %s: %s", name, " ".join(command))
    with output.open("a", encoding="utf-8") as stream:
        completed = subprocess.run(
            command, cwd=ROOT, env=os.environ.copy(),
            stdout=stream, stderr=subprocess.STDOUT, check=False,
        )
    timings[name] = time.perf_counter() - started
    if completed.returncode:
        raise RuntimeError(f"{name} failed with exit code {completed.returncode}")
    logging.info("DONE %s in %.2fs", name, timings[name])


def require_cuda() -> None:
    import torch

    if not torch.cuda.is_available():
        raise RuntimeError(
            f"CUDA is required but unavailable (torch={torch.__version__}). "
            "Install a CUDA-enabled PyTorch build before starting Seed 710."
        )
    logging.info("Using CUDA device: %s", torch.cuda.get_device_name(0))


def write_summary(rows: list[dict], path: Path) -> None:
    fields = (
        "method", "scenario", "queue_length", "waiting_time", "average_speed",
        "arrived_count", "vehicles_in_network", "total_travel_time",
        "average_delay_per_vehicle", "throughput", "execution_seconds",
    )
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def create_bar_plot(summary: Path, output: Path) -> None:
    import matplotlib.pyplot as plt
    import numpy as np

    metrics = (
        ("queue_length", "Queue Length"),
        ("waiting_time", "Waiting Time"),
        ("average_speed", "Average Speed"),
        ("arrived_count", "Arrived Count"),
        ("vehicles_in_network", "Vehicles In Network"),
    )
    rows = list(csv.DictReader(summary.open(newline="", encoding="utf-8")))
    methods = ("fixed_time", "rule_based", "drl_ppo")
    figure, axes = plt.subplots(3, 2, figsize=(16, 13), constrained_layout=True)
    positions = np.arange(len(SCENARIOS))
    for axis, (metric, title) in zip(axes.flat, metrics):
        width = 0.25
        for index, method in enumerate(methods):
            values = [
                float(next(row[metric] for row in rows
                           if row["method"] == method and row["scenario"] == scenario))
                for scenario in SCENARIOS
            ]
            axis.bar(positions + (index - 1) * width, values, width, label=method)
        axis.set_title(title)
        axis.set_xticks(positions, SCENARIOS)
        axis.grid(axis="y", alpha=0.3)
    axes.flat[-1].axis("off")
    axes.flat[0].legend()
    output.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(output, dpi=160)
    plt.close(figure)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=710)
    parser.add_argument("--timesteps", type=int, default=600_000)
    args = parser.parse_args()
    root_result = ROOT / "results" / f"seed{args.seed}"
    eval_dir = ROOT / "evaluation" / f"seed{args.seed}"
    model_dir = ROOT / "models" / f"seed{args.seed}"
    checkpoint_dir = model_dir / "checkpoints"
    plot_dir = root_result / "plots"
    for directory in (root_result, eval_dir, checkpoint_dir, plot_dir):
        directory.mkdir(parents=True, exist_ok=True)
    log_dir = ROOT / "results" / "logs" / f"seed{args.seed}"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / "pipeline.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=(logging.FileHandler(log_path, encoding="utf-8"), logging.StreamHandler()),
    )
    require_cuda()
    started = time.perf_counter()
    timings = {}
    subprocess_log = log_dir / "subprocess.log"

    for method, script in (
        ("fixed_time", ROOT / "FixedTime" / "run_fixed_time.py"),
        ("rule_based", ROOT / "RuleBased" / "run_rule_based.py"),
    ):
        for scenario in SCENARIOS:
            run(
                [sys.executable, str(script), "--scenario", scenario, "--seed", str(args.seed)],
                subprocess_log, timings, f"{method}_{scenario}",
            )

    final_model = model_dir / f"ppo_seed{args.seed}_final"
    run(
        [sys.executable, "-m", "DRL.train_multiscenario",
         "--seed", str(args.seed), "--timesteps", str(args.timesteps),
         "--device", "cuda", "--checkpoint-prefix", f"ppo_seed{args.seed}",
         "--model", str(final_model), "--log-dir", str(ROOT / "runs" / f"ppo_seed{args.seed}"),
         "--checkpoint-dir", str(checkpoint_dir)],
        subprocess_log, timings, "drl_training",
    )
    run(
        [sys.executable, "-m", "DRL.evaluate", "--seed", str(args.seed),
         "--model", f"{final_model}.zip", "--output-dir", str(eval_dir)],
        subprocess_log, timings, "drl_evaluation",
    )

    rows = []
    for method, directory, prefix in (
        ("fixed_time", ROOT / "FixedTime" / "logs", "fixed_time"),
        ("rule_based", ROOT / "RuleBased" / "logs", "rule_based"),
    ):
        for scenario in SCENARIOS:
            log = directory / f"seed{args.seed}" / f"{prefix}_{scenario}_seed{args.seed}.jsonl"
            rows.append(aggregate_records(
                [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines() if line],
                method, scenario, timings[f"{method}_{scenario}"],
            ))
    rows.extend(read_drl_rows(eval_dir / "metrics.csv", timings["drl_evaluation"]))
    summary = root_result / "summary_final.csv"
    write_summary(rows, summary)
    create_bar_plot(summary, plot_dir / f"seed{args.seed}_baseline_comparison_5plots.png")
    timings["total_pipeline"] = time.perf_counter() - started
    (root_result / "pipeline_timings.json").write_text(json.dumps(timings, indent=2), encoding="utf-8")
    run(
        [sys.executable, "generate_final_report.py", "--seed", str(args.seed),
         "--timesteps", str(args.timesteps),
         "--output", str(ROOT / "results" / "comparison_result" / f"drl_seed{args.seed}_report.md")],
        subprocess_log, timings, "report_generation",
    )
    logging.info("Pipeline completed in %.2fs", timings["total_pipeline"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
