# DRL Seed 107 Experimental Report

**Status:** Completed Seed 107 multi-scenario PPO experiment.

## 1. Objective

Compare Fixed-Time, Rule-Based, and a single PPO agent trained across the four SUMO demand scenarios.

## 2. Experimental Setup

| Parameter | Configuration |
|---|---|
| Simulator | SUMO 1.28.0 |
| Algorithm | PPO (Stable-Baselines3) |
| Training scenarios | Low; Medium; High; Imbalance |
| Seed | 107 |
| Timesteps | 800,000 |
| Simulation step | 0.1 s |
| Decision interval | 5 s (50 simulation steps) |
| GUI | Disabled |
| Total pipeline runtime | 27.66 hours (99558.18 seconds) |
| PPO training runtime | 27.38 hours (98558.77 seconds) |

## 3. Evaluation Metrics

The report uses the pipeline's measured values for queue length, waiting time, average speed, arrived count, and vehicles remaining. For waiting time and queue length, lower is better; for speed and arrivals, higher is better.

## 4. Results — Seed 107

| Metric | Fixed-Time | Rule-Based | DRL PPO (800k) |
|---|---:|---:|---:|
| **Low** |  |  |  |
| Waiting Time (s) | 91.26 | 54.44 | 45.26 |
| Queue Length (vehicles) | 4.65 | 3.75 | 3.22 |
| Average Speed (m/s) | 8.56 | 7.34 | 7.50 |
| Arrived Count (vehicles) | 1174.00 | 25.00 | 17.85 |
| Vehicles in Network | 19.53 | 18.34 | 17.07 |
| **Medium** |  |  |  |
| Waiting Time (s) | 233.16 | 139.82 | 125.34 |
| Queue Length (vehicles) | 12.53 | 9.80 | 9.01 |
| Average Speed (m/s) | 8.08 | 6.84 | 6.92 |
| Arrived Count (vehicles) | 2982.00 | 76.00 | 36.22 |
| Vehicles in Network | 52.82 | 49.34 | 46.92 |
| **High** |  |  |  |
| Waiting Time (s) | 1172.51 | 649.68 | 555.05 |
| Queue Length (vehicles) | 51.80 | 38.77 | 33.99 |
| Average Speed (m/s) | 5.42 | 4.16 | 4.60 |
| Arrived Count (vehicles) | 5275.00 | 113.00 | 72.93 |
| Vehicles in Network | 143.50 | 126.36 | 116.13 |
| **Imbalance** |  |  |  |
| Waiting Time (s) | 1962.03 | 706.89 | 815.19 |
| Queue Length (vehicles) | 83.04 | 36.58 | 46.34 |
| Average Speed (m/s) | 3.42 | 3.60 | 2.89 |
| Arrived Count (vehicles) | 3888.00 | 142.00 | 44.35 |
| Vehicles in Network | 185.59 | 110.17 | 128.20 |

## 5. DRL PPO Improvement

Improvement (%) = (baseline - DRL) / baseline x 100 for metrics where lower is better. For average speed, the numerator is DRL - baseline.

| Scenario | Metric | DRL vs Fixed-Time | DRL vs Rule-Based |
|---|---|---:|---:|
| Low | Waiting Time (s) | 50.41% | 16.87% |
| Low | Queue Length (vehicles) | 30.68% | 14.10% |
| Low | Average Speed (m/s) | -12.37% | 2.23% |
| Medium | Waiting Time (s) | 46.24% | 10.35% |
| Medium | Queue Length (vehicles) | 28.09% | 8.04% |
| Medium | Average Speed (m/s) | -14.37% | 1.15% |
| High | Waiting Time (s) | 52.66% | 14.57% |
| High | Queue Length (vehicles) | 34.39% | 12.35% |
| High | Average Speed (m/s) | -15.07% | 10.55% |
| Imbalance | Waiting Time (s) | 58.45% | -15.32% |
| Imbalance | Queue Length (vehicles) | 44.19% | -26.70% |
| Imbalance | Average Speed (m/s) | -15.56% | -19.85% |

## 6. Execution Time

| Method | Scenario | Execution Time (s) |
|---|---|---:|
| fixed_time | low | 28.39 |
| fixed_time | medium | 52.50 |
| fixed_time | high | 131.58 |
| fixed_time | imbalance | 224.57 |
| rule_based | low | 21.69 |
| rule_based | medium | 40.70 |
| rule_based | high | 100.74 |
| rule_based | imbalance | 96.89 |
| drl_ppo | low | 300.29 |
| drl_ppo | medium | 300.29 |
| drl_ppo | high | 300.29 |
| drl_ppo | imbalance | 300.29 |
| PPO training | all scenarios | 98558.77 |
| Total pipeline | all stages | 99558.18 |

## 7. Advanced Performance Metrics

| Method | Scenario | Total Travel Time | Average Delay / Vehicle | Throughput |
|---|---|---:|---:|---:|
| fixed_time | low | 70320.00 | 0.08 | 1175.63 |
| fixed_time | medium | 190155.00 | 0.08 | 2986.15 |
| fixed_time | high | 516610.00 | 0.22 | 5282.34 |
| fixed_time | imbalance | 668120.00 | 0.50 | 3893.41 |
| rule_based | low | 66025.00 | 2.18 | 25.03 |
| rule_based | medium | 177625.00 | 1.84 | 76.11 |
| rule_based | high | 454875.00 | 5.75 | 113.16 |
| rule_based | imbalance | 396585.00 | 4.98 | 142.20 |
| drl_ppo | low | N/A | N/A | N/A |
| drl_ppo | medium | N/A | N/A | N/A |
| drl_ppo | high | N/A | N/A | N/A |
| drl_ppo | imbalance | N/A | N/A | N/A |

## 8. Analysis

### Heavy and Imbalanced Traffic

The high and imbalance scenarios are the most demanding tests. The tables above should be read together: queue and waiting-time reductions indicate congestion relief, while speed and throughput indicate whether that relief translates into useful traffic flow.

### Single Multi-Scenario Agent

The PPO policy is one agent trained while sampling all four scenarios. This improves deployment simplicity and tests transfer across demand patterns, but it can trade peak performance in one scenario for robustness across the full distribution.

### Computation Cost

The recorded PPO training time was 27.38 hours (98558.77 seconds) and the complete pipeline took 27.66 hours (99558.18 seconds). Checkpointing provides recovery points during long runs.

### Learning Curve and Checkpoint

The recommended deployment checkpoint is `models/checkpoints/ppo_multiscenario_500000_steps.zip` (present).

The requested peak-reward and policy-degradation claims must be verified against the TensorBoard event file before being treated as measured findings; this report does not fabricate values that are not present in the CSV/JSON inputs.

### Comparison with a 20k Single-Scenario Model

A 20k single-scenario artifact was not found in the workspace; therefore a numerical comparison is not reported.

## 9. Data Sources

- `results/summary_final.csv`
- `evaluation/summary.csv`
- `results/pipeline_timings.json`
- `results/comparison_result/baseline_comparsion_seed57.md` (format reference)
