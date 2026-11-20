# Thang Long Avenue's Experimental Results (seed 1024)

**Purpose:** Compare Fixed-Time and Rule-Based traffic signal controllers at O Cho Dua intersection.

## 1. Objective
Evaluate the performance of two baseline controllers under the same traffic scenarios and random seeds.
- Baseline controller: Fixed-Time
- Candidate controller: Rule-Based

## 2. Experimental Setup

| Parameter | Configuration |
|---|---|
| Simulator | SUMO 1.28.0 |
| Network | BigC Thang Long |
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
| `mean_queue` (vehicles) | 5.85 | 7.72 | -32.05% |
| `max_queue` (vehicles) | 16 | 23 | -43.75% |
| `mean_total_waiting_time` (s) | 63.63 | 107.73 | -69.32% |
| `max_total_waiting_time` (s) | 239.1 | 454.6 | -90.13% |

### 4.2. Medium Traffic
| Metric | Fixed-Time | Rule-Based | Reduction (%) |
|---|---:|---:|---:|
| `mean_queue` (vehicles) | 13.90 | 22.78 | -63.88% |
| `max_queue` (vehicles) | 31 | 60 | -93.55% |
| `mean_total_waiting_time` (s) | 153.07 | 334.37 | -118.45% |
| `max_total_waiting_time` (s) | 389.3 | 1169.7 | -200.46% |

### 4.3. High Traffic
| Metric | Fixed-Time | Rule-Based | Reduction (%) |
|---|---:|---:|---:|
| `mean_queue` (vehicles) | 23.13 | 38.88 | -68.11% |
| `max_queue` (vehicles) | 44 | 99 | -125% |
| `mean_total_waiting_time` (s) | 256.59 | 556.46 | -116.87% |
| `max_total_waiting_time` (s) | 669.7 | 1937.90 | -189.37% |

### 4.4. Imbalanced Traffic
| Metric | Fixed-Time | Rule-Based | Reduction (%) |
|---|---:|---:|---:|
| `mean_queue` (vehicles) | 26.21 | 44.08 | -68.16% |
| `max_queue` (vehicles) | 72 | 122 | -69.44% |
| `mean_total_waiting_time` (s) | 295.37 | 626.56 | -112.13% |
| `max_total_waiting_time` (s) | 1204.1 | 2732.4 | -126.92% |
