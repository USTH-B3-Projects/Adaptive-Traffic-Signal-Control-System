# DRL Seed100 — V2 experimental report

**Completed V2 seed100 experiment; results below are measured artifacts.**

## Configuration and execution

- Training seed: 100; requested/actual steps: 600,000 / 601,920.
- GPU: Quadro RTX 3000; fixed validation seed999; held-out evaluation seeds: [101, 102, 103].
- Training seeds sampled only from [1000,999999]; shuffled cycles cover all four scenarios.
- 12D directional observations clipped to [0,1]; MLP actor/critic [128,128].
- Reward = clip(-[Q_NS+Q_EW+0.05(W_NS+W_EW)+0.02(Q_NS-Q_EW)^2]/100,-10,0).
- SUMO step0.1s; decision5s; min/max green15/75s; yellow/all-red3/3s.
- PPO: n_steps2880, batch96, epochs5, gamma0.99, GAE0.95, clip0.2, entropy0.01, vf0.5, grad_norm0.5, target_KL0.02.
- LR linearly decreases 3e-4→1e-5; CUDA; advantage normalization enabled.
- Best model selected ONLY by mean reward on four seed999 validation episodes; held-out seeds never select the model.
- Timings in seconds: {"fixed_time_low_seed101": 26.83239609998418, "fixed_time_medium_seed101": 47.49392189999344, "fixed_time_high_seed101": 117.79104829998687, "fixed_time_imbalance_seed101": 232.1293944999925, "fixed_time_low_seed102": 24.05379550001817, "fixed_time_medium_seed102": 44.80832840001676, "fixed_time_high_seed102": 110.47892720001983, "fixed_time_imbalance_seed102": 281.24485299998196, "fixed_time_low_seed103": 23.954957699985243, "fixed_time_medium_seed103": 44.33473629999207, "fixed_time_high_seed103": 104.7506793999928, "fixed_time_imbalance_seed103": 177.04397429997334, "rule_based_low_seed101": 22.125246500014327, "rule_based_medium_seed101": 39.81055529997684, "rule_based_high_seed101": 93.06016490003094, "rule_based_imbalance_seed101": 83.40195109997876, "rule_based_low_seed102": 22.64193919999525, "rule_based_medium_seed102": 39.09121360001154, "rule_based_high_seed102": 91.5829398999922, "rule_based_imbalance_seed102": 88.34391930000857, "rule_based_low_seed103": 22.603232299967203, "rule_based_medium_seed103": 39.64554269996006, "rule_based_high_seed103": 90.65050029999111, "rule_based_imbalance_seed103": 76.19019679998746, "drl_training": 57655.59046400001, "drl_evaluation_best": 798.1653076999937, "drl_evaluation_final": 813.890689599968, "pipeline_through_evaluation": 61211.735251000035}

## Fair multi-seed traffic results

Mean ± sample Std (ddof=1) over evaluation seeds; single-seed preflight reports Std=0, not an uncertainty estimate.
Queue/wait/speed/network count: means of 720 post-step snapshots at t=5..3600s.
Arrivals: SUM of incremental arrivals over every 0.1s substep for the full episode.
Speed: vehicle-count-weighted over the same eight incoming lanes for all methods.
Same SUMO seeds and input files are passed directly to all methods; controlled trajectories may differ.

