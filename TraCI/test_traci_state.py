
from pathlib import Path
import sys

# Import TraCI Environment
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from core.environment import Environment


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
    settings={"gui": False, "max_episode_seconds": 90}
) as env:

    state = env.reset("low", seed=42)

    # Initial state
    show_state(state)

    # Run simulation
    for i in range(18):
        state, terminated, truncated, info = env.step("KEEP")

        print(
            f"Step {i + 1}: "
            f"time={state['simulation_time']}s, "
            f"action={info['executed_action']}"
        )

        # Show details every 15 seconds
        if i % 3 == 2:
            show_state(state)

        if terminated or truncated:
            print("Simulation ended:", info["end_reason"])
            break