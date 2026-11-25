# DRL: DQN baseline for adaptive traffic-signal control (SUMO)

Single four-way intersection (`SUMO/Map_Nga_tu`, outputs in `Map_Nga_Tu/`), scenarios `low`, `medium`, `high`, `imbalance`.
Action every 5 s: KEEP / SWITCH (min green 30 s, max green 75 s). Episode = 3600 s (720 decisions).

## Files
| File | Purpose |
|---|---|
| `traffic_gym.py` | Gymnasium wrapper `TrafficEnv` over the TraCI bridge (observation in [0,1]: 11 values for `Map_Nga_Tu`, 22 values for `O_Cho_Dua`; Discrete(2) = KEEP / SWITCH) |
| `train_dqn.py` | Train SB3 DQN (100k steps); writes `logs/<name>.monitor.csv`, `_model.zip`, `_best_model.zip`, `_val.csv`, `_config.json` |
| `evaluate.py` | Evaluate a model (or `--constant switch/keep`) on test seeds 57, 367, 1024; writes `results/drl/` |
| `train_plot.py` | Plot the training curve of one run (`python ../DRL/train_plot.py dqn_low_seed0`) |
| `check_policy.py` | Quick check on random observations whether a model is constant (weak proxy, do not rely on it) |

## Repository layout
```
DRL/          shared code (this folder)
Map_Nga_Tu/   logs/ and results/ of the DQN runs on SUMO/Map_Nga_tu
O_Cho_Dua/    logs/ and results/ of the DQN runs on SUMO/O_cho_dua (work in progress)
```
Select the map with `--map simple_intersection` (default, Map_Nga_Tu) or `--map o_cho_dua`; run from the folder of that map.

## Protocol
Train traffic seeds 0-9; validation seeds 100-102 (best checkpoint); test seeds 57, 367, 1024.
Metrics (720 samples per episode): mean/max queue, mean/max total waiting time; reported as mean +/- sample SD.

## Versions (important)
- **v1** (original): reward `avg_wait`, observation scales q=20, v=30, w=60.
- **v2**: optional `--q-scale/--v-scale/--w-scale` and `--reward total_wait`.
- **The default `--reward` is now `total_wait`.** To reproduce v1 pass `--reward avg_wait` (and `--eval-freq 0` to skip validation).

## Commands
**Run every command from the map folder** (`cd Map_Nga_Tu`), and call the code in `../DRL/`. `logs/` and `results/` below are `Map_Nga_Tu/logs/` and `Map_Nga_Tu/results/`; the code (`DRL/`) is shared between maps and sits next to `Map_Nga_Tu/` at the repository root.

```
python ../DRL/train_dqn.py --scenario imbalance --seed 0 --reward avg_wait --eval-freq 0           # v1
python ../DRL/train_dqn.py --scenario high --seed 0 --q-scale 60 --v-scale 90 --w-scale 30 \
       --reward avg_wait --tag v2a                                                              # v2a
python ../DRL/train_dqn.py --scenario high --seed 0 --q-scale 60 --v-scale 90 --w-scale 30 \
       --reward total_wait --tag v2b                                                            # v2b
python ../DRL/evaluate.py --scenario high --model logs/dqn_high_seed0_v2a_best_model
python ../DRL/evaluate.py --scenario high --constant switch
```
Result folders: `results/drl/` (DQN models, per test seed and summary; includes clipping rates and requested/executed switch rates), `results/constant/` (constant policies always SWITCH / always KEEP).
Each run saves `logs/<name>_config.json` (arguments, scales, package versions). Results and the full
write-ups are in `docs/baseline_report/` and `docs/dqn_100k_report.md`.

## Environment used for the results
All evaluation results (`results/`, `docs/`) were produced with **SUMO 1.28.0** (`eclipse-sumo`, `sumo-data`, `traci`, `sumolib` 1.28.0).
The DQN models were trained earlier with SUMO 1.27.1 (see `logs/<name>_config.json`) and were not retrained.
Python 3.12.16, macOS (arm64), stable-baselines3 2.9.2, torch 2.15.0, gymnasium 1.4.0, numpy 2.5.4, matplotlib 3.11.2
(training versions read from `logs/dqn_high_seed0_v2a_config.json`; matplotlib is not recorded there). Other versions may give
different numbers. Suggested pins for `requirements.txt`:
```
eclipse-sumo==1.28.0
sumo-data==1.28.0
traci==1.28.0
sumolib==1.28.0
stable-baselines3==2.9.2
torch==2.15.0
gymnasium==1.4.0
numpy==2.5.4
matplotlib==3.11.2
```

## Notes on the trained models
**Files.** `<name>_model.zip` is the model at the last training step; `<name>_best_model.zip` is the checkpoint with the
best validation return (seeds 100-102, every 10,000 steps). The v1 results in the report use the final models
(v1 had no validation); the v2 results use the best checkpoints.

**Use the same observation scales as in training.** A model only works with the scales it was trained with
(v1: q=20, v=30, w=60; v2a/v2b High: 60/90/30; v2a Imbalance: 70/110/30). `evaluate.py` reads them from
`<name>_config.json`, so keep that file next to the model. A v1 model evaluated with other scales gives wrong results.

**Scope.** Models are trained per scenario (low, medium, high, imbalance) and per map. The results in this repository
are for `SUMO/Map_Nga_tu` (`--map simple_intersection`, outputs in `Map_Nga_Tu/`) with the traffic volumes of the route
files on `main`. A model is not expected to transfer to another map or to other volumes. `SUMO/O_cho_dua`
(`--map o_cho_dua`, outputs in `O_Cho_Dua/`) is a separate setting: only the main junction is controlled,
4 green phases (SUMO phases 0, 2, 5, 7) in a fixed cycle, so SWITCH means "go to the next green phase".
Its results are not part of this stage. `evaluate.py` refuses a model whose training map differs from `--map`.

**What the results show (see `docs/baseline_report/`).**
- DQN is clearly better than fixed-time in all four scenarios.
- In Low, Medium and High, DQN is about equal to the rule-based controller and to the constant policy
  "always SWITCH". In High the final models of DRL seeds 0 and 1 and of both v2 runs are exactly "always SWITCH".
- Only in Imbalance does DQN beat the rule-based controller (about 8.3% on mean queue over 5 DRL seeds),
  and the gain varies by seed (1.2% to 11.4%). Quote it as an average over seeds, not from one seed.
- Observation clipping (saturation) exists in High and Imbalance with the v1 scales. The v2 scales and reward
  removed it but did not improve the mean or the worst-case metrics.

**How to read the actions.** SWITCH requested before the minimum green (30 s) is ignored, so the share of
requested SWITCH can be much higher than the share of executed switches (`evaluate.py` prints both). Judge a
policy by the executed rate and by the metrics, not by `check_policy.py`, which uses random observations.

**Variability.** Results change with the DRL seed. Use at least 3 DRL seeds (5 for Imbalance) and report mean and SD over the test seeds 57, 367, 1024. The training return in the plots includes exploration; it is not the test performance.
