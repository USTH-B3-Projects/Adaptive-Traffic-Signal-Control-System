# DRL Seed 710 Experimental Report

**Status:** Completed Seed 710 multi-scenario PPO experiment.

## 1. Objective

Compare Fixed-Time, Rule-Based, and a single PPO agent trained across the four SUMO demand scenarios.

## 2. Experimental Setup

| Parameter | Configuration |
|---|---|
| Simulator | SUMO 1.28.0 |
| Algorithm | PPO (Stable-Baselines3) |
| Training scenarios | Low; Medium; High; Imbalance |
| Seed | 710 |
| Timesteps | 600,000 |
| Simulation step | 0.1 s |
| Decision interval | 5 s (50 simulation steps) |
| GUI | Disabled |
| Total pipeline runtime | 21.12 hours (76022.20 seconds) |
| PPO training runtime | 20.81 hours (74922.30 seconds) |

## 3. Evaluation Metrics

The report uses the pipeline's measured values for queue length, waiting time, average speed, arrived count, and vehicles remaining. For waiting time and queue length, lower is better; for speed and arrivals, higher is better.

## 4. Results — Seed 710

| Metric | Fixed-Time | Rule-Based | DRL PPO (600k) |
|---|---:|---:|---:|
| **Low** |  |  |  |
| Waiting Time (s) | 82.31 | 50.40 | 50.04 |
| Queue Length (vehicles) | 4.29 | 3.54 | 3.55 |
| Average Speed (m/s) | 8.75 | 7.48 | 7.42 |
| Arrived Count (vehicles) | 1207.00 | 28.00 | 13.22 |
| Vehicles in Network | 19.69 | 18.68 | 18.31 |
| **Medium** |  |  |  |
| Waiting Time (s) | 221.51 | 146.09 | 135.17 |
| Queue Length (vehicles) | 12.35 | 10.17 | 9.63 |
| Average Speed (m/s) | 8.12 | 6.77 | 6.80 |
| Arrived Count (vehicles) | 3014.00 | 72.00 | 35.86 |
| Vehicles in Network | 53.27 | 50.31 | 49.32 |
| **High** |  |  |  |
| Waiting Time (s) | 1028.96 | 700.88 | 962.12 |
| Queue Length (vehicles) | 49.56 | 42.74 | 54.97 |
| Average Speed (m/s) | 5.63 | 3.99 | 3.40 |
| Arrived Count (vehicles) | 5389.00 | 130.00 | 52.66 |
| Vehicles in Network | 141.21 | 134.01 | 153.68 |
| **Imbalance** |  |  |  |
| Waiting Time (s) | 2283.80 | 733.60 | 1117.53 |
| Queue Length (vehicles) | 97.63 | 40.27 | 65.47 |
| Average Speed (m/s) | 3.10 | 3.44 | 2.32 |
| Arrived Count (vehicles) | 3961.00 | 123.00 | 46.44 |
| Vehicles in Network | 213.55 | 119.57 | 166.15 |

## 5. DRL PPO Improvement

Improvement (%) = (baseline - DRL) / baseline x 100 for metrics where lower is better. For average speed, the numerator is DRL - baseline.

| Scenario | Metric | DRL vs Fixed-Time | DRL vs Rule-Based |
|---|---|---:|---:|
| Low | Waiting Time (s) | 39.20% | 0.71% |
| Low | Queue Length (vehicles) | 17.30% | -0.31% |
| Low | Average Speed (m/s) | -15.17% | -0.77% |
| Medium | Waiting Time (s) | 38.98% | 7.48% |
| Medium | Queue Length (vehicles) | 21.97% | 5.27% |
| Medium | Average Speed (m/s) | -16.22% | 0.49% |
| High | Waiting Time (s) | 6.50% | -37.27% |
| High | Queue Length (vehicles) | -10.91% | -28.60% |
| High | Average Speed (m/s) | -39.71% | -14.89% |
| Imbalance | Waiting Time (s) | 51.07% | -52.33% |
| Imbalance | Queue Length (vehicles) | 32.94% | -62.56% |
| Imbalance | Average Speed (m/s) | -25.13% | -32.56% |

## 6. Execution Time

| Method | Scenario | Execution Time (s) |
|---|---|---:|
| fixed_time | low | 28.15 |
| fixed_time | medium | 50.62 |
| fixed_time | high | 128.12 |
| fixed_time | imbalance | 266.96 |
| rule_based | low | 20.32 |
| rule_based | medium | 38.89 |
| rule_based | high | 102.15 |
| rule_based | imbalance | 98.60 |
| drl_ppo | low | 364.58 |
| drl_ppo | medium | 364.58 |
| drl_ppo | high | 364.58 |
| drl_ppo | imbalance | 364.58 |
| PPO training | all scenarios | 74922.30 |
| Total pipeline | all stages | 76022.20 |

## 7. Advanced Performance Metrics

| Method | Scenario | Total Travel Time | Average Delay / Vehicle | Throughput |
|---|---|---:|---:|---:|
| fixed_time | low | 70885.00 | 0.07 | 1208.68 |
| fixed_time | medium | 191770.00 | 0.07 | 3018.19 |
| fixed_time | high | 508350.00 | 0.19 | 5396.50 |
| fixed_time | imbalance | 768770.00 | 0.58 | 3966.51 |
| rule_based | low | 67230.00 | 1.80 | 28.04 |
| rule_based | medium | 181105.00 | 2.03 | 72.10 |
| rule_based | high | 482420.00 | 5.39 | 130.18 |
| rule_based | imbalance | 430410.00 | 5.96 | 123.17 |
| drl_ppo | low | 65920.00 | 2.18 | 23.00 |
| drl_ppo | medium | 177540.00 | 1.85 | 73.00 |
| drl_ppo | high | 553205.00 | 8.51 | 113.00 |
| drl_ppo | imbalance | 598105.00 | 12.42 | 90.00 |

## 8. Analysis

### Heavy and Imbalanced Traffic

The high and imbalance scenarios are the most demanding tests. The tables above should be read together: queue and waiting-time reductions indicate congestion relief, while speed and throughput indicate whether that relief translates into useful traffic flow.

### Single Multi-Scenario Agent

The PPO policy is one agent trained while sampling all four scenarios. This improves deployment simplicity and tests transfer across demand patterns, but it can trade peak performance in one scenario for robustness across the full distribution.

### Computation Cost

The recorded PPO training time was 20.81 hours (74922.30 seconds) and the complete pipeline took 21.12 hours (76022.20 seconds). Checkpointing provides recovery points during long runs.

### Learning Curve and Checkpoint

The recommended deployment checkpoint is `models/seed710/checkpoints/ppo_seed710_500000_steps.zip` (present).

The requested peak-reward and policy-degradation claims must be verified against the TensorBoard event file before being treated as measured findings; this report does not fabricate values that are not present in the CSV/JSON inputs.

### Comparison with a 20k Single-Scenario Model

A 20k single-scenario artifact was not found in the workspace; therefore a numerical comparison is not reported.

## 9. Comparison Plot

![Seed 710 comparison](D:/grp prj new lap/Adaptive-Traffic-Signal-Control-System/results/seed710/plots/seed710_baseline_comparison_5plots.png)

## 10. Data Sources

- `results/summary_final.csv`
- `evaluation/summary.csv`
- `results/pipeline_timings.json`
- `results/comparison_result/baseline_comparsion_seed57.md` (format reference)
