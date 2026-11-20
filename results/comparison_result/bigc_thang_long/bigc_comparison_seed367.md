# Thang Long Avenue's Experimental Results (seed 367)

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
| `mean_queue` (vehicles) | 5.73 | 6.24 | -8.87% |
| `max_queue` (vehicles) | 16 | 20 | -25% |
| `mean_total_waiting_time` (s) | 63.76 | 82.94 | -30.27% |
| `max_total_waiting_time` (s) | 274.9 | 362.6 | -31.9% |

### 4.2. Medium Traffic
| Metric | Fixed-Time | Rule-Based | Reduction (%) |
|---|---:|---:|---:|
| `mean_queue` (vehicles) | 13.31 | 21.57 | -62.03% |
| `max_queue` (vehicles) | 32 | 51 | -59.38% |
| `mean_total_waiting_time` (s) | 147.20 | 338.48 | -129.94% |
| `max_total_waiting_time` (s) | 382.9 | 1088.5 | -184.28% |

### 4.3. High Traffic
| Metric | Fixed-Time | Rule-Based | Reduction (%) |
|---|---:|---:|---:|
| `mean_queue` (vehicles) | 22.9 | 37.78 | -64.96% |
| `max_queue` (vehicles) | 49 | 91 | -85.71% |
| `mean_total_waiting_time` (s) | 253.74 | 538.35 | -112.17% |
| `max_total_waiting_time` (s) | 585.1 | 1929.3 | -229.74% |

### 4.4. Imbalanced Traffic
| Metric | Fixed-Time | Rule-Based | Reduction (%) |
|---|---:|---:|---:|
| `mean_queue` (vehicles) | 26.12 | 44.21 | -69.27% |
| `max_queue` (vehicles) | 74 | 122 | -64.86% |
| `mean_total_waiting_time` (s) | 291.64 | 627.16 | -115.05% |
| `max_total_waiting_time` (s) | 1057.3 | 2623.5 | -148.13% |