| Scenario | Metric | Fixed-Time | Rule-Based | PPO best | PPO final (secondary) |
|---|---|---:|---:|---:|---:|
| low | queue_length | 4.71 ± 0.11 | 2.42 ± 0.06 | 2.49 ± 0.05 | 2.49 ± 0.05 |
| low | waiting_time | 91.95 ± 2.55 | 22.71 ± 0.66 | 23.34 ± 0.32 | 23.34 ± 0.32 |
| low | average_speed | 6.79 ± 0.12 | 8.22 ± 0.09 | 8.15 ± 0.07 | 8.15 ± 0.07 |
| low | arrived_count | 1170.33 ± 28.04 | 1173.33 ± 26.76 | 1175.00 ± 24.27 | 1175.00 ± 24.27 |
| low | vehicles_in_network | 19.73 ± 0.41 | 17.01 ± 0.49 | 17.11 ± 0.43 | 17.11 ± 0.43 |
| medium | queue_length | 12.59 ± 0.60 | 6.98 ± 0.25 | 7.28 ± 0.30 | 7.28 ± 0.30 |
| medium | waiting_time | 231.66 ± 14.96 | 67.17 ± 2.72 | 71.68 ± 4.30 | 71.68 ± 4.30 |
| medium | average_speed | 6.16 ± 0.13 | 7.58 ± 0.11 | 7.47 ± 0.08 | 7.47 ± 0.08 |
| medium | arrived_count | 2972.33 ± 27.21 | 2982.33 ± 23.69 | 2984.00 ± 20.88 | 2984.00 ± 20.88 |
| medium | vehicles_in_network | 53.15 ± 0.25 | 46.08 ± 0.80 | 46.44 ± 0.80 | 46.44 ± 0.80 |
| high | queue_length | 46.41 ± 2.75 | 32.07 ± 0.23 | 33.30 ± 3.60 | 32.30 ± 1.89 |
| high | waiting_time | 977.85 ± 71.61 | 385.14 ± 9.48 | 395.16 ± 44.47 | 386.55 ± 29.62 |
| high | average_speed | 3.80 ± 0.14 | 4.59 ± 0.03 | 4.49 ± 0.29 | 4.57 ± 0.16 |
| high | arrived_count | 5250.33 ± 69.28 | 5280.00 ± 83.72 | 5268.33 ± 80.60 | 5273.00 ± 80.02 |
| high | vehicles_in_network | 135.78 ± 3.58 | 118.14 ± 1.32 | 120.59 ± 6.43 | 118.71 ± 3.78 |
| imbalance | queue_length | 88.53 ± 13.57 | 27.79 ± 3.28 | 21.19 ± 0.53 | 22.47 ± 6.88 |
| imbalance | waiting_time | 1984.07 ± 243.31 | 418.28 ± 41.75 | 350.30 ± 23.18 | 387.29 ± 131.94 |
| imbalance | average_speed | 2.09 ± 0.26 | 4.23 ± 0.32 | 5.06 ± 0.03 | 4.97 ± 0.82 |
| imbalance | arrived_count | 3886.00 ± 61.05 | 4086.67 ± 54.50 | 4095.00 ± 68.51 | 4093.33 ± 59.92 |
| imbalance | vehicles_in_network | 200.16 ± 29.34 | 99.18 ± 6.88 | 86.76 ± 1.06 | 89.49 ± 12.90 |

![V2 comparison](../seed100/plots/seed100_baseline_comparison.png)

## Historical V1 → V2 context

Descriptive comparison only: V1 used different timing (min green30s), unmatched traffic seeds,
and faulty arrivals/speed definitions. Do not attribute changes solely to the neural network.

| Scenario | V1 PPO107 waiting | V1 PPO710 waiting | V2 PPO best waiting |
|---|---:|---:|---:|
| low | 45.26 | 50.04 | 23.34 ± 0.32 |
| medium | 125.34 | 135.17 | 71.68 ± 4.30 |
| high | 555.05 | 962.12 | 395.16 ± 44.47 |
| imbalance | 815.19 | 1117.53 | 350.30 ± 23.18 |

## Interpretation and limitations

Waiting is the time-mean of the sum of current lane waiting times, not mean trip delay.
Evaluation stops at3600s; remaining vehicles are reported; completed-trip delay is not inferred.
Collision warnings are retained in subprocess.log; low queue/wait does not establish collision-free operation.
Normalization clips queue>60, vehicles>80 and waiting>1500 per axis; saturation and imbalance penalty can trade throughput against balance.
Only three held-out seeds support this comparison; no guarantee of superiority or convergence is implied.
V1 models, evaluations, results, event logs and existing comparison Markdown files were preserved.

Sources: per-step metrics.csv, per-episode episodes.csv, summary_final.csv, pipeline_timings.json,
training_metadata.json and the preserved V1 seed107/seed710 summaries.

## Appendix — Additional traffic-seed evaluation: 57, 367, 1024

<!-- APPENDIX-NEW-TRAFFIC-SEEDS-57-367-1024 -->

This appendix evaluates the same PPO best checkpoint from training seed 100 (models/seed100/best_model/best_model.zip), with deterministic=True and no retraining. It is a separate 36-episode / 25,920-sample comparison against newly executed Fixed-Time and Rule-Based baselines; the earlier 101/102/103 results and all preceding text remain unchanged.

V2 settings: simulation step 0.1 s, decision interval 5 s, min/max green 15/75 s, yellow/all-red 3/3 s, 3600 s per episode. PPO/Rule-Based share adaptive signal constraints; Fixed-Time retains its static 51 s green per axis inside the same bounds. Shared post-step metrics use episode means, except arrived_count, which sums all 0.1 s substeps. Waiting is summed current lane waiting, not completed-trip delay; speed is vehicle-weighted on eight incoming lanes. These corrected V2 measurements and 15 s minimum green must not be conflated with older 30 s baseline logs.

