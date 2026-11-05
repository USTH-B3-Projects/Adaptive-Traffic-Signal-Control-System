import argparse
import numpy as np
from traffic_gym import Q_SCALE, TrafficEnv

p = argparse.ArgumentParser()
p.add_argument("--scenario", default="low", choices=["low", "medium", "high", "imbalance"])
p.add_argument("--model", default=None, help="path to a saved DQN model (optional)")
p.add_argument("--seeds", type=int, nargs="+", default=[100, 101, 102, 103, 104],
               help="SUMO traffic seeds not used during training")
args = p.parse_args()

env = TrafficEnv(args.scenario)
rng = np.random.default_rng(0)
FIXED_GREEN = 50.0   # about the 51 s green stage (3 s startup + 48 s) of the original program


# Each policy maps an observation to 0 (KEEP) or 1 (SWITCH).
def p_fixed(obs):
    return int(obs[10] * env.max_green >= FIXED_GREEN)

def p_max_green(obs):
    return 0                                     # the bridge forces a switch at max_green

def p_random(obs):
    return int(rng.integers(2))

def p_queue(obs):
    if obs[9] > 0.5:                             # in yellow / all-red
        return 0
    q_ns, q_ew = obs[0] * Q_SCALE, obs[1] * Q_SCALE
    green, red = (q_ns, q_ew) if obs[8] > 0.5 else (q_ew, q_ns)
    return int(red > green + 2)

policies = {
    "fixed-time (~51 s)": p_fixed,
    "max-green": p_max_green,
    "random": p_random,
    "queue-rule": p_queue,
}
if args.model:
    from stable_baselines3 import DQN
    model = DQN.load(args.model)
    policies["DQN"] = lambda obs: int(model.predict(obs, deterministic=True)[0])


def run(policy, sumo_seed):
    obs, _ = env.reset(options={"sumo_seed": sumo_seed})
    halts, waits, done = [], [], False
    while not done:
        obs, _, terminated, truncated, info = env.step(policy(obs))
        halts.append(info["halting"])
        waits.append(info["avg_wait"])
        done = terminated or truncated
    return float(np.mean(halts)), float(np.mean(waits))


print(f"\nScenario: {args.scenario} | traffic seeds: {args.seeds}")
print(f"Bridge settings: step={env.settings['simulation_step']} s, "
      f"decision={env.settings['decision_interval']} s, "
      f"green={env.settings['min_green']}-{env.settings['max_green']} s\n")
print(f"{'policy':20s} {'queue (veh)':>16s} {'wait (s)':>16s}")
for name, policy in policies.items():
    res = np.array([run(policy, s) for s in args.seeds])
    print(f"{name:20s} {res[:, 0].mean():8.2f} +/- {res[:, 0].std():4.2f} "
          f"{res[:, 1].mean():8.2f} +/- {res[:, 1].std():4.2f}")
env.close()