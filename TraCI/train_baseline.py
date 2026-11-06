"""Train a PPO traffic-signal baseline and write TensorBoard logs."""
import argparse

from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import EvalCallback
from stable_baselines3.common.monitor import Monitor

from .gym_env import TrafficSignalEnv


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenario", choices=("low", "medium", "high", "imbalance"), default="low")
    parser.add_argument("--timesteps", type=int, default=10_000)
    parser.add_argument("--model", default="models/ppo_low")
    parser.add_argument("--log-dir", default="runs/ppo_low")
    args = parser.parse_args()
    if args.timesteps <= 0:
        parser.error("--timesteps must be positive")

    train_env = Monitor(TrafficSignalEnv(args.scenario))
    eval_env = Monitor(TrafficSignalEnv(args.scenario))
    callback = EvalCallback(
        eval_env,
        best_model_save_path="models/best",
        log_path="runs/eval",
        eval_freq=max(1, args.timesteps // 10),
        deterministic=True,
    )
    model = PPO("MlpPolicy", train_env, verbose=1, tensorboard_log=args.log_dir)
    try:
        model.learn(total_timesteps=args.timesteps, callback=callback)
        model.save(args.model)
    finally:
        train_env.close()
        eval_env.close()
    print(f"Saved model: {args.model}.zip")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