### A. Multi-seed mean ± sample Std (ddof=1)

Units: queue/network in vehicles, waiting in seconds, speed in m/s, arrivals in vehicles per episode. Lower queue/wait/network and higher speed/arrivals are favorable.

| Scenario | Metric | Fixed-Time | Rule-Based | PPO best |
| --- | --- | --- | --- | --- |
| low | queue_length | 4.963426 ± 0.046592 | 2.576852 ± 0.073524 | 2.664352 ± 0.084086 |
| low | waiting_time | 97.892639 ± 1.082200 | 24.263981 ± 0.170608 | 25.635046 ± 1.137117 |
| low | average_speed | 6.609051 ± 0.070891 | 8.132315 ± 0.031724 | 8.019519 ± 0.152761 |
| low | arrived_count | 1192.333333 ± 27.061658 | 1198.666667 ± 24.440404 | 1199.000000 ± 24.879711 |
| low | vehicles_in_network | 20.278704 ± 0.273665 | 17.456481 ± 0.390350 | 17.556481 ± 0.195663 |
| medium | queue_length | 12.939352 ± 0.387060 | 7.058796 ± 0.249325 | 6.962500 ± 0.079434 |
| medium | waiting_time | 238.878333 ± 8.043524 | 68.476759 ± 2.932450 | 67.211019 ± 1.347887 |
| medium | average_speed | 6.023025 ± 0.077788 | 7.510455 ± 0.102917 | 7.554743 ± 0.015656 |
| medium | arrived_count | 2951.000000 ± 61.506097 | 2957.333333 ± 62.228075 | 2961.000000 ± 58.129167 |
| medium | vehicles_in_network | 53.402778 ± 1.320360 | 45.870370 ± 1.223669 | 45.724537 ± 0.801415 |
| high | queue_length | 45.629630 ± 2.859215 | 33.485185 ± 0.908272 | 33.249074 ± 1.292734 |
| high | waiting_time | 939.661713 ± 75.381490 | 401.980278 ± 12.695573 | 392.615880 ± 17.328119 |
| high | average_speed | 3.843322 ± 0.136998 | 4.459157 ± 0.136015 | 4.456669 ± 0.123420 |
| high | arrived_count | 5304.333333 ± 56.571489 | 5314.333333 ± 37.819748 | 5319.000000 ± 49.507575 |
| high | vehicles_in_network | 135.045833 ± 4.598682 | 121.367593 ± 2.762906 | 121.167593 ± 2.940572 |
| imbalance | queue_length | 82.909722 ± 6.982146 | 24.559259 ± 1.768458 | 19.606019 ± 0.435051 |
| imbalance | waiting_time | 1851.894537 ± 112.696974 | 333.737361 ± 9.596070 | 311.851944 ± 13.395462 |
| imbalance | average_speed | 2.123738 ± 0.079933 | 4.428855 ± 0.213498 | 5.222944 ± 0.033861 |
| imbalance | arrived_count | 3931.666667 ± 33.291641 | 4111.666667 ± 53.050291 | 4123.000000 ± 65.642974 |
| imbalance | vehicles_in_network | 188.637963 ± 17.549400 | 94.475463 ± 4.036181 | 84.681019 ± 0.841126 |

### B. PPO best improvement (%)

Positive is favorable: 100(B-P)/B for queue/wait/network; 100(P-B)/B for speed/arrivals. Calculated before rounding.

| Scenario | Metric | vs Fixed-Time (%) | vs Rule-Based (%) |
| --- | --- | --- | --- |
| low | queue_length | 46.320306 | -3.395616 |
| low | waiting_time | 73.813101 | -5.650618 |
| low | average_speed | 21.341461 | -1.387010 |
| low | arrived_count | 0.559128 | 0.027809 |
| low | vehicles_in_network | 13.424045 | -0.572853 |
| medium | queue_length | 46.191277 | 1.364203 |
| medium | waiting_time | 71.863912 | 1.848424 |
| medium | average_speed | 25.431038 | 0.589693 |
| medium | arrived_count | 0.338868 | 0.123986 |
| medium | vehicles_in_network | 14.377980 | 0.317925 |
| high | queue_length | 27.132711 | 0.705121 |
| high | waiting_time | 58.217316 | 2.329567 |
| high | average_speed | 15.958772 | -0.055805 |
| high | arrived_count | 0.276503 | 0.087813 |
| high | vehicles_in_network | 10.276689 | 0.164789 |
| imbalance | queue_length | 76.352570 | 20.168527 |
| imbalance | waiting_time | 83.160383 | 6.557677 |
| imbalance | average_speed | 145.931595 | 17.929880 |
| imbalance | arrived_count | 4.866469 | 0.275638 |
| imbalance | vehicles_in_network | 55.109238 | 10.367183 |

