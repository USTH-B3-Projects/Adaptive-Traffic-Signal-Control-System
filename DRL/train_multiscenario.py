"""Train one PPO policy while sampling all four SUMO demand scenarios."""
import argparse
from pathlib import Path

import gymnasium as gym
import numpy as np
from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import CheckpointCallback
from stable_baselines3.common.monitor import Monitor
from gymnasium import spaces

from .gym_env import TrafficSignalEnv


SCENARIOS = ("low", "medium", "high", "imbalance")


class MultiScenarioEnv(gym.Env):
    """Select a demand scenario on every episode reset."""

    metadata = {"render_modes": []}

    def __init__(self, seed: int):
        super().__init__()
        self._seed = seed
        self._episode = 0
        self._env = None
        self.action_space = spaces.Discrete(2)
        self.observation_space = spaces.Box(
            low=0.0, high=np.inf, shape=(6,), dtype=np.float32
        )

    def reset(self, *, seed=None, options=None):
        super().reset(seed=seed)
        scenario = SCENARIOS[int(self.np_random.integers(len(SCENARIOS)))]
        self._env = TrafficSignalEnv(scenario)
        episode_seed = self._seed + self._episode
        self._episode += 1
        return self._env.reset(seed=episode_seed)

    def step(self, action):
        if self._env is None:
            raise RuntimeError("reset must be called before step")
        return self._env.step(action)

    def close(self):
        if self._env is not None:
            self._env.close()
            self._env = None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=107)
    parser.add_argument("--timesteps", type=int, default=800_000)
    parser.add_argument("--model", type=Path, default=Path("models/ppo_final"))
    parser.add_argument("--log-dir", type=Path, default=Path("runs/ppo_overnight"))
    parser.add_argument(
        "--checkpoint-dir", type=Path, default=Path("models/checkpoints")
    )
    args = parser.parse_args()
    if args.seed < 0 or args.timesteps <= 0:
        parser.error("--seed must be nonnegative and --timesteps must be positive")

    args.log_dir.mkdir(parents=True, exist_ok=True)
    args.checkpoint_dir.mkdir(parents=True, exist_ok=True)
    env = Monitor(MultiScenarioEnv(args.seed))
    callback = CheckpointCallback(
        save_freq=50_000,
        save_path=str(args.checkpoint_dir),
        name_prefix="ppo_multiscenario",
    )
    model = PPO(
        "MlpPolicy",
        env,
        seed=args.seed,
        verbose=1,
        tensorboard_log=str(args.log_dir),
    )
    try:
        model.learn(total_timesteps=args.timesteps, callback=callback)
        model.save(str(args.model))
    finally:
        env.close()
    print(f"Saved model: {args.model}.zip")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
