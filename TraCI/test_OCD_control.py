from pathlib import Path

from core.environment import Environment

ROOT = Path(__file__).resolve().parent

TLS_ID = (
    "joinedS_5707161152_6677677155_"
    "6677677160_6677677161_#2more"
)

with Environment(
    scenarios_path=ROOT / "configs" / "scenarios_o_cho_dua.yaml",
    settings={
        "gui": False,
        "simulation_step": 0.1,
        "decision_interval": 5,
        "min_green": 30,
        "max_green": 75,
        "max_episode_seconds": 200,
    },
    tls_ids=[TLS_ID],
    green_phases_by_tls={
        TLS_ID: [0, 2, 5, 7],
    },
) as env:
    state = env.reset("high", seed=57)

    assert set(state["tls"]) == {TLS_ID}
    print("Controlled TLS:", list(state["tls"]))

    while True:
        now = state["simulation_time"]
        tls = state["tls"][TLS_ID]

        # Request SWITCH at all action
        state, terminated, truncated, info = env.step("KEEP")

        print(
            f"t={now:6.1f} | "
            f"phase={tls['phase_id']} | "
            f"green={tls['green_elapsed']:5.1f} | "
            f"transition={tls['in_transition']} | "
            f"executed={info['executed_action'][TLS_ID]} | "
            f"reason={info['override_reason'][TLS_ID]} | "
            f"next_phase={state['tls'][TLS_ID]['phase_id']}"
        )

        # Print the self-phase transitions between the two decisive moments.
        for event in info["automatic_events"]:
            print(
                f"  AUTO t={event['sim_time']:.1f}: "
                f"{event['override_reason']}"
            )

        if terminated or truncated:
            print(
                "Finished:",
                state["simulation_time"],
                info["end_reason"],
            )
            break