### C. Individual traffic seeds

#### Seed 57

| Scenario | Method | Queue | Waiting (s) | Speed (m/s) | Arrivals | Network vehicles |
| --- | --- | --- | --- | --- | --- | --- |
| low | Fixed-Time | 4.987500 | 96.723194 | 6.539893 | 1162.000000 | 19.990278 |
| low | Rule-Based | 2.519444 | 24.256528 | 8.129235 | 1172.000000 | 17.052778 |
| low | PPO best | 2.754167 | 26.947500 | 7.881923 | 1172.000000 | 17.330556 |
| medium | Fixed-Time | 12.544444 | 229.664167 | 6.110740 | 2917.000000 | 52.369444 |
| medium | Rule-Based | 6.856944 | 66.322778 | 7.595975 | 2926.000000 | 45.168056 |
| medium | PPO best | 7.005556 | 67.248333 | 7.537362 | 2931.000000 | 45.447222 |
| high | Fixed-Time | 42.329167 | 858.467500 | 3.990629 | 5280.000000 | 130.208333 |
| high | Rule-Based | 33.251389 | 401.499722 | 4.514158 | 5292.000000 | 120.147222 |
| high | PPO best | 34.300000 | 403.516806 | 4.392335 | 5305.000000 | 122.888889 |
| imbalance | Fixed-Time | 75.863889 | 1725.039444 | 2.211614 | 3895.000000 | 170.958333 |
| imbalance | Rule-Based | 22.538889 | 324.116389 | 4.674703 | 4060.000000 | 89.887500 |
| imbalance | PPO best | 19.837500 | 307.307361 | 5.203657 | 4060.000000 | 84.622222 |

#### Seed 367

| Scenario | Method | Queue | Waiting (s) | Speed (m/s) | Arrivals | Network vehicles |
| --- | --- | --- | --- | --- | --- | --- |
| low | Fixed-Time | 4.909722 | 98.095972 | 6.605703 | 1201.000000 | 20.311111 |
| low | Rule-Based | 2.551389 | 24.097222 | 8.165467 | 1204.000000 | 17.484722 |
| low | PPO best | 2.651389 | 24.945139 | 7.992733 | 1204.000000 | 17.668056 |
| medium | Fixed-Time | 12.955556 | 242.474167 | 5.995919 | 2914.000000 | 52.948611 |
| medium | Rule-Based | 6.981944 | 67.291111 | 7.539155 | 2917.000000 | 45.159722 |
| medium | PPO best | 6.870833 | 65.844861 | 7.567738 | 2924.000000 | 45.098611 |
| high | Fixed-Time | 47.206944 | 1007.424861 | 3.819605 | 5264.000000 | 135.568056 |
| high | Rule-Based | 32.716667 | 389.531806 | 4.559058 | 5293.000000 | 119.425000 |
| high | PPO best | 31.805556 | 372.634722 | 4.598964 | 5278.000000 | 117.772222 |
| imbalance | Fixed-Time | 83.038889 | 1890.193472 | 2.104249 | 3960.000000 | 188.901389 |
| imbalance | Rule-Based | 25.826389 | 343.308333 | 4.290100 | 4109.000000 | 96.059722 |
| imbalance | PPO best | 19.876389 | 326.928472 | 5.203132 | 4118.000000 | 83.870833 |

#### Seed 1024

