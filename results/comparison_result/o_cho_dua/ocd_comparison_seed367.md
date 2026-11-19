# O Cho Dua's Experimental Results
**Status:** Draft / Initial experiment (seed 367)

**Purpose:** Compare Fixed-Time and Rule-Based traffic signal controllers at O Cho Dua intersection.

**Notation:** This is the VERSION 1 when adapting the original control principle from baseline simple intersection. Therefore it contains large limitations, which will be improved in VERSION 2.

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
| Scenarios | Low; Medium; High; Imbalance |
| Simulation duration | 3600s; 3600s; 3600 s; 10800 s (confirm from run configuration) |
| Initial random seed | 367 |
| Data source | `ocd_comparison_seed367.jsonl` |

Fair comparison checklist: Confirm both controllers use the same scenario, seed, simulation duration, vehicle demand, and metric aggregation rules.

## 3. Evaluation Metrics
| JSONL metric | Unit | Meaning / calculation |
|---|---|---|
| `mean_queue` | vehicles | Mean queue count over sampled simulation states; verify aggregation. |
| `max_queue` | vehicles | Maximum queue count observed; verify aggregation. |
| `mean_total_waiting_time` | s | Mean of total waiting time measured at samples; **not necessarily average waiting time per vehicle**. |
| `max_total_waiting_time` | s | Maximum total waiting time observed at a sample. |

Reduction (%) = (Fixed-Time - Rule-Based) / Fixed-Time × 100

A positive reduction means a lower value under Rule-Based. For these four metrics, lower values are preferable, assuming consistent measurement definitions.

## 4. Results (Seed 367)

### 4.1. Low Traffic
| Metric | Fixed-Time | Rule-Based | Reduction (%) |
|---|---:|---:|---:|
| `mean_queue` (vehicles) | 18.30 | 19.99 | -9.23% |
| `max_queue` (vehicles) | 37.0 | 41.0 | -10.81% |
| `mean_total_waiting_time` (s) | 724.71 | 874.75 | -20.70% |
| `max_total_waiting_time` (s) | 2018.2 | 2502.60 | -24.00% |

### 4.2. Medium Traffic
| Metric | Fixed-Time | Rule-Based | Reduction (%) |
|---|---:|---:|---:|
| `mean_queue` (vehicles) | 39.83 | 42.55 | -6.82% |
| `max_queue` (vehicles) | 86.0 | 82.0 | 4.65% |
| `mean_total_waiting_time` (s) | 1901.21 | 2306.79 | -21.33% |
| `max_total_waiting_time` (s) | 5125.1 | 5264.1 | -2.71% |

### 4.3. High Traffic
| Metric | Fixed-Time | Rule-Based | Reduction (%) |
|---|---:|---:|---:|
| `mean_queue` (vehicles) | 83.25 | 81.59 | 2.00% |
| `max_queue` (vehicles) | 169.0 | 162.0 | 4.14% |
| `mean_total_waiting_time` (s) | 4499.80 | 4647.85 | -3.29% |
| `max_total_waiting_time` (s) | 11465.2 | 10877.6 | 5.13% |

### 4.4. Imbalanced Traffic
| Metric | Fixed-Time | Rule-Based | Reduction (%) |
|---|---:|---:|---:|
| `mean_queue` (vehicles) | 67.60 | 72.39 | -7.08% |
| `max_queue` (vehicles) | 175.0 | 172.0 | 1.71% |
| `mean_total_waiting_time` (s) | 3850.40 | 4496.08 | -16.77% |
| `max_total_waiting_time` (s) | 12139.2 | 14774.2 | -21.71% |