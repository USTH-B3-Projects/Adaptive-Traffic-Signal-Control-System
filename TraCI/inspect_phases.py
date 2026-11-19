
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from core.environment import Environment

with Environment(settings={"gui": False}) as env:
    state = env.reset("low", seed=42)

    tls_id = "J"
    api = env.connection.trafficlight

    # Get active traffic light program
    program_id = api.getProgram(tls_id)

    programs = api.getAllProgramLogics(tls_id)
    program = next(
        p for p in programs
        if p.programID == program_id
    )

    links = api.getControlledLinks(tls_id)

    print("\n=== TRAFFIC LIGHT PROGRAM ===")
    print("TLS:", tls_id)
    print("Program:", program_id)

    # Show all phases
    print("\n=== PHASE INFORMATION ===")

    for i, phase in enumerate(program.phases):
        green_indices = [
            j for j, signal in enumerate(phase.state)
            if signal in ("G", "g")
        ]

        print(f"\nPhase {i}")
        print("  State:", phase.state)
        print("  Duration:", phase.duration)
        print("  Green link indices:", green_indices)

        green_movements = set()

        for j in green_indices:
            for link in links[j]:
                if link:
                    incoming, outgoing, via = link
                    green_movements.add((incoming, outgoing))

        print("  Green movements:")
        for incoming, outgoing in sorted(green_movements):
            print(f"    {incoming} -> {outgoing}")

    # Show signal link mapping
    print("\n=== CONTROLLED LINKS ===")

    for i, group in enumerate(links):
        print(f"\nSignal Index {i}")

        for link in group:
            if link:
                incoming, outgoing, via = link
                print(f"  {incoming} -> {outgoing}")
