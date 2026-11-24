"""V2 balanced training and fixed-seed four-scenario validation."""
import argparse
import csv
import json
import math
from pathlib import Path

import gymnasium as gym
import numpy as np
import torch
from gymnasium import spaces
from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import CheckpointCallback, EvalCallback
from stable_baselines3.common.monitor import Monitor

from .artifacts import ROOT, empty_directory, output_path
from .gym_env import TrafficSignalEnv
from .metrics import SCENARIOS

N_STEPS = 2880
VAL_SEED = 999


def linear_learning_rate(progress_remaining):
    return 1e-5 + (3e-4 - 1e-5) * float(np.clip(progress_remaining, 0.0, 1.0))


def require_cuda():
    if not torch.cuda.is_available():
        raise RuntimeError(f'CUDA unavailable: torch={torch.__version__}')
    name = torch.cuda.get_device_name(0)
    print(f'CUDA ready: {name}; torch={torch.__version__}', flush=True)
    # Exercise allocation/kernel before a long baseline run starts.
    torch.ones(1, device='cuda').add_(1)
    torch.cuda.synchronize()
    return name


class MultiScenarioEnv(gym.Env):
    metadata = {'render_modes': []}

    def __init__(self, seed=100, episode_log=None):
        super().__init__()
        self._seed = seed
        self.rng = np.random.default_rng(seed)
        self._cycle = []
        self._episode = 0
        self._env = None
        self.episode_log = Path(episode_log) if episode_log else None
        self.action_space = spaces.Discrete(2)
        self.observation_space = spaces.Box(0.0, 1.0, shape=(12,), dtype=np.float32)

    def next_episode(self):
        if not self._cycle:
            self._cycle = list(self.rng.permutation(SCENARIOS))
        scenario = str(self._cycle.pop(0))
        traffic_seed = int(self.rng.integers(1000, 1_000_000))
        return scenario, traffic_seed

    def reset(self, *, seed=None, options=None):
        super().reset(seed=seed)
        self.close()
        if seed is not None:
            self.rng = np.random.default_rng(seed)
            self._cycle = []
            self._episode = 0
        scenario, traffic_seed = self.next_episode()
        self._env = TrafficSignalEnv(scenario)
        try:
            observation, info = self._env.reset(seed=traffic_seed)
            self._episode += 1
            info.update(episode=self._episode)
            if self.episode_log:
                with self.episode_log.open('a', encoding='utf-8') as stream:
                    stream.write(json.dumps(info) + '\n')
            return observation, info
        except BaseException:
            self.close()
            raise

    def step(self, action):
        if self._env is None:
            raise RuntimeError('reset must be called before step')
        return self._env.step(action)

    def close(self):
        if self._env is not None:
            self._env.close()
            self._env = None


class ValidationEnv(MultiScenarioEnv):
    """Exactly one low/medium/high/imbalance per validation, all seed999."""

    def __init__(self):
        super().__init__(VAL_SEED)
        self.position = 0

    def restart_cycle(self):
        self.close()
        self.position = 0

    def close_simulation(self):
        # Deliberately distinct from Monitor.close(), which also closes its CSV.
        self.close()

    def next_episode(self):
        scenario = SCENARIOS[self.position % len(SCENARIOS)]
        self.position += 1
        return scenario, VAL_SEED


