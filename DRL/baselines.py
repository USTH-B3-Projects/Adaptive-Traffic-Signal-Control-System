"""Comparable baseline episodes, sampled after each complete decision interval."""
import argparse
from pathlib import Path

from .artifacts import ROOT, output_path, write_csv
from .core.environment import Environment
from .core.scenario_loader import ScenarioLoader, load_settings
from .core.simulation import Simulation
from .core.state_extractor import StateExtractor
from .metrics import SCENARIOS, traffic_row, episode_summary


class FixedSignals:
    """Snapshot-only adapter: never take ownership of the static SUMO program."""
    tls_ids = ('J',)

    def __init__(self, connection):
        self.connection = connection

    def snapshot(self, tls, now):
        api = self.connection.trafficlight
        phase = api.getPhase(tls)
        return dict(phase_id=phase, phase_state=api.getRedYellowGreenState(tls),
                    green_elapsed=api.getSpentDuration(tls) if phase in (0, 1, 4, 5) else 0,
                    in_transition=phase not in (0, 1, 4, 5))


def fixed_episode(scenario_name, seed):
    settings = load_settings()
    scenario = ScenarioLoader().load(scenario_name)
    simulation = Simulation(settings)
    rows = []
    try:
        connection = simulation.start(scenario, seed=seed)
        extractor = StateExtractor(connection, FixedSignals(connection))
        end = scenario.end
        if settings['max_episode_seconds'] is not None:
            cap = scenario.begin + settings['max_episode_seconds']
            end = min(end, cap) if end is not None else cap
        if end is None:
            raise ValueError('Fixed-time requires a finite episode end')
        now = connection.simulation.getTime()
        while now < end - 1e-8 and connection.simulation.getMinExpectedNumber():
            deadline = min(now + settings['decision_interval'], end)
            arrived = 0
            while now < deadline - 1e-8:
                connection.simulationStep()
                now = connection.simulation.getTime()
                arrived += connection.simulation.getArrivedNumber()
                if connection.simulation.getMinExpectedNumber() == 0:
                    break
            state = extractor.extract(scenario_name, now)
            info = dict(sim_time=now, arrived_count=arrived,
                        vehicles_in_network=connection.vehicle.getIDCount())
            rows.append(traffic_row(state, info, seed, 'fixed_time'))
        return rows
    finally:
        simulation.close()


def rule_episode(scenario, seed):
    from RuleBased.rule_based_controller import choose_action
    rows = []
    with Environment() as env:
        state = env.reset(scenario, seed=seed)
        while True:
            action = choose_action(state, settings=env.settings)
            state, terminated, truncated, info = env.step(action)
            rows.append(traffic_row(state, info, seed, 'rule_based'))
            if terminated or truncated:
                break
    return rows


def main(method):
    parser = argparse.ArgumentParser(description=f'V2 {method} baseline')
    parser.add_argument('--scenario', choices=SCENARIOS, required=True)
    parser.add_argument('--seed', type=int, required=True)
    parser.add_argument('--output-dir', type=Path)
    args = parser.parse_args()
    output = output_path(args.output_dir or ROOT/f'evaluation/seed100/baselines/{method}/seed{args.seed}')
    print(f'START {method} {args.scenario} SUMO seed={args.seed}', flush=True)
    rows = (fixed_episode if method == 'fixed_time' else rule_episode)(args.scenario, args.seed)
    stem = f'{args.scenario}_seed{args.seed}'
    write_csv(output/f'metrics_{stem}.csv', rows)
    write_csv(output/f'episode_{stem}.csv', [episode_summary(rows)])
    print(f'DONE {method} {stem}: {len(rows)} samples; arrivals={sum(r["arrived_count"] for r in rows)}', flush=True)
