# Thang Long Avenue's Experimental Results (seed 57)

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
| Initial random seed | 57 |
| Data source | `fixed_time_summary_seed57.jsonl`, `rule_based_summary_seed57.jsonl` |

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

## 4. Results Test (Seed 57)

### 4.1. Low Trafic
| Metric | Fixed-Time | Rule-Based | Reduction (%) |
|---|---:|---:|---:|
| `mean_queue` (vehicles) | 5.88 | 7.51 | -27.76% |
| `max_queue` (vehicles) | 19 | 26 | -36.84% |
| `mean_total_waiting_time` (s) | 64.41 | 105.35 | -63.56% |
| `max_total_waiting_time` (s) | 236.4 | 556.2 | -135.28% |

### 4.2. Medium Traffic
| Metric | Fixed-Time | Rule-Based | Reduction (%) |
|---|---:|---:|---:|
| `mean_queue` (vehicles) | 13.96 | 22.08 | -58.19% |
| `max_queue` (vehicles) | 30 | 58 | -93.33% |
| `mean_total_waiting_time` (s) | 153.36 | 322.30 | -110.16% |
| `max_total_waiting_time` (s) | 469.3 | 1176.2 | -150.63% |

### 4.3. High Traffic
| Metric | Fixed-Time | Rule-Based | Reduction (%) |
|---|---:|---:|---:|
| `mean_queue` (vehicles) | 23.52 | 38.73 | -64.62% |
| `max_queue` (vehicles) | 51 | 88 | -72.50% |
| `mean_total_waiting_time` (s) | 257.50 | 557.03 | -116.32% |
| `max_total_waiting_time` (s) | 612.4 | 1988.4 | -224.69% |

### 4.4. Imbalanced Traffic
| Metric | Fixed-Time | Rule-Based | Reduction (%) |
|---|---:|---:|---:|
| `mean_queue` (vehicles) | 26.54 | 44.51 | -67.68% |
| `max_queue` (vehicles) | 66 | 126 | -90.91% |
| `mean_total_waiting_time` (s) | 299.93 | 628.99 | -109.71% |
| `max_total_waiting_time` (s) | 1042.5 | 2682.9 | -158.35% |
