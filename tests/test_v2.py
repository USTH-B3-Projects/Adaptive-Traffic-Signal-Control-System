"""V2 semantic regression tests; no training or SUMO launch in this module."""
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import numpy as np

from DRL.artifacts import ROOT, output_path
from DRL.artifacts import write_csv
from DRL.core.environment import Environment
from DRL.gym_env import TrafficSignalEnv
from DRL.metrics import NS_LANES, EW_LANES, SCENARIOS, episode_summary, aggregate_episodes
from DRL.train_multiscenario import MultiScenarioEnv, ValidationEnv, linear_learning_rate
from DRL.train_multiscenario import FourScenarioEvalCallback
from RuleBased.rule_based_controller import choose_action


def state_fixture():
    lanes = {lane: dict(halting_count=4, vehicle_count=8, waiting_time=400., average_speed=6.95)
             for lane in NS_LANES}
    lanes.update({lane: dict(halting_count=0, vehicle_count=0, waiting_time=None, average_speed=None)
                  for lane in EW_LANES})
    return {'tls': {'J': dict(lanes=lanes, phase_id=0, green_elapsed=20., in_transition=False)}}


class V2Tests(unittest.TestCase):
    def test_directional_observation_reward_and_empty_speed(self):
        env = TrafficSignalEnv()
        state = state_fixture()
        expected = [16/60, 0, .4, 0, 1, 0, .5, 1, 1, 0, 20/75, 1]
        np.testing.assert_allclose(env._observation(state), expected, atol=1e-6)
        self.assertTrue(env.observation_space.contains(env._observation(state)))
        self.assertAlmostEqual(env._reward(state), -1.0112)
        for lane in state['tls']['J']['lanes'].values():
            lane['halting_count'] = 10000
            lane['waiting_time'] = 100000
        self.assertEqual(env._reward(state), -10.)
        self.assertTrue(np.all(env._observation(state) <= 1))

    def test_seed_passthrough(self):
        env = TrafficSignalEnv()
        env._environment = Mock()
        env._environment.reset.return_value = state_fixture()
        env.reset(seed=101)
        env._environment.reset.assert_called_once_with('low', seed=101)

    def test_balanced_cycles_and_heldout_exclusion(self):
        a, b = MultiScenarioEnv(100), MultiScenarioEnv(100)
        for _ in range(100):
            cycle = [a.next_episode() for _ in range(4)]
            self.assertEqual(cycle, [b.next_episode() for _ in range(4)])
            self.assertEqual({s for s, _ in cycle}, set(SCENARIOS))
            self.assertTrue(all(1000 <= seed < 1000000 for _, seed in cycle))

    def test_validation_restarts_with_all_scenarios_seed999(self):
        env = ValidationEnv()
        for _ in range(2):
            env.restart_cycle()
            self.assertEqual([env.next_episode() for _ in range(4)], [(s, 999) for s in SCENARIOS])
            env.next_episode()  # DummyVecEnv auto-reset must not rotate next evaluation.

    def test_repeated_eval_callback_keeps_monitor_writer_open(self):
        import csv
        import gymnasium as gym
        from stable_baselines3.common.monitor import Monitor
        from unittest.mock import patch

        class OneStepEnv(gym.Env):
            def __init__(self, scenario):
                self.scenario = scenario
            def reset(self, *, seed=None, options=None):
                self.seed_value = seed
                return np.zeros(12, dtype=np.float32), {}
            def step(self, action):
                return np.zeros(12, dtype=np.float32), -1., True, False, dict(
                    scenario=self.scenario, sumo_seed=self.seed_value)
            def close(self):
                pass

        base = ROOT/'results/seed100'
        with tempfile.TemporaryDirectory(prefix='_callback_test_', dir=base) as directory:
            self.assertEqual(Path(directory).resolve().parent, base.resolve())
            with patch('DRL.train_multiscenario.TrafficSignalEnv', OneStepEnv):
                monitor = Monitor(ValidationEnv(), filename=str(Path(directory)/'validation'),
                                  info_keywords=('scenario', 'sumo_seed'))
                callback = FourScenarioEvalCallback(monitor, n_eval_episodes=4, eval_freq=1, verbose=0)
                model = Mock()
                model.get_env.return_value = callback.eval_env
                model.get_vec_normalize_env.return_value = None
                model.num_timesteps = 1
                model.predict.side_effect = lambda obs, **kw: (np.zeros(len(obs), dtype=int), None)
                callback.init_callback(model)
                try:
                    callback.on_step()
                    callback.on_step()
                finally:
                    callback.eval_env.close()
            with (Path(directory)/'validation.monitor.csv').open() as stream:
                next(stream)
                rows = list(csv.DictReader(stream))
            self.assertEqual([r['scenario'] for r in rows], list(SCENARIOS)*2)
            self.assertTrue(all(r['sumo_seed'] == '999' for r in rows))

    def test_learning_rate_endpoints(self):
        self.assertAlmostEqual(linear_learning_rate(1), 3e-4)
        self.assertAlmostEqual(linear_learning_rate(0), 1e-5)
        self.assertAlmostEqual(linear_learning_rate(-.01), 1e-5)

    def test_rule_thresholds_come_from_settings(self):
        state = state_fixture()
        for lane in EW_LANES:
            state['tls']['J']['lanes'][lane]['halting_count'] = 10
        self.assertEqual(choose_action(state, dict(min_green=25, max_green=75)), 'KEEP')
        self.assertEqual(choose_action(state, dict(min_green=15, max_green=75)), 'SWITCH')

    def test_v1_paths_rejected(self):
        for path in ('models/seed710/test.zip', 'models/ppo_final.zip',
                     'results/comparison_result/drl_seed107_report.md', 'runs/ppo_overnight/test'):
            with self.assertRaises(ValueError):
                output_path(ROOT/path)

    def test_arrivals_are_summed_across_substeps(self):
        ticks = [0]
        api = SimpleNamespace(getTime=lambda: ticks[0]/10,
                              getMinExpectedNumber=lambda: 1,
                              getArrivedNumber=lambda: int(ticks[0] in (1, 27, 50)))
        conn = SimpleNamespace(simulation=api,
                               simulationStep=lambda: ticks.__setitem__(0, ticks[0]+1),
                               vehicle=SimpleNamespace(getIDCount=lambda: 2))
        env = Environment.__new__(Environment)
        env.simulation = SimpleNamespace(connection=conn)
        env.simulation.close = lambda: setattr(env.simulation, 'connection', None)
        env._done, env._end = False, 5.
        env.settings = dict(decision_interval=5.)
        env.scenario = SimpleNamespace(name='low')
        env.signals = SimpleNamespace(tls_ids=('J',), request=lambda actions, now:
            {'J': dict(requested_action='KEEP', executed_action='KEEP', override_reason=None)},
            advance=lambda now: [])
        env.extractor = SimpleNamespace(extract=lambda name, now: state_fixture())
        _, terminated, truncated, info = env.step('KEEP')
        self.assertEqual(info['arrived_count'], 3)
        self.assertEqual(ticks[0], 50)
        self.assertFalse(terminated)
        self.assertTrue(truncated)
        self.assertIsNone(env.connection)

    def test_arrival_episode_sum_and_sample_std(self):
        rows = [dict(method='drl_ppo', scenario='low', seed=101, simulation_time=t,
                     queue_length=1, waiting_time=10, average_speed=2,
                     arrived_count=count, vehicles_in_network=3)
                for t, count in ((5, 2), (10, 3))]
        episode = episode_summary(rows)
        self.assertEqual(episode['arrived_count'], 5)
        episodes = [dict(episode, seed=seed, arrived_count=count)
                    for seed, count in ((101, 4), (102, 5), (103, 6))]
        result = aggregate_episodes(episodes)[0]
        self.assertEqual(result['arrived_count_mean'], 5)
        self.assertEqual(result['arrived_count_std'], 1)

    def test_report_export_uses_episode_arrival_totals(self):
        import csv
        import json
        from unittest.mock import patch
        from generate_final_report import main as export_main
        base = ROOT/'results/seed100'
        base.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix='_export_test_', dir=base) as directory:
            directory = Path(directory).resolve()
            self.assertEqual(directory.parent, base.resolve())
            evaluation, results, models = (directory/p for p in ('evaluation', 'results', 'models'))
            results.mkdir()
            models.mkdir()
            for method in ('fixed_time', 'rule_based', 'drl_ppo', 'drl_ppo_final'):
                all_rows = []
                for scenario in SCENARIOS:
                    rows = [dict(method=method, scenario=scenario, seed=101, simulation_time=5*(i+1),
                                 queue_length=1, waiting_time=2, average_speed=3, arrived_count=1,
                                 vehicles_in_network=4) for i in range(720)]
                    if method in ('fixed_time', 'rule_based'):
                        write_csv(evaluation/'baselines'/method/'seed101'/f'metrics_{scenario}_seed101.csv', rows)
                    else:
                        all_rows.extend(rows)
                if all_rows:
                    write_csv(evaluation/('best' if method == 'drl_ppo' else 'final')/'metrics.csv', all_rows)
            (models/'training_metadata.json').write_text(json.dumps(dict(
                requested_timesteps=5760, actual_timesteps=5760, gpu='fixture only')))
            (results/'pipeline_timings.json').write_text('{}')
            report = results/'report.md'
            with patch('sys.argv', ['generate_final_report.py', '--evaluation-root', str(evaluation),
                       '--result-dir', str(results), '--model-root', str(models), '--output', str(report),
                       '--seeds', '101', '--dry-run']):
                export_main()
            with (results/'summary_final.csv').open() as stream:
                summary = list(csv.DictReader(stream))
            self.assertEqual(len(summary), 16)
            self.assertTrue(all(float(row['arrived_count_mean']) == 720 for row in summary))
            self.assertTrue((results/'plots/seed100_baseline_comparison.png').is_file())
            self.assertIn('DRY-RUN', report.read_text(encoding='utf-8'))


if __name__ == '__main__':
    unittest.main()
