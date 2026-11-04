from pathlib import Path
import sys
import json

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "TraCI"))

from RuleBased.rule_based_controller import choose_action, get_group_queues
from core.environment import Environment

log_dir = ROOT / "RuleBased" / "logs"
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


with Environment(
    settings={"gui": True, "max_episode_seconds": 300, "simulation_step": 0.1}
) as env:

    state = env.reset("imbalance", seed=42)
    # Initial state
    show_state(state)
    with open(log_dir / "rule_based_imbalance_seed42.jsonl", "w", encoding="utf-8") as log_file:
        # Run simulation
        for i in range(60):
            action = choose_action(state)

            record = {
                "scenario": state["scenario"],
                "decision_time": state["simulation_time"],
                "phase_id": state["tls"]["J"]["phase_id"],
                "green_elapsed": state["tls"]["J"]["green_elapsed"],
                "queues": get_group_queues(state),
                "chosen_action": action,
            }
            print(
                "Time:", state["simulation_time"],
                "Phase:", state["tls"]["J"]["phase_id"],
                "Green elapsed:", state["tls"]["J"]["green_elapsed"],
                "Chosen:", action,
            )

            print("Queues:", get_group_queues(state))
            
            state, terminated, truncated, info = env.step(action)

            record["executed_action"] = info["executed_action"]["J"]
            record["override_reason"] = info["override_reason"]["J"]
            record["next_time"] = state["simulation_time"]

            print(
                f"Step {i + 1}: "
                f"time={state['simulation_time']}s, "
                f"action={info['executed_action']}"
            )

            print(
                "Executed:", info["executed_action"]["J"],
                "Reason:", info["override_reason"]["J"],
            )

            # Show details every 15 seconds
            if i % 3 == 2:
                show_state(state)

            log_file.write(json.dumps(record, ensure_ascii=False) + "\n")

            if terminated or truncated:
                print("Simulation ended:", info["end_reason"])
                break