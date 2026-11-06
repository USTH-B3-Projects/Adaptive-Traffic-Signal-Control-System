"""Run a short TraCI smoke test against one SUMO traffic scenario."""
import argparse
import csv
import os
from pathlib import Path
import shutil
import statistics
import sys

import traci


ROOT = Path(__file__).resolve().parents[1]
SCENARIOS = {
    "low": ROOT / "SUMO" / "Map_Nga_tu" / "Map_Low" / "simulation.sumocfg",
    "medium": ROOT / "SUMO" / "Map_Nga_tu" / "Map_Medium" / "simulation.sumocfg",
    "high": ROOT / "SUMO" / "Map_Nga_tu" / "Map_High" / "simulation.sumocfg",
    "imbalance": ROOT / "SUMO" / "Map_Nga_tu" / "Map_Imbalance" / "simulation.sumocfg",
}


def find_sumo() -> str:
    binary = shutil.which("sumo")
    if binary:
        return binary
    sumo_home = os.environ.get("SUMO_HOME")
    if sumo_home:
        candidate = Path(sumo_home) / "bin" / "sumo.exe"
        if candidate.is_file():
            return str(candidate)
    raise FileNotFoundError(
        "Cannot find sumo.exe. Check SUMO_HOME or add SUMO/bin to PATH."
    )


def incoming_lanes() -> tuple[str, ...]:
    lanes = {
        link[0]
        for tls_id in traci.trafficlight.getIDList()
        for group in traci.trafficlight.getControlledLinks(tls_id)
        for link in group
        if link
    }
    if not lanes:
        raise RuntimeError("The scenario has no traffic-light-controlled incoming lanes.")
    return tuple(sorted(lanes))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenario", choices=SCENARIOS, default="low")
    parser.add_argument("--steps", type=int, default=100)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.steps <= 0:
        parser.error("--steps must be positive")

    config = SCENARIOS[args.scenario]
    output = args.output or ROOT / "TraCI" / "outputs" / f"queue_{args.scenario}.csv"
    output.parent.mkdir(parents=True, exist_ok=True)
    sumo = find_sumo()
    traci.start([sumo, "-c", str(config), "--seed", "42"])

    try:
        lanes = incoming_lanes()
        with output.open("w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(
                file,
                fieldnames=(
                    "step",
                    "simulation_time",
                    "queue_length",
                    "waiting_time",
                    "average_speed",
                    "arrived_count",
                    "vehicles_in_network",
                ),
            )
            writer.writeheader()
            for step in range(1, args.steps + 1):
                traci.simulationStep()
                lane_queue = sum(
                    traci.lane.getLastStepHaltingNumber(lane) for lane in lanes
                )
                lane_waiting = sum(traci.lane.getWaitingTime(lane) for lane in lanes)
                speeds = [
                    traci.vehicle.getSpeed(vehicle_id)
                    for vehicle_id in traci.vehicle.getIDList()
                ]
                writer.writerow(
                    {
                        "step": step,
                        "simulation_time": traci.simulation.getTime(),
                        "queue_length": lane_queue,
                        "waiting_time": lane_waiting,
                        "average_speed": statistics.fmean(speeds) if speeds else 0.0,
                        "arrived_count": traci.simulation.getArrivedNumber(),
                        "vehicles_in_network": traci.vehicle.getIDCount(),
                    }
                )
    finally:
        traci.close()

    print(f"Scenario: {args.scenario}")
    print(f"Steps: {args.steps}")
    print(f"CSV: {output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
