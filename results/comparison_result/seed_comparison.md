# PPO Training Seed Comparison

## 1. Scope

This living report compares completed multi-scenario PPO experiments. When a
new seed is trained, add its `results/seed<SEED>/summary_final.csv` and
`pipeline_timings.json` values using the same tables and append a section to
the assessment. The current experiments are:

| Item | Seed 107 | Seed 710 |
|---|---:|---:|
| PPO timesteps | 800,000 | 600,000 |
| Simulation step | 0.1 s | 0.1 s |
| Decision interval | 5 s | 5 s |
| Scenarios | Low, Medium, High, Imbalance | Low, Medium, High, Imbalance |
| Device | Recorded in pipeline artifacts | CUDA (`Quadro RTX 3000`) |

Both experiments use the same four scenarios and the same five core metrics. Values below are taken from the corresponding `summary_final.csv` files.

## 2. DRL Results by Scenario

### Low

| Metric | Seed 107 (800k) | Seed 710 (600k) | Seed 710 vs 107 |
|---|---:|---:|---:|
| Waiting Time (s) | 45.26 | 50.04 | +10.58% |
| Queue Length (vehicles) | 3.22 | 3.55 | +10.17% |
| Average Speed (m/s) | 7.50 | 7.42 | -1.05% |
| Arrived Count (vehicles) | 17.85 | 13.23 | -25.92% |
| Vehicles in Network | 17.07 | 18.31 | +7.29% |

### Medium

| Metric | Seed 107 (800k) | Seed 710 (600k) | Seed 710 vs 107 |
|---|---:|---:|---:|
| Waiting Time (s) | 125.34 | 135.17 | +7.84% |
| Queue Length (vehicles) | 9.01 | 9.63 | +6.92% |
| Average Speed (m/s) | 6.92 | 6.80 | -1.69% |
| Arrived Count (vehicles) | 36.22 | 35.86 | -1.00% |
| Vehicles in Network | 46.92 | 49.32 | +5.11% |

### High

| Metric | Seed 107 (800k) | Seed 710 (600k) | Seed 710 vs 107 |
|---|---:|---:|---:|
| Waiting Time (s) | 555.05 | 962.12 | +73.34% |
| Queue Length (vehicles) | 33.99 | 54.97 | +61.74% |
| Average Speed (m/s) | 4.60 | 3.40 | -26.22% |
| Arrived Count (vehicles) | 72.93 | 52.66 | -27.80% |
| Vehicles in Network | 116.13 | 153.68 | +32.34% |

### Imbalance

| Metric | Seed 107 (800k) | Seed 710 (600k) | Seed 710 vs 107 |
|---|---:|---:|---:|
| Waiting Time (s) | 815.19 | 1,117.53 | +37.09% |
| Queue Length (vehicles) | 46.34 | 65.47 | +41.26% |
| Average Speed (m/s) | 2.89 | 2.32 | -19.67% |
| Arrived Count (vehicles) | 44.35 | 46.44 | +4.73% |
| Vehicles in Network | 128.20 | 166.15 | +29.59% |

Positive percentages mean that Seed 710 has a higher metric than Seed 107. For waiting time, queue length, and vehicles in network this is worse; for average speed and arrived count, a positive value is generally better.

## 3. Current Seed-to-Seed Assessment (107 vs 710)

- **Seed 107 is stronger overall** on waiting time, queue length, average speed, and vehicles in network in all four scenarios.
- The difference is small in `low` and `medium`, where waiting time increases by 10.58% and 7.84% respectively for Seed 710.
- The difference becomes substantial in `high`: Seed 710 has 73.34% higher waiting time, 61.74% higher queue length, and 26.22% lower average speed.
- `imbalance` shows the same direction, with 37.09% higher waiting time and 41.26% higher queue length for Seed 710.
- Seed 710's higher arrived count in `imbalance` should not be interpreted alone as better performance because it also leaves more vehicles in the network and has materially higher delay and queue values.

The results suggest that the 800k training run (Seed 107) produced a more robust policy for the heavy and imbalanced demand distributions. The difference may reflect both training duration and stochastic seed effects; it is not sufficient to attribute the entire gap to timestep count without additional repeated seeds.

## 4. Current Runtime Comparison

| Stage | Seed 107 | Seed 710 |
|---|---:|---:|
| PPO training | 27.38 h (98,558.77 s) | 20.81 h (74,922.30 s) |
| PPO evaluation | 300.29 s | 364.58 s |
| Total pipeline | 27.66 h (99,558.18 s) | 21.12 h (76,022.20 s) |

Seed 710 reduced training time by using 600k timesteps and completed approximately 6.54 hours faster overall. This speed advantage came with weaker measured DRL results in the demanding scenarios.

## 5. Baseline Context

The baseline comparison remains available in the individual reports:

- `drl_seed107_report.md`
- `drl_seed710_report.md`

In the Seed 710 run, PPO improved waiting time over Fixed-Time in all scenarios, but it was worse than Rule-Based in `high` and `imbalance`. Therefore, Seed 107 is the better DRL candidate among the two seeds, but Rule-Based should remain the reference controller for stress scenarios until more training seeds or a selected checkpoint are evaluated.

## 6. Data Sources

- `results/seed107/summary_final.csv`
- `results/seed107/pipeline_timings.json`
- `results/seed710/summary_final.csv`
- `results/seed710/pipeline_timings.json`

For future experiments, keep each run isolated under `results/seed<SEED>/`,
`evaluation/seed<SEED>/`, and `models/seed<SEED>/`. Do not overwrite the
existing seed directories or replace the seed-specific report names.
