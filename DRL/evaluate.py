"""V2 deterministic evaluation on shared held-out SUMO seeds."""
import argparse
from pathlib import Path

from stable_baselines3 import PPO

from .artifacts import ROOT, empty_directory, output_path, write_csv
from .gym_env import TrafficSignalEnv
from .metrics import SCENARIOS, HELD_OUT_SEEDS, METRICS, episode_summary, aggregate_episodes


def evaluate_scenario(model, scenario, seed, method='drl_ppo'):
    env = TrafficSignalEnv(scenario)
    rows = []
    try:
        observation, _ = env.reset(seed=seed)
        while True:
            action, _ = model.predict(observation, deterministic=True)
            observation, _, terminated, truncated, info = env.step(int(action))
            rows.append(dict(method=method, scenario=scenario, seed=seed,
                             simulation_time=info['sim_time'],
                             **{metric: info[metric] for metric in METRICS}))
            if terminated or truncated:
                break
    finally:
        env.close()
    return dict(scenario=scenario, seed=seed, rows=rows, summary=episode_summary(rows))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', type=Path, default=ROOT/'models/seed100/best_model/best_model.zip')
    parser.add_argument('--output-dir', type=Path, default=ROOT/'evaluation/seed100/best')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--seeds', type=int, nargs='+', default=None)
    group.add_argument('--seed', type=int, default=None)
    parser.add_argument('--method', choices=('drl_ppo', 'drl_ppo_final'), default='drl_ppo')
    args = parser.parse_args()
    seeds = args.seeds or ([args.seed] if args.seed is not None else list(HELD_OUT_SEEDS))
    if len(set(seeds)) != len(seeds) or any(seed < 0 for seed in seeds):
        parser.error('Evaluation seeds must be nonnegative and unique')
    if not args.model.is_file():
        parser.error(f'Model not found: {args.model}')
    if args.model.resolve() != output_path(args.model):
        parser.error('V2 evaluator requires a seed100 artifact')
    output = empty_directory(args.output_dir)
    model = PPO.load(args.model, device='cuda')
    if model.observation_space.shape != (12,):
        raise ValueError('V1 6D models are incompatible with V2; historical models were preserved')
    results = []
    for seed in seeds:
        for scenario in SCENARIOS:
            result = evaluate_scenario(model, scenario, seed, args.method)
            results.append(result)
            print(f'EVAL {args.method} {scenario} seed={seed} arrivals={result["summary"]["arrived_count"]}', flush=True)
    write_csv(output/'metrics.csv', [r for result in results for r in result['rows']])
    episodes = [result['summary'] for result in results]
    write_csv(output/'episodes.csv', episodes)
    write_csv(output/'summary.csv', aggregate_episodes(episodes))


if __name__ == '__main__':
    main()
