from pathlib import Path

from core.scenario_loader import (
    ScenarioLoader,
    load_settings,
    validate_settings,
)
from core.simulation import Simulation

ROOT = Path(__file__).resolve().parent

loader = ScenarioLoader(
    ROOT / "configs" / "scenarios_o_cho_dua.yaml"
)
scenario = loader.load("high")

settings = load_settings()
settings.update(gui=False, simulation_step=0.1)
settings = validate_settings(settings)

simulation = Simulation(settings)

try:
    connection = simulation.start(scenario, seed=57)
    api = connection.trafficlight

    print("\n=== SCENARIO ===")
    print("Config:", scenario.config_path)
    print("Network:", scenario.net_path)
    print("Routes:", scenario.route_paths)
    print("End:", scenario.end)

    tls_ids = api.getIDList()
    print("\n=== TRAFFIC LIGHTS ===")
    print("Number of TLS:", len(tls_ids))

    for tls_id in tls_ids:
        program_id = api.getProgram(tls_id)
        program = next(
            p for p in api.getAllProgramLogics(tls_id)
            if p.programID == program_id
        )
        links = api.getControlledLinks(tls_id)

        incoming_lanes = sorted({
            link[0]
            for group in links
            for link in group
            if link
        })

        print(f"\n=== TLS: {tls_id} ===")
        print("Program:", program_id)
        print("Program type:", program.type)
        print("Current phase:", api.getPhase(tls_id))
        print("Incoming lanes:")
        for lane in incoming_lanes:
            print(" ", lane)

        print("\nPhases:")
        for index, phase in enumerate(program.phases):
            print(
                f"\nPhase {index}: "
                f"duration={phase.duration}, state={phase.state}"
            )

            movements = sorted({
                (link[0], link[1])
                for signal_index, signal in enumerate(phase.state)
                if signal in ("G", "g")
                for link in links[signal_index]
                if link
            })

            for incoming, outgoing in movements:
                print(f"  {incoming} -> {outgoing}")

finally:
    simulation.close()