| Scenario | Method | Queue | Waiting (s) | Speed (m/s) | Arrivals | Network vehicles |
| --- | --- | --- | --- | --- | --- | --- |
| low | Fixed-Time | 4.993056 | 98.858750 | 6.681557 | 1214.000000 | 20.534722 |
| low | Rule-Based | 2.659722 | 24.438194 | 8.102243 | 1220.000000 | 17.831944 |
| low | PPO best | 2.587500 | 25.012500 | 8.183901 | 1221.000000 | 17.670833 |
| medium | Fixed-Time | 13.318056 | 244.496667 | 5.962418 | 3022.000000 | 54.890278 |
| medium | Rule-Based | 7.337500 | 71.816389 | 7.396234 | 3029.000000 | 47.283333 |
| medium | PPO best | 7.011111 | 68.539861 | 7.559129 | 3028.000000 | 46.627778 |
| high | Fixed-Time | 47.352778 | 953.092778 | 3.719730 | 5369.000000 | 139.361111 |
| high | Rule-Based | 34.487500 | 414.909306 | 4.304254 | 5358.000000 | 124.530556 |
| high | PPO best | 33.641667 | 401.696111 | 4.378707 | 5374.000000 | 122.841667 |
| imbalance | Fixed-Time | 89.826389 | 1940.450694 | 2.055352 | 3940.000000 | 206.054167 |
| imbalance | Rule-Based | 25.312500 | 333.787361 | 4.321764 | 4166.000000 | 97.479167 |
| imbalance | PPO best | 19.104167 | 301.320000 | 5.262042 | 4191.000000 | 85.550000 |

### D. Measured runtime

Methods ran concurrently; episode wall time includes SUMO startup/close and inference but excludes the one-time model load. These shared-resource measurements are not isolated algorithm-speed benchmarks or pure inference latency.

| Method | Scenario | Seed | Wall seconds |
| --- | --- | --- | --- |
| Fixed-Time | low | 57 | 27.412971 |
| Fixed-Time | medium | 57 | 48.665407 |
| Fixed-Time | high | 57 | 114.948974 |
| Fixed-Time | imbalance | 57 | 189.996121 |
| Fixed-Time | low | 367 | 26.447514 |
| Fixed-Time | medium | 367 | 47.901318 |
| Fixed-Time | high | 367 | 117.285099 |
| Fixed-Time | imbalance | 367 | 236.250245 |
| Fixed-Time | low | 1024 | 23.974755 |
| Fixed-Time | medium | 1024 | 45.367533 |
| Fixed-Time | high | 1024 | 118.791654 |
| Fixed-Time | imbalance | 1024 | 248.552804 |
| Rule-Based | low | 57 | 25.692336 |
| Rule-Based | medium | 57 | 43.117105 |
| Rule-Based | high | 57 | 106.176726 |
| Rule-Based | imbalance | 57 | 83.468672 |
| Rule-Based | low | 367 | 24.898275 |
| Rule-Based | medium | 367 | 42.728806 |
| Rule-Based | high | 367 | 103.647567 |
| Rule-Based | imbalance | 367 | 87.550631 |
| Rule-Based | low | 1024 | 25.128441 |
| Rule-Based | medium | 1024 | 44.260788 |
| Rule-Based | high | 1024 | 108.475190 |
| Rule-Based | imbalance | 1024 | 96.523713 |
| PPO best | low | 57 | 28.094195 |
| PPO best | medium | 57 | 46.198486 |
| PPO best | high | 57 | 111.632526 |
| PPO best | imbalance | 57 | 80.428272 |
| PPO best | low | 367 | 27.107650 |
| PPO best | medium | 367 | 45.142903 |
| PPO best | high | 367 | 104.455256 |
| PPO best | imbalance | 367 | 77.382197 |
| PPO best | low | 1024 | 27.186475 |
| PPO best | medium | 1024 | 46.089228 |
| PPO best | high | 1024 | 111.266785 |
| PPO best | imbalance | 1024 | 85.260607 |

### E. Figures and source provenance

![01_summary_comparison.png](../seed100_eval_57_367_1024/plots/01_summary_comparison.png)

![02_per_seed_high_imbalance.png](../seed100_eval_57_367_1024/plots/02_per_seed_high_imbalance.png)

![03_timeseries_all_scenarios.png](../seed100_eval_57_367_1024/plots/03_timeseries_all_scenarios.png)

Figure 03 retains raw 5 s snapshot samples beneath trailing 60 s means (12 full samples, starting at t=60 s); cumulative arrivals are unchanged. This is a display transformation only. Three traffic seeds describe test variability, not training-seed uncertainty or statistical significance.

Sources: [episodes](../../evaluation/seed100_eval_57_367_1024/episodes.csv), [raw metrics](../../evaluation/seed100_eval_57_367_1024/metrics.csv), [mean/std](../seed100_eval_57_367_1024/summary_final.csv), [improvement](../seed100_eval_57_367_1024/improvement.csv), [runtime](../seed100_eval_57_367_1024/runtime.csv), [separate comparison report](drl_seed100_eval_57_367_1024_comparison.md).

