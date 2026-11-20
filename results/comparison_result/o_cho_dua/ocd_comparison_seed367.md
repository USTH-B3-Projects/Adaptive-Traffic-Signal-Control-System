# O Cho Dua's Experimental Results (seed 367)

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
| Initial random seed | 367 |
| Data source | `fixed_time_summary_seed367.jsonl`, `rule_based_summary_seed367.jsonl` |

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

## 4. Results (Seed 367)

### 4.1. Low Traffic
| Metric | Fixed-Time | Rule-Based | Reduction (%) |
|---|---:|---:|---:|
| `mean_queue` (vehicles) | 18.23 | 19.58 | -7.41% |
| `max_queue` (vehicles) | 39 | 44 | -12.82% |
| `mean_total_waiting_time` (s) | 721.12 | 848.47 | -17.66% |
| `max_total_waiting_time` (s) | 2016.80 | 2857.40 | -41.68% |

### 4.2. Medium Traffic
| Metric | Fixed-Time | Rule-Based | Reduction (%) |
|---|---:|---:|---:|
| `mean_queue` (vehicles) | 38.30 | 43.11 | -12.56% |
| `max_queue` (vehicles) | 76 | 82 | -7.89% |
| `mean_total_waiting_time` (s) | 1842.27 | 2341.18 | -27.08% |
| `max_total_waiting_time` (s) | 5572.40 | 6304.40 | -13.14% |

### 4.3. High Traffic
| Metric | Fixed-Time | Rule-Based | Reduction (%) |
|---|---:|---:|---:|
| `mean_queue` (vehicles) | 85.8 | 91.65 | -6.82% |
| `max_queue` (vehicles) | 165 | 163 | 1.21% |
| `mean_total_waiting_time` (s) | 4625.46 | 5162.19 | -11.6% |
| `max_total_waiting_time` (s) | 12295.5 | 11788.3 | 4.13% |

### 4.4. Imbalanced Traffic
| Metric | Fixed-Time | Rule-Based | Reduction (%) |
|---|---:|---:|---:|
| `mean_queue` (vehicles) | 65.16 | 73.24 | -12.41% |
| `max_queue` (vehicles) | 180 | 192 | -6.67% |
| `mean_total_waiting_time` (s) | 3602.14 | 4515.44 | -25.35% |
| `max_total_waiting_time` (s) | 12966.6 | 16285.4 | -25.59% |