class FourScenarioEvalCallback(EvalCallback):
    def _on_step(self):
        due = self.eval_freq > 0 and self.n_calls % self.eval_freq == 0
        if due:
            # evaluate_policy/DummyVecEnv auto-reset once after its last episode.
            # Restart explicitly so that this extra reset cannot rotate scenarios.
            self.eval_env.env_method('restart_cycle')
        try:
            return super()._on_step()
        finally:
            if due:
                self.eval_env.env_method('close_simulation')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--seed', type=int, default=100)
    parser.add_argument('--timesteps', type=int, default=600000)
    parser.add_argument('--device', choices=('cuda',), default='cuda')
    parser.add_argument('--model-root', type=Path, default=ROOT/'models/seed100')
    parser.add_argument('--log-dir', type=Path, default=ROOT/'runs/ppo_seed100')
    parser.add_argument('--validation-dir', type=Path, default=ROOT/'evaluation/seed100/validation')
    parser.add_argument('--checkpoint-freq', type=int, default=28800)
    parser.add_argument('--eval-freq', type=int, default=28800)
    args = parser.parse_args()
    if args.seed != 100 or args.timesteps <= 0:
        parser.error('V2 pipeline uses training seed100 and a positive budget')
    if min(args.eval_freq, args.checkpoint_freq) <= 0 or args.eval_freq > args.timesteps:
        parser.error('Callback frequencies must be positive and evaluation must occur during training')
    gpu = require_cuda()
    model_root = empty_directory(args.model_root)
    log_dir = empty_directory(args.log_dir)
    validation_dir = empty_directory(args.validation_dir)
    checkpoint_dir = empty_directory(model_root/'checkpoints')
    best_dir = empty_directory(model_root/'best_model')
    env = Monitor(MultiScenarioEnv(args.seed, log_dir/'training_episodes.jsonl'),
                  filename=str(log_dir/'train'), info_keywords=('scenario', 'sumo_seed'))
    validation = Monitor(ValidationEnv(), filename=str(validation_dir/'episodes'),
                         info_keywords=('scenario', 'sumo_seed'))
    model = None
    try:
        callbacks = [
            CheckpointCallback(save_freq=args.checkpoint_freq,
                               save_path=str(checkpoint_dir), name_prefix='ppo_seed100'),
            FourScenarioEvalCallback(validation, n_eval_episodes=4, eval_freq=args.eval_freq,
                                     deterministic=True, best_model_save_path=str(best_dir),
                                     log_path=str(validation_dir)),
        ]
        model = PPO(
            policy='MlpPolicy', env=env,
            learning_rate=linear_learning_rate,
            n_steps=N_STEPS, batch_size=96, n_epochs=5,
            gamma=0.99, gae_lambda=0.95, clip_range=0.2, clip_range_vf=None,
            ent_coef=0.01, vf_coef=0.5, max_grad_norm=0.5, target_kl=0.02,
            normalize_advantage=True,
            policy_kwargs=dict(net_arch=dict(pi=[128, 128], vf=[128, 128]), activation_fn=torch.nn.Tanh),
            use_sde=False, sde_sample_freq=-1, stats_window_size=100,
            rollout_buffer_class=None, rollout_buffer_kwargs=None,
            device='cuda', seed=args.seed, verbose=1, tensorboard_log=str(log_dir),
        )
        model.learn(total_timesteps=args.timesteps, callback=callbacks)
        model.save(str(output_path(model_root/'ppo_seed100_final.zip')))
        if not (best_dir/'best_model.zip').is_file():
            raise RuntimeError('Validation never produced best_model.zip')
        with (log_dir/'train.monitor.csv').open(encoding='utf-8') as stream:
            next(stream)  # SB3 Monitor JSON header
            completed_episodes = list(csv.DictReader(stream))
        metadata = dict(version='V2', seed=args.seed, requested_timesteps=args.timesteps,
                        actual_timesteps=model.num_timesteps, n_steps=N_STEPS,
                        expected_rollouts=math.ceil(args.timesteps/N_STEPS),
                        completed_training_episodes=len(completed_episodes),
                        validation_seed=VAL_SEED, held_out_seeds=[101, 102, 103], gpu=gpu,
                        observation_shape=[12], training_seed_range=[1000, 999999],
                        best_selection='maximum four-scenario mean validation reward',
                        learning_rate_start=3e-4, learning_rate_end=1e-5)
        (model_root/'training_metadata.json').write_text(json.dumps(metadata, indent=2), encoding='utf-8')
        print(f'Saved V2 final and best model under {model_root}', flush=True)
    finally:
        env.close()
        validation.close()


if __name__ == '__main__':
    main()
