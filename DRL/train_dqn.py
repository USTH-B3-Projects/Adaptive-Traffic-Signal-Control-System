import argparse
import json
import os
import platform
import sys
from importlib import metadata
from stable_baselines3 import DQN
from stable_baselines3.common.monitor import Monitor

from traffic_gym import TrafficEnv


def version(pkg):
    try:
        return metadata.version(pkg)
    except metadata.PackageNotFoundError:
        return None


p = argparse.ArgumentParser()
p.add_argument("--scenario", default="low", choices=["low", "medium", "high", "imbalance"])
p.add_argument("--seed", type=int, default=0)
p.add_argument("--steps", type=int, default=20_000)
p.add_argument("--traffic-seeds", type=int, default=10)
args = p.parse_args()

name = f"dqn_{args.scenario}_seed{args.seed}"
os.makedirs("logs", exist_ok=True)

env = Monitor(TrafficEnv(args.scenario, traffic_seeds=range(args.traffic_seeds)),
              f"logs/{name}")

model = DQN(
    "MlpPolicy", env,
    learning_rate=1e-3, buffer_size=50_000, learning_starts=1_000,
    batch_size=64, gamma=0.99, target_update_interval=500,
    exploration_fraction=0.3, exploration_final_eps=0.05,
    seed=args.seed, verbose=1,
)

# Record everything needed to reproduce the run on another machine.
with open(f"logs/{name}_config.json", "w") as f:
    json.dump({
        "args": vars(args),
        "bridge_settings": env.unwrapped.settings,
        "python": sys.version,
        "platform": platform.platform(),
        "versions": {k: version(k) for k in
                     ["eclipse-sumo", "traci", "stable-baselines3", "torch", "gymnasium", "numpy"]},
    }, f, indent=2, default=str)

model.learn(total_timesteps=args.steps)
model.save(f"logs/{name}_model")
env.close()
