import argparse
import csv
import json
import os
import platform
import sys
from importlib import metadata

import numpy as np
from stable_baselines3 import DQN
from stable_baselines3.common.callbacks import BaseCallback
from stable_baselines3.common.monitor import Monitor

from traffic_gym import MAPS, REWARDS, TEST_SEEDS, TrafficEnv, default_scales


def version(pkg):
    try:
        return metadata.version(pkg)
    except metadata.PackageNotFoundError:
        return None


p = argparse.ArgumentParser()
p.add_argument("--map", default="simple_intersection", choices=list(MAPS),
               help="simple_intersection = Map_Nga_Tu (default), o_cho_dua = O_Cho_Dua")
p.add_argument("--scenario", default="low", choices=["low", "medium", "high", "imbalance"])
p.add_argument("--seed", type=int, default=0, help="seed of the DRL algorithm")
p.add_argument("--steps", type=int, default=100_000)
p.add_argument("--train-seeds", type=int, nargs="+", default=list(range(10)),
               help="SUMO traffic seeds sampled during training (must not include 57, 367, 1024)")
p.add_argument("--val-seeds", type=int, nargs="+", default=[100, 101, 102],
               help="SUMO traffic seeds used to pick the best model (not the test seeds)")
p.add_argument("--eval-freq", type=int, default=10_000,
               help="validation every N training steps (0 = no validation, no best model)")
p.add_argument("--reward", default="total_wait", choices=REWARDS)
p.add_argument("--q-scale", type=float, default=None, help="observation scale of queue per direction group / stage (default: 20, o_cho_dua 60)")
p.add_argument("--v-scale", type=float, default=None, help="observation scale of vehicles per direction group / stage (default: 30, o_cho_dua 100)")
p.add_argument("--w-scale", type=float, default=None, help="observation scale of wait per vehicle, s (default: 60, o_cho_dua 120)")
p.add_argument("--learning-rate", type=float, default=1e-3)
p.add_argument("--target-update-interval", type=int, default=500)
p.add_argument("--eps-final", type=float, default=0.05)
p.add_argument("--tag", default="", help="suffix added to output names, e.g. --tag v2a gives dqn_high_seed0_v2a_*")
args = p.parse_args()

if set(args.train_seeds) & set(TEST_SEEDS):
    p.error(f"train seeds must not include the test seeds {TEST_SEEDS}")
if set(args.val_seeds) & set(TEST_SEEDS):
    p.error(f"validation seeds must not include the test seeds {TEST_SEEDS}")
if set(args.val_seeds) & set(args.train_seeds):
    p.error("validation seeds must differ from the train seeds")

name = f"dqn_{args.scenario}_seed{args.seed}" + (f"_{args.tag}" if args.tag else "")
os.makedirs("logs", exist_ok=True)


class BestModelCallback(BaseCallback):
    """Run the current policy (greedy) on the validation seeds, keep the best model."""

    def __init__(self, eval_env, val_seeds, eval_freq, best_path, csv_path):
        super().__init__()
        self.eval_env, self.val_seeds, self.eval_freq = eval_env, val_seeds, eval_freq
        self.best_path, self.csv_path = best_path, csv_path
        self.best = -np.inf

    def _validate(self):
        returns = []
        for s in self.val_seeds:
            obs, _ = self.eval_env.reset(options={"sumo_seed": s})
            done, total = False, 0.0
            while not done:
                action = int(self.model.predict(obs, deterministic=True)[0])
                obs, reward, terminated, truncated, _ = self.eval_env.step(action)
                total += reward
                done = terminated or truncated
            returns.append(total)
        score = float(np.mean(returns))
        is_best = score > self.best
        if is_best:
            self.best = score
            self.model.save(self.best_path)
        with open(self.csv_path, "a", newline="") as f:
            csv.writer(f).writerow([self.num_timesteps, f"{score:.3f}", int(is_best)])
        print(f"[validation] step {self.num_timesteps}: return {score:.2f} "
              f"(best {self.best:.2f}){' *' if is_best else ''}", flush=True)

    def _on_training_start(self):
        with open(self.csv_path, "w", newline="") as f:
            csv.writer(f).writerow(["step", "val_return", "is_best"])

    def _on_step(self):
        if self.n_calls % self.eval_freq == 0:
            self._validate()
        return True

    def _on_training_end(self):
        if self.num_timesteps % self.eval_freq != 0:
            self._validate()


_defaults = default_scales(args.map)
scales = (args.q_scale or _defaults[0], args.v_scale or _defaults[1], args.w_scale or _defaults[2])
env = Monitor(TrafficEnv(args.scenario, traffic_seeds=args.train_seeds, reward=args.reward,
                         scales=scales, map_name=args.map),
              f"logs/{name}")
eval_env = (TrafficEnv(args.scenario, reward=args.reward, scales=scales, map_name=args.map)
            if args.eval_freq > 0 else None)

model = DQN(
    "MlpPolicy", env,
    learning_rate=args.learning_rate, buffer_size=100_000, learning_starts=1_000,
    batch_size=64, gamma=0.99, target_update_interval=args.target_update_interval,
    exploration_fraction=0.3, exploration_final_eps=args.eps_final,
    seed=args.seed, verbose=1,
)

# Record everything needed to reproduce the run on another machine.
with open(f"logs/{name}_config.json", "w") as f:
    json.dump({
        "args": vars(args),
        "scales": env.unwrapped.scales,
        "bridge_settings": env.unwrapped.settings,
        "python": sys.version,
        "platform": platform.platform(),
        "versions": {k: version(k) for k in
                     ["eclipse-sumo", "traci", "stable-baselines3", "torch", "gymnasium", "numpy"]},
    }, f, indent=2, default=str)

callback = (BestModelCallback(eval_env, args.val_seeds, args.eval_freq,
                              f"logs/{name}_best_model", f"logs/{name}_val.csv")
            if args.eval_freq > 0 else None)
model.learn(total_timesteps=args.steps, callback=callback)
model.save(f"logs/{name}_model")
env.close()
if eval_env is not None:
    eval_env.close()
