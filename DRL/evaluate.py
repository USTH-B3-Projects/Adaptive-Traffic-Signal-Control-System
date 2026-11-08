"""Evaluate a trained PPO model on all traffic-demand scenarios."""
import argparse
import csv
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from stable_baselines3 import PPO

from .gym_env import TrafficSignalEnv


SCENARIOS = ("low", "medium", "high", "imbalance")
METRICS = (
    "queue_length",
    "waiting_time",
    "average_speed",
    "arrived_count",
    "vehicles_in_network",
)


def evaluate_scenario(model: PPO, scenario: str, seed: int) -> dict:
    env = TrafficSignalEnv(scenario)
    observation, _ = env.reset(seed=seed)
    rows = []
    cumulative_arrived = 0
    try:
        terminated = truncated = False
        while not terminated and not truncated:
            action, _ = model.predict(observation, deterministic=True)
            observation, _, terminated, truncated, info = env.step(int(action))
            cumulative_arrived += int(info["arrived_count"])
            rows.append(
                {
                    "scenario": scenario,
                    "simulation_time": info["sim_time"],
                    "queue_length": info["queue_length"],
                    "waiting_time": info["waiting_time"],
                    "average_speed": info["average_speed"],
                    "arrived_count": cumulative_arrived,
                    "vehicles_in_network": info["vehicles_in_network"],
                }
            )
    finally:
        env.close()
    if not rows:
        raise RuntimeError(f"Scenario {scenario!r} produced no evaluation steps.")
    return {"scenario": scenario, "rows": rows}


def write_csv(results: list[dict], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ("scenario", "simulation_time", *METRICS)
    with output.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for result in results:
            writer.writerows(result["rows"])


def write_summary(results: list[dict], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ("scenario", *(f"{metric}_mean" for metric in METRICS))
    with output.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for result in results:
            rows = result["rows"]
            writer.writerow(
                {
                    "scenario": result["scenario"],
                    **{
                        f"{metric}_mean": float(np.mean([row[metric] for row in rows]))
                        for metric in METRICS
                    },
                }
            )


def plot_results(results: list[dict], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    figure, axes = plt.subplots(3, 2, figsize=(13, 12), constrained_layout=True)
    for result in results:
        rows = result["rows"]
        label = result["scenario"].title()
        time = [row["simulation_time"] for row in rows]
        for axis, metric in zip(axes.flat, METRICS):
            axis.plot(time, [row[metric] for row in rows], label=label)
            axis.set_title(metric.replace("_", " ").title())
            axis.set_xlabel("Simulation time (s)")
            axis.grid(alpha=0.3)
    axes.flat[-1].axis("off")
    axes.flat[0].legend()
    figure.savefig(output, dpi=150)
    plt.close(figure)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=Path, default=Path("models/ppo_low.zip"))
    parser.add_argument("--output-dir", type=Path, default=Path("evaluation"))
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    if args.seed < 0:
        parser.error("--seed must be nonnegative")
    if not args.model.is_file():
        parser.error(f"Model not found: {args.model}")

    model = PPO.load(args.model)
    results = [evaluate_scenario(model, scenario, args.seed) for scenario in SCENARIOS]
    write_csv(results, args.output_dir / "metrics.csv")
    write_summary(results, args.output_dir / "summary.csv")
    plot_results(results, args.output_dir / "comparison.png")
    print(f"Evaluation outputs: {args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
