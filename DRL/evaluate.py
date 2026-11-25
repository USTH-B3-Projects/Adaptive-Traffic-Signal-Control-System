import argparse
import json
import os
import re

import numpy as np

from traffic_gym import MAPS, TEST_SEEDS, TrafficEnv

p = argparse.ArgumentParser()
p.add_argument("--map", default="simple_intersection", choices=list(MAPS),
               help="simple_intersection = Map_Nga_Tu (default), o_cho_dua = O_Cho_Dua; must match the training map")
p.add_argument("--scenario", default="low", choices=["low", "medium", "high", "imbalance"])
p.add_argument("--model", default=None, help="path to a saved DQN model, e.g. logs/dqn_low_seed0_model")
p.add_argument("--constant", choices=["switch", "keep"], default=None,
               help="instead of a model, always request this action (reference policy: 'switch' = change phase as soon "
                    "as the minimum green allows, 'keep' = only the maximum green forces a change)")
p.add_argument("--seeds", type=int, nargs="+", default=list(TEST_SEEDS),
               help="SUMO traffic seeds for the test (default: 57 367 1024)")
p.add_argument("--out-dir", default=None,
               help="default: results/drl for --model, results/constant for --constant")
args = p.parse_args()
if (args.model is None) == (args.constant is None):
    p.error("give exactly one of --model and --constant")
if args.out_dir is None:
    args.out_dir = "results/constant" if args.constant else "results/drl"

if args.constant:
    model = None
    name = f"constant_{args.constant}_{args.scenario}"
    cfg_path = ""
else:
    from stable_baselines3 import DQN  # noqa: E402

    model = DQN.load(args.model)
    name = re.sub(r"_model$", "", os.path.basename(args.model).replace(".zip", ""))
    cfg_path = re.sub(r"(_best)?_model(\.zip)?$", "", args.model) + "_config.json"

# observation scales used in training
scales = None
if cfg_path and os.path.exists(cfg_path):
    with open(cfg_path) as f:
        cfg = json.load(f)
    train_map = cfg.get("args", {}).get("map", "simple_intersection")   # older configs: Map_Nga_Tu only
    if train_map != args.map:
        p.error(f"this model was trained on map {train_map}, but --map is {args.map}")
    sc = cfg.get("scales")
    if sc:
        scales = (sc["q_scale"], sc["v_scale"], sc["w_scale"])
env = TrafficEnv(args.scenario, scales=scales, map_name=args.map)
OBS_NAMES = env.obs_names
K = env.n_groups   # observation layout: K queues, K vehicle counts, K waits, K speeds, ...
print(f"observation scales: {env.scales}", flush=True)

METRICS = ["mean_queue", "max_queue", "mean_total_waiting_time", "max_total_waiting_time"]


def run(sumo_seed):
    obs, info = env.reset(options={"sumo_seed": sumo_seed})
    queues, waits = [info["total_queue"]], [info["total_wait"]]      # sample at t = 0
    done = False
    clipped = []
    raw = []
    asked, done_sw = [], []
    while not done:
        action = (1 if args.constant == "switch" else 0) if args.constant else int(model.predict(obs, deterministic=True)[0])
        obs, _, terminated, truncated, info = env.step(action)
        asked.append(action)
        ex = info.get("executed_action", action)
        done_sw.append(int(ex == "SWITCH" or ex == 1))
        queues.append(info["total_queue"])
        waits.append(info["total_wait"])
        clipped.append(info["clipped"])
        raw.append(info["raw"])
        done = terminated or truncated
    queues, waits = queues[:-1], waits[:-1]   # samples are taken before each action: t = 0..3595
    return {
        "mean_queue": float(np.mean(queues)),
        "max_queue": float(np.max(queues)),
        "mean_total_waiting_time": float(np.mean(waits)),
        "max_total_waiting_time": float(np.max(waits)),
        "sample_count": len(queues),
        "switch_requested_rate": float(np.mean(asked)),   # share of decisions where the network chose SWITCH
        "switch_executed_rate": float(np.mean(done_sw)),  # share of decisions where the signal really switched
        "clip_rate": dict(zip(OBS_NAMES, np.mean(clipped, axis=0).round(4).tolist())),
    }, raw


os.makedirs(args.out_dir, exist_ok=True)
rows = []
all_raw = []
for s in args.seeds:
    r, raw = run(s)
    all_raw += raw
    rows.append({"map": args.map, "scenario": args.scenario, "seed": s, "controller": "constant" if args.constant else "dqn",
                 "model": name, **r})
    print(f"seed {s}: " + ", ".join(f"{m}={r[m]:.2f}" for m in METRICS)
          + f" (samples={r['sample_count']})", flush=True)
    print(f"        switch requested {r['switch_requested_rate']:.1%}, executed {r['switch_executed_rate']:.1%}", flush=True)
env.close()

with open(os.path.join(args.out_dir, f"{name}_eval.jsonl"), "w", encoding="utf-8") as f:
    for r in rows:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")

clip = {n: float(np.mean([r["clip_rate"][n] for r in rows])) for n in OBS_NAMES}
summary = {"map": args.map, "scenario": args.scenario, "model": name, "seeds": args.seeds,
           "bridge_settings": env.settings, "scales": env.scales, "clip_rate": clip, "metrics": {}}
print(f"\nMap: {args.map} | Scenario: {args.scenario} | model: {name} | seeds: {args.seeds}")
print(f"{'metric':28s} {'mean +/- SD':>20s}")
for m in METRICS:
    v = np.array([r[m] for r in rows])
    sd = float(v.std(ddof=1)) if len(v) > 1 else 0.0
    summary["metrics"][m] = {"mean": float(v.mean()), "sd": sd}
    print(f"{m:28s} {v.mean():10.2f} +/- {sd:6.2f}")
print("\nfraction of steps with the feature clipped at 1 (only features above 0):")
for n, v in clip.items():
    if v > 0:
        print(f"  {n:14s} {v:6.1%}")
# 95th percentile of the unclipped features -> scale that would clip them in at most 5% of the steps
p95 = np.percentile(np.array(all_raw), 95, axis=0)
sc = env.scales
sugg = {"q_scale": float(p95[0:K].max() * sc["q_scale"]),
        "v_scale": float(p95[K:2 * K].max() * sc["v_scale"]),
        "w_scale": float(p95[2 * K:3 * K].max() * sc["w_scale"])}
summary["suggested_scales_p95"] = sugg
print("scales that would clip at most 5% of the steps: "
      + ", ".join(f"{k}={v:.0f}" for k, v in sugg.items()))
with open(os.path.join(args.out_dir, f"{name}_summary.json"), "w", encoding="utf-8") as f:
    json.dump(summary, f, indent=2, default=str)
print(f"\nSaved to {args.out_dir}/{name}_eval.jsonl and {name}_summary.json")
