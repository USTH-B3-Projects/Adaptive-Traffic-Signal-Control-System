from pathlib import Path
import sys
import json

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "TraCI"))
log_dir = ROOT / "FixedTime" / "logs"
log_dir.mkdir(parents=True, exist_ok=True)

from core.scenario_loader import ScenarioLoader, load_settings, validate_settings
from core.simulation import Simulation

settings = load_settings()

settings["gui"] = False
settings["simulation_step"] = 0.1
settings = validate_settings(settings)

loader = ScenarioLoader()
scenario = loader.load("high")
simulation = Simulation(settings)

def get_fixed_time_queues(connection):
    lanes = connection.lane
    ns_lanes = ["N_in_0", "N_in_1", "S_in_0", "S_in_1"]
    ew_lanes = ["E_in_0", "E_in_1", "W_in_0", "W_in_1"]

    queue_ns = 0
    for lane_id in ns_lanes:
        queue_ns += lanes.getLastStepHaltingNumber(lane_id)

    queue_ew = 0
    for lane_id in ew_lanes:
        queue_ew += lanes.getLastStepHaltingNumber(lane_id)

    return {"NS": queue_ns, "EW": queue_ew}

def get_total_waiting_time(connection):
    incoming_lanes = [
        "N_in_0", "N_in_1", "S_in_0", "S_in_1",
        "E_in_0", "E_in_1", "W_in_0", "W_in_1"
    ]
    return sum(connection.lane.getWaitingTime(lane_id)
               for lane_id in incoming_lanes)

try:
    connection = simulation.start(scenario, seed=42)
    print("Initial phase:", connection.trafficlight.getPhase("J"))

    with open(log_dir / "fixed_time_high_seed42.jsonl", "w", encoding="utf-8") as log_file:
        next_sample_time = 0.0
        next_progress_time = 60.0
        while connection.simulation.getTime() < 3600:
            now = connection.simulation.getTime()

            if now >= next_sample_time - 1e-8:
                record = {
                    "scenario": scenario.name,
                    "controller": "fixed_time",
                    "simulation_time": now,
                    "phase_id": connection.trafficlight.getPhase("J"),
                    "queues": get_fixed_time_queues(connection),
                    "total_waiting_time": get_total_waiting_time(connection),
                }
                log_file.write(json.dumps(record, ensure_ascii=False) + "\n")
                next_sample_time += 5

            connection.simulationStep()
            now = connection.simulation.getTime()

            if now >= next_progress_time - 1e-8:
                print(f"Progress: {now:.0f}/3600 s")
                next_progress_time += 60

finally:
    simulation.close()