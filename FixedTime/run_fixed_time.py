from pathlib import Path
import sys
import json
import argparse

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "TraCI"))

from core.scenario_loader import ScenarioLoader, load_settings, validate_settings
from core.simulation import Simulation

parser = argparse.ArgumentParser(
    description="Run the fixed-time baseline."
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
    "--tls-id",
    help="TLS to observe; required for complex maps.",
)

parser.add_argument(
    "--duration",
    type=int,
    default=None,
    help="Run duration in seconds; omit to use scenario end.",
)

args = parser.parse_args()

log_dir = ROOT / "FixedTime" / "logs" / args.map_name / f"seed{args.seed}"
log_dir.mkdir(parents=True, exist_ok=True)

settings = load_settings()

settings["gui"] = False
settings["simulation_step"] = 0.1
settings = validate_settings(settings)

scenario_files = {
    "simple_intersection": "scenarios_simple_intersection.yaml",
    "o_cho_dua": "scenarios_o_cho_dua.yaml",
}

if args.map_name not in scenario_files:
    parser.error("Map configuration is not ready yet.")

if args.map_name != "simple_intersection":
    if args.scenario not in ("high", "imbalance"):
        parser.error("Complex maps only use high and imbalance.")
    if not args.tls_id:
        parser.error("--tls-id is required for complex maps.")

if args.duration is not None and args.duration <= 0:
    parser.error("--duration must be positive.")

tls_id = args.tls_id or "J"

loader = ScenarioLoader(
    ROOT / "TraCI" / "configs" / scenario_files[args.map_name]
)
scenario = loader.load(args.scenario)
simulation = Simulation(settings)

# Requested duration is measured from the scenario's begin time.
if args.duration is not None:
    end_time = scenario.begin + args.duration
    if scenario.end is not None:
        end_time = min(end_time, scenario.end)
else:
    end_time = scenario.end
    if end_time is None:
        end_time = scenario.begin + 3600

if end_time <= scenario.begin:
    parser.error("End time must be after scenario begin.")

def get_lane_metrics(connection, incoming_lanes):
    lane_queues = {
        lane_id: connection.lane.getLastStepHaltingNumber(lane_id)
        for lane_id in incoming_lanes
    }

    total_waiting_time = sum(
        connection.lane.getWaitingTime(lane_id)
        for lane_id in incoming_lanes
    )

    return lane_queues, total_waiting_time

log_path = (
    log_dir / f"fixed_time_{args.scenario}_seed{args.seed}.jsonl"
)
print(f"Running fixed-time: scenario={args.scenario}, seed={args.seed}")
print(f"Log: {log_path}")

try:
    connection = simulation.start(scenario, seed=args.seed)
    api = connection.trafficlight

    if tls_id not in api.getIDList():
        raise ValueError(
            f"Unknown TLS: {tls_id}. "
            f"Available: {list(api.getIDList())}"
        )

    program_id = api.getProgram(tls_id)
    programs = [
        program
        for program in api.getAllProgramLogics(tls_id)
        if program.programID == program_id
    ]

    if len(programs) != 1 or programs[0].type != 0:
        raise ValueError(
            f"{tls_id}: FT requires one active static program."
        )

    program = programs[0]

    incoming_lanes = sorted({
        link[0]
        for group in api.getControlledLinks(tls_id)
        for link in group
        if link
    })

    if not incoming_lanes:
        raise ValueError(f"{tls_id}: no incoming lanes found.")

    print("Map:", args.map_name)
    print("Config:", scenario.config_path)
    print("TLS:", tls_id)
    print("Program:", program_id)
    print("Incoming lanes:", incoming_lanes)
    print(f"Simulation window: {scenario.begin} -> {end_time}")

    for index, phase in enumerate(program.phases):
        print(
            f"Phase {index}: "
            f"duration={phase.duration}, state={phase.state}"
        )

    # Keep short trial runs separate from full evaluation logs.
    if args.duration is not None:
        log_path = (
            log_dir / "trials"
            / f"fixed_time_{args.scenario}_seed{args.seed}"
              f"_{args.duration}s.jsonl"
        )

    log_path.parent.mkdir(parents=True, exist_ok=True)
    print("Writing log:", log_path)

    # Exclusive creation prevents overwriting an existing run.
    with open(log_path, "x", encoding="utf-8") as log_file:
        next_sample_time = connection.simulation.getTime()
        next_progress_time = next_sample_time + 60.0

        while connection.simulation.getTime() < end_time - 1e-8:
            now = connection.simulation.getTime()

            if now >= next_sample_time - 1e-8:
                lane_queues, waiting_time = get_lane_metrics(
                    connection, incoming_lanes
                )

                record = {
                    "map": args.map_name,
                    "scenario": scenario.name,
                    "seed": args.seed,
                    "controller": "fixed_time",
                    "simulation_time": now,
                    "tls_id": tls_id,
                    "program_id": api.getProgram(tls_id),
                    "phase_id": api.getPhase(tls_id),
                    "phase_state": api.getRedYellowGreenState(tls_id),
                    "lane_queues": lane_queues,
                    "total_queue": sum(lane_queues.values()),
                    "total_waiting_time": waiting_time,
                }

                # Preserve the existing queue fields for the simple map.
                if args.map_name == "simple_intersection":
                    record["queues"] = {
                        "NS": sum(
                            lane_queues[lane]
                            for lane in (
                                "N_in_0", "N_in_1",
                                "S_in_0", "S_in_1",
                            )
                        ),
                        "EW": sum(
                            lane_queues[lane]
                            for lane in (
                                "E_in_0", "E_in_1",
                                "W_in_0", "W_in_1",
                            )
                        ),
                    }

                log_file.write(
                    json.dumps(record, ensure_ascii=False) + "\n"
                )
                next_sample_time += 5.0

            connection.simulationStep()
            now = connection.simulation.getTime()

            if now >= next_progress_time - 1e-8:
                print(f"Progress: {now:.1f}/{end_time:.1f} s")
                next_progress_time += 60.0

    print("Finished:", log_path)

finally:
    simulation.close()