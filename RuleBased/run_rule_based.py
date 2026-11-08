from pathlib import Path
import sys
import json
import argparse

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "TraCI"))

from RuleBased.rule_based_controller import choose_action, get_group_queues
from core.environment import Environment

parser = argparse.ArgumentParser(
    description="Run the rule-based baseline."
)

parser.add_argument(
    "--scenario",
    choices=["low", "medium", "high", "imbalance"],
    required=True,
)

parser.add_argument(
    "--seed",
    type=int,
    required=True,
)

args = parser.parse_args()

log_dir = ROOT / "RuleBased" / "logs" / f"seed{args.seed}"
log_dir.mkdir(parents=True, exist_ok=True)

def show_state(state):
    print(f"\n===== TIME: {state['simulation_time']}s =====")
    print("Scenario:", state["scenario"])

    for tls_id, tls in state["tls"].items():
        print(f"\nTraffic Light: {tls_id}")
        print("Phase ID:", tls["phase_id"])
        print("Phase State:", tls["phase_state"])
        print("Green Elapsed:", tls["green_elapsed"])
        print("In Transition:", tls["in_transition"])

        print("\nLane Information:")

        for lane_id, data in tls["lanes"].items():
            print(
                f"  {lane_id}: "
                f"vehicles={data['vehicle_count']}, "
                f"queue={data['halting_count']}, "
                f"waiting={data['waiting_time']}, "
                f"speed={data['average_speed']}"
            )

        print("\nTotals:", tls["totals"])

log_path = (log_dir / f"rule_based_{args.scenario}_seed{args.seed}.jsonl")
print(f"Running rule-based: scenario={args.scenario}, seed={args.seed}")
print(f"Log: {log_path}")

with Environment(
    settings={"gui": False, "max_episode_seconds": 3600, "simulation_step": 0.1}
) as env:

    state = env.reset(args.scenario, seed=args.seed)
    # Initial state
    show_state(state)
    arrived_count = 0
    with open(log_path, "w", encoding="utf-8") as log_file:
        # Run simulation
        i = 0
        while True:
            action = choose_action(state)

            record = {
                "scenario": state["scenario"],
                "seed": args.seed,
                "controller": "rule_based",
                "simulation_time": state["simulation_time"],
                "phase_id": state["tls"]["J"]["phase_id"],
                "green_elapsed": state["tls"]["J"]["green_elapsed"],
                "queues": get_group_queues(state),
                "total_waiting_time": state["tls"]["J"]["totals"]["waiting_time"],
                "chosen_action": action,
            }
            
            state, terminated, truncated, info = env.step(action)
            arrived_count += int(info["arrived_count"])

            record["executed_action"] = info["executed_action"]["J"]
            record["override_reason"] = info["override_reason"]["J"]
            record["next_time"] = state["simulation_time"]
            record["average_speed"] = (
                state["tls"]["J"]["totals"]["average_speed"] or 0.0
            )
            record["arrived_count"] = arrived_count
            record["vehicles_in_network"] = info["vehicles_in_network"]

            log_file.write(json.dumps(record, ensure_ascii=False) + "\n")

            i += 1

            # Show details after each 60s = 12 turrs
            if i % 12 == 0:
                print(f"Progress: {state['simulation_time']:.0f}/3600 s")

            if terminated or truncated:
                print(f"Simulation ended at {state['simulation_time']:.1f}:", info["end_reason"])
                break