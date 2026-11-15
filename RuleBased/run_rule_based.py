from pathlib import Path
import sys
import json
import argparse

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "TraCI"))

from RuleBased.rule_based_controller import (
    choose_action,
    get_group_queues,
    CyclicRuleBasedController,
)
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

parser.add_argument(
    "--map",
    dest="map_name",
    choices=["simple_intersection", "o_cho_dua", "bigc_thang_long"],
    default="simple_intersection",
)

parser.add_argument(
    "--duration",
    type=int,
    default=None,
    help="Run duration in seconds; omit to use scenario end.",
)

args = parser.parse_args()

if args.duration is not None and args.duration <= 0:
    parser.error("--duration must be positive.")

MIN_GREEN = 30
MAX_GREEN = 75

if args.map_name == "simple_intersection":
    scenarios_path = (
        ROOT / "TraCI" / "configs"
        / "scenarios_simple_intersection.yaml"
    )
    tls_id = "J"
    green_phases = None
    green_profiles = None

elif args.map_name == "o_cho_dua":
    if args.scenario not in ("high", "imbalance"):
        parser.error("O Cho Dua only supports high and imbalance.")

    scenarios_path = (
        ROOT / "TraCI" / "configs"
        / "scenarios_o_cho_dua.yaml"
    )
    tls_id = (
        "joinedS_5707161152_6677677155_"
        "6677677160_6677677161_#2more"
    )
    green_phases = [0, 2, 5, 7]
    green_profiles = {tls_id: green_phases}

else:
    parser.error("Map configuration is not ready yet.")

log_dir = ROOT / "RuleBased" / "logs" / args.map_name / f"seed{args.seed}"
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

if args.duration is None:
    log_path = (
        log_dir
        / f"rule_based_{args.scenario}_seed{args.seed}.jsonl"
    )
else:
    log_path = (
        log_dir
        / "trials"
        / (
            f"rule_based_{args.scenario}_seed{args.seed}"
            f"_{args.duration}s.jsonl"
        )
    )

log_path.parent.mkdir(parents=True, exist_ok=True)

print(
    f"Running rule-based: map={args.map_name}, "
    f"scenario={args.scenario}, seed={args.seed}"
)
print("Log:", log_path)

def build_phase_lanes(connection, tls_id, green_phases):
    api = connection.trafficlight
    program_id = api.getProgram(tls_id)

    program = next(
        program
        for program in api.getAllProgramLogics(tls_id)
        if program.programID == program_id
    )

    controlled_links = api.getControlledLinks(tls_id)

    phase_lanes = {}

    for phase_id in green_phases:
        phase_state = program.phases[phase_id].state

        incoming_lanes = {
            link[0]
            for signal_index, signal in enumerate(phase_state)
            if signal in ("G", "g")
            for link in controlled_links[signal_index]
            if link
        }

        phase_lanes[phase_id] = sorted(incoming_lanes)

    return phase_lanes

with Environment(
    scenarios_path=scenarios_path,
    settings={
        "gui": False,
        "simulation_step": 0.1,
        "decision_interval": 5,
        "min_green": MIN_GREEN,
        "max_green": MAX_GREEN,
        "max_episode_seconds": args.duration,
    },
    tls_ids=[tls_id],
    green_phases_by_tls=green_profiles,
    stop_on_empty=False,
) as env:

    state = env.reset(args.scenario, seed=args.seed)
    
    controller = None

    if args.map_name == "o_cho_dua":
        phase_lanes = build_phase_lanes(
            env.connection,
            tls_id,
            green_phases,
        )

        controller = CyclicRuleBasedController(
            tls_id=tls_id,
            green_phases=green_phases,
            phase_lanes=phase_lanes,
            min_green=MIN_GREEN,
            max_green=MAX_GREEN,
        )

        print("Green phase order:", green_phases)

        for phase_id, lanes in phase_lanes.items():
            print(f"Phase {phase_id}: {lanes}")

    show_state(state)

    # Match the episode window used by Environment.
    end_limits = []

    if env.scenario.end is not None:
        end_limits.append(env.scenario.end)

    if args.duration is not None:
        end_limits.append(env.scenario.begin + args.duration)

    if not end_limits:
        raise ValueError(
            "Scenario has no end time. Please provide --duration."
        )

    end_time = min(end_limits)
    print(f"Simulation window: {env.scenario.begin} -> {end_time}")

    # "x" prevents overwriting an existing log.
    with open(log_path, "x", encoding="utf-8") as log_file:
        next_progress_time = state["simulation_time"] + 60.0
        sample_count = 0

        while state["simulation_time"] < end_time - 1e-8:
            tls = state["tls"][tls_id]

            if controller is None:
                # Original controller for the simple intersection.
                action = choose_action(state)
                phase_queues = None
            else:
                action = controller.choose_action(state)
                phase_queues = controller.get_phase_queues(state)

            lane_queues = {
                lane_id: data["halting_count"]
                for lane_id, data in tls["lanes"].items()
            }

            # Record the observation BEFORE applying the action.
            record = {
                "map": args.map_name,
                "scenario": state["scenario"],
                "seed": args.seed,
                "controller": "rule_based",
                "simulation_time": state["simulation_time"],
                "tls_id": tls_id,
                "program_id": (
                    env.connection.trafficlight.getProgram(tls_id)
                ),
                "phase_id": tls["phase_id"],
                "phase_state": tls["phase_state"],
                "green_elapsed": tls["green_elapsed"],
                "in_transition": tls["in_transition"],
                "lane_queues": lane_queues,
                "total_queue": sum(lane_queues.values()),
                "total_waiting_time": tls["totals"]["waiting_time"],
                "chosen_action": action,
                "min_green": MIN_GREEN,
                "max_green": MAX_GREEN,
                "decision_interval": 5,
            }

            if controller is None:
                record["queues"] = get_group_queues(state)
            else:
                record["phase_queues"] = phase_queues

            next_state, terminated, truncated, info = env.step(action)

            record["executed_action"] = (
                info["executed_action"][tls_id]
            )
            record["override_reason"] = (
                info["override_reason"][tls_id]
            )
            record["automatic_events"] = info["automatic_events"]
            record["next_time"] = next_state["simulation_time"]

            log_file.write(
                json.dumps(record, ensure_ascii=False) + "\n"
            )
            sample_count += 1

            # Detailed output for short trial runs.
            if args.duration is not None:
                print(
                    f"t={record['simulation_time']:6.1f} | "
                    f"phase={record['phase_id']} | "
                    f"green={record['green_elapsed']:5.1f} | "
                    f"queues={phase_queues} | "
                    f"chosen={action} | "
                    f"executed={record['executed_action']} | "
                    f"reason={record['override_reason']} | "
                    f"next_phase="
                    f"{next_state['tls'][tls_id]['phase_id']}"
                )

                for event in info["automatic_events"]:
                    print("  AUTO:", event)

            state = next_state

            if state["simulation_time"] >= next_progress_time - 1e-8:
                print(
                    f"Progress: {state['simulation_time']:.1f}"
                    f"/{end_time:.1f} s"
                )
                next_progress_time += 60.0

            if terminated or truncated:
                print(
                    f"Simulation ended at "
                    f"{state['simulation_time']:.1f}:",
                    info["end_reason"],
                )
                break

    print("Samples:", sample_count)
    print("Finished:", log_path)