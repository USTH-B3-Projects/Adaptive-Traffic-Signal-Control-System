from pathlib import Path
import argparse
import json
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "TraCI"))

from core.scenario_loader import (
    ScenarioLoader,
    load_settings,
    validate_settings,
)
from core.simulation import Simulation


SCENARIO_FILES = {
    "simple_intersection": "scenarios_simple_intersection.yaml",
    "o_cho_dua": "scenarios_o_cho_dua.yaml",
    "bigc_thang_long": "scenarios_bigc_thang_long.yaml",
}

DEFAULT_TLS = {
    "simple_intersection": ["J"],
    "o_cho_dua": [
        "joinedS_5707161152_6677677155_"
        "6677677160_6677677161_#2more"
    ],
    "bigc_thang_long": [
        "1314185677",
        "1314191420",
        "4539674875",
        "4539674879",
    ],
}


def get_lane_metrics(connection, lanes):
    queues = {
        lane: connection.lane.getLastStepHaltingNumber(lane)
        for lane in lanes
    }

    waiting = sum(
        connection.lane.getWaitingTime(lane)
        for lane in lanes
    )

    return queues, waiting


def main():
    parser = argparse.ArgumentParser(
        description="Run the fixed-time baseline."
    )
    parser.add_argument(
        "--map",
        dest="map_name",
        choices=list(SCENARIO_FILES),
        default="simple_intersection",
    )
    parser.add_argument(
        "--scenario",
        choices=["low", "medium", "high", "imbalance"],
        required=True,
    )
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument(
        "--duration",
        type=int,
        default=None,
        help="Trial duration; omit to use scenario end.",
    )
    parser.add_argument(
        "--tls-id",
        default=None,
        help="Observe one TLS instead of the default map scope.",
    )

    args = parser.parse_args()

    if args.duration is not None and args.duration <= 0:
        parser.error("--duration must be positive.")

    tls_ids = (
        [args.tls_id]
        if args.tls_id
        else DEFAULT_TLS[args.map_name]
    )

    settings = load_settings()
    settings.update({
        "gui": False,
        "simulation_step": 0.1,
        "seed": args.seed,
    })
    settings = validate_settings(settings)

    loader = ScenarioLoader(
        ROOT / "TraCI" / "configs"
        / SCENARIO_FILES[args.map_name]
    )
    scenario = loader.load(args.scenario)

    end_limits = []

    if scenario.end is not None:
        end_limits.append(scenario.end)

    if args.duration is not None:
        end_limits.append(scenario.begin + args.duration)

    if not end_limits:
        parser.error(
            "Scenario has no end time; provide --duration."
        )

    end_time = min(end_limits)

    if end_time <= scenario.begin:
        parser.error("End time must be after scenario begin.")

    log_dir = (
        ROOT / "FixedTime" / "logs"
        / args.map_name / f"seed{args.seed}"
    )

    filename = (
        f"fixed_time_{args.scenario}_seed{args.seed}"
    )

    if args.duration is not None:
        log_dir /= "trials"
        filename += f"_{args.duration}s"

    log_path = log_dir / f"{filename}.jsonl"

    if log_path.exists():
        parser.error(f"Log already exists: {log_path}")

    simulation = Simulation(settings)

    try:
        connection = simulation.start(
            scenario, seed=args.seed
        )
        api = connection.trafficlight
        available_tls = set(api.getIDList())
        lanes_by_tls = {}

        for tls_id in tls_ids:
            if tls_id not in available_tls:
                raise ValueError(
                    f"Unknown TLS {tls_id}; "
                    f"available: {sorted(available_tls)}"
                )

            program_id = api.getProgram(tls_id)
            programs = [
                program
                for program in api.getAllProgramLogics(tls_id)
                if program.programID == program_id
            ]

            if len(programs) != 1 or programs[0].type != 0:
                raise ValueError(
                    f"{tls_id}: FT requires an active "
                    "static program."
                )

            lanes_by_tls[tls_id] = sorted({
                link[0]
                for group in api.getControlledLinks(tls_id)
                for link in group
                if link
            })

            if not lanes_by_tls[tls_id]:
                raise ValueError(
                    f"{tls_id}: no controlled incoming lanes."
                )

            print(f"\nTLS: {tls_id}")
            print("Program:", program_id)
            print("Incoming lanes:", lanes_by_tls[tls_id])

            for index, phase in enumerate(programs[0].phases):
                print(
                    f"Phase {index}: "
                    f"duration={phase.duration}, "
                    f"state={phase.state}"
                )

        # Union of lanes: count each lane only once.
        all_lanes = sorted({
            lane
            for lanes in lanes_by_tls.values()
            for lane in lanes
        })

        print("\nMap:", args.map_name)
        print("Scenario:", args.scenario)
        print("TLS count:", len(tls_ids))
        print("Unique incoming lanes:", len(all_lanes))
        print(
            f"Simulation window: "
            f"{scenario.begin} -> {end_time}"
        )
        print("Writing log:", log_path)

        log_dir.mkdir(parents=True, exist_ok=True)

        with log_path.open("x", encoding="utf-8") as log_file:
            next_sample_time = connection.simulation.getTime()
            next_progress_time = next_sample_time + 60
            sample_count = 0

            while connection.simulation.getTime() < end_time - 1e-8:
                now = connection.simulation.getTime()

                if now >= next_sample_time - 1e-8:
                    lane_queues, waiting = get_lane_metrics(
                        connection, all_lanes
                    )

                    tls_records = {}

                    for tls_id in tls_ids:
                        local_queues, local_waiting = (
                            get_lane_metrics(
                                connection,
                                lanes_by_tls[tls_id],
                            )
                        )

                        tls_records[tls_id] = {
                            "program_id": api.getProgram(tls_id),
                            "phase_id": api.getPhase(tls_id),
                            "phase_state": (
                                api.getRedYellowGreenState(tls_id)
                            ),
                            "lane_queues": local_queues,
                            "total_queue": sum(local_queues.values()),
                            "total_waiting_time": local_waiting,
                        }

                    record = {
                        "map": args.map_name,
                        "scenario": scenario.name,
                        "seed": args.seed,
                        "controller": "fixed_time",
                        "simulation_time": now,
                        "tls_ids": tls_ids,
                        "tls": tls_records,
                        "lane_queues": lane_queues,
                        "total_queue": sum(lane_queues.values()),
                        "total_waiting_time": waiting,
                    }

                    # Preserve existing fields for single-TLS runs.
                    if len(tls_ids) == 1:
                        tls_id = tls_ids[0]
                        record["tls_id"] = tls_id
                        record.update(tls_records[tls_id])

                    if args.map_name == "simple_intersection":
                        record["queues"] = {
                            "NS": sum(
                                lane_queues[f"{direction}_in_{i}"]
                                for direction in ("N", "S")
                                for i in (0, 1)
                            ),
                            "EW": sum(
                                lane_queues[f"{direction}_in_{i}"]
                                for direction in ("E", "W")
                                for i in (0, 1)
                            ),
                        }

                    log_file.write(
                        json.dumps(record, ensure_ascii=False)
                        + "\n"
                    )

                    sample_count += 1
                    next_sample_time += 5.0

                connection.simulationStep()
                now = connection.simulation.getTime()

                if now >= next_progress_time - 1e-8:
                    print(
                        f"Progress: {now:.1f}/{end_time:.1f} s"
                    )
                    next_progress_time += 60

        print("Samples:", sample_count)
        print("Finished:", log_path)

    finally:
        simulation.close()


if __name__ == "__main__":
    main()