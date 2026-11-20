# O Cho Dua's Experimental Results (seed 1024)

**Purpose:** Compare Fixed-Time and Rule-Based traffic signal controllers at O Cho Dua intersection.

## 1. Objective
Evaluate the performance of two baseline controllers under the same traffic scenarios and random seeds.
- Baseline controller: Fixed-Time
- Candidate controller: Rule-Based

## 2. Experimental Setup

| Parameter | Configuration |
|---|---|
| Simulator | SUMO 1.28.0 |
| Network | O Cho Dua |
| Controllers | Fixed-Time; Rule-Based |
| Scenarios | High; Imbalance |
| Simulation duration | 3600 s; 10800 s (confirm from run configuration) |
| Initial random seed | 1024 |
| Data source | `fixed_time_summary_seed1024.jsonl`, `rule_based_summary_seed1024.jsonl` |

Fair comparison checklist: Confirm both controllers use the same scenario, seed, simulation duration, vehicle demand, and metric aggregation rules.

## 3. Evaluation Metrics
| JSONL metric | Unit | Meaning / calculation |
|---|---|---|
| `mean_queue` | vehicles | Mean queue count over sampled simulation states; verify aggregation. |
| `max_queue` | vehicles | Maximum queue count observed; verify aggregation. |
| `mean_total_waiting_time` | s | Mean of total waiting time measured at samples; **not necessarily average waiting time per vehicle**. |
| `max_total_waiting_time` | s | Maximum total waiting time observed at a sample. |

$$
\text{Reduction}=\frac{\text{Fixed-Time}-\text{Rule-Based}}{\text{Fixed-Time}}\times100\%
$$

A positive reduction means a lower value under Rule-Based. For these four metrics, lower values are preferable, assuming consistent measurement definitions.

## 4. Results (Seed 1024)

### 4.1. Low Traffic
| Metric | Fixed-Time | Rule-Based | Reduction (%) |
|---|---:|---:|---:|
| `mean_queue` (vehicles) | 18.36 | 18.58 | -1.20% |
| `max_queue` (vehicles) | 35 | 38 | -8.57% |
| `mean_total_waiting_time` (s) | 763.05 | 876.72 | -14.90% |
| `max_total_waiting_time` (s) | 2065.10 | 2188.60 | -5.98% |

### 4.2. Medium Traffic
| Metric | Fixed-Time | Rule-Based | Reduction (%) |
|---|---:|---:|---:|
| `mean_queue` (vehicles) | 39.54 | 41.17 | -4.12% |
| `max_queue` (vehicles) | 78 | 92 | -17.95% |
| `mean_total_waiting_time` (s) | 1977.55 | 2284.51 | -15.52% |
| `max_total_waiting_time` (s) | 5495.90 | 6473.9 | -17.8% |

### 4.3. High Traffic
| Metric | Fixed-Time | Rule-Based | Reduction (%) |
|---|---:|---:|---:|
| `mean_queue` (vehicles) | 78.3625 | 96.92 | -23.68% |
| `max_queue` (vehicles) | 167 | 178 | -6.59% |
| `mean_total_waiting_time` (s) | 4207.47 | 6247.88 | -48.49% |
| `max_total_waiting_time` (s) | 10477.6 | 23363.2 | -122.98% |

### 4.4. Imbalanced Traffic
| Metric | Fixed-Time | Rule-Based | Reduction (%) |
|---|---:|---:|---:|
| `mean_queue` (vehicles) | 70.24 | 76.21 | -8.5% |
| `max_queue` (vehicles) | 157 | 170 | -8.28% |
| `mean_total_waiting_time` (s) | 3940.18 | 4848.19 | -23.04% |
| `max_total_waiting_time` (s) | 12492.6 | 13267.2 | -6.2% |
