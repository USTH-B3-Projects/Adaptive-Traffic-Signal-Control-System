from pathlib import Path
import sys
import json
import argparse

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "TraCI"))

from core.scenario_loader import ScenarioLoader, load_settings, validate_settings
from core.simulation import Simulation

parser = argparse.ArgumentParser(description="Fixed-time baseline on O Cho Dua")
parser.add_argument("--scenario", choices=["ocd_low","ocd_medium","ocd_high", "ocd_imbalance"], required=True)
parser.add_argument("--seed", type=int, required=True)
args = parser.parse_args()
END_TIME = {"ocd_low": 3600,"ocd_medium": 3600,"ocd_high": 3600, "ocd_imbalance": 10800}
end_time = END_TIME[args.scenario]

log_dir = ROOT / "FixedTime" / "logs_ochodua" / f"seed{args.seed}"
log_dir.mkdir(parents=True, exist_ok=True)

settings = validate_settings(
    load_settings() | {"gui": False, "simulation_step": 0.1}
)

loader = ScenarioLoader()
scenario = loader.load(args.scenario)
simulation = Simulation(settings)

MAIN_TLS = "joinedS_5707161152_6677677155_6677677160_6677677161_#2more"

log_path = log_dir / f"fixed_time_{args.scenario}_seed{args.seed}.jsonl"
print(f"Running fixed-time O Cho Dua: scenario={args.scenario}, seed={args.seed}")
print(f"Log: {log_path}")

try:
    connection = simulation.start(scenario, seed=args.seed)

    controlled_links = connection.trafficlight.getControlledLinks(MAIN_TLS)
    incoming_lanes = list(dict.fromkeys(
        link[0] for group in controlled_links for link in group
    ))
    print(f"Main TLS: {MAIN_TLS}")
    print(f"Incoming lanes: {len(incoming_lanes)}")

    with open(log_path, "w", encoding="utf-8") as log_file:
        next_sample = 0.0
        next_progress = 600.0

        while connection.simulation.getTime() < end_time:
            now = connection.simulation.getTime()

            if now >= next_sample - 1e-8:
                phase_id = connection.trafficlight.getPhase(MAIN_TLS)

                total_queue = 0
                total_waiting = 0.0
                for lane_id in incoming_lanes:
                    total_queue += connection.lane.getLastStepHaltingNumber(lane_id)
                    total_waiting += connection.lane.getWaitingTime(lane_id)

                record = {
                    "scenario": args.scenario,
                    "seed": args.seed,
                    "controller": "fixed_time",
                    "simulation_time": now,
                    "tls_id": MAIN_TLS,
                    "phase_id": phase_id,
                    "queues": {"total": total_queue},
                    "total_waiting_time": total_waiting,
                }
                log_file.write(json.dumps(record, ensure_ascii=False) + "\n")
                next_sample += 5.0

            connection.simulationStep()

            if connection.simulation.getTime() >= next_progress - 1e-8:
                print(f"Progress: {connection.simulation.getTime():.0f}/{end_time} s")
                next_progress += 600.0

finally:
    simulation.close()
    print("Done.")