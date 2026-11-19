# O Cho Dua's Experimental Results
**Status:** Draft / Initial experiment (seed 1024)

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
| Initial random seed | 1024 |
| Data source | `ocd_comparison_seed1024.jsonl` |

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

## 4. Results (Seed 1024)

### 4.1. Low Traffic
| Metric | Fixed-Time | Rule-Based | Reduction (%) |
|---|---:|---:|---:|
| `mean_queue` (vehicles) | 18.33 | 19.26 | -5.09% |
| `max_queue` (vehicles) | 35.0 | 42.0 | -20.00% |
| `mean_total_waiting_time` (s) | 758.27 | 838.14 | -10.53% |
| `max_total_waiting_time` (s) | 1918.1 | 2114.0 | -10.21% |

### 4.2. Medium Traffic
| Metric | Fixed-Time | Rule-Based | Reduction (%) |
|---|---:|---:|---:|
| `mean_queue` (vehicles) | 39.76 | 41.13 | -3.46% |
| `max_queue` (vehicles) | 83.0 | 89.0 | -7.23% |
| `mean_total_waiting_time` (s) | 2115.83 | 2425.84 | -14.65% |
| `max_total_waiting_time` (s) | 5147.8 | 7020.1 | -36.37% |

### 4.3. High Traffic
| Metric | Fixed-Time | Rule-Based | Reduction (%) |
|---|---:|---:|---:|
| `mean_queue` (vehicles) | 91.89 | 93.30 | -1.53% |
| `max_queue` (vehicles) | 160.0 | 172.0 | -7.50% |
| `mean_total_waiting_time` (s) | 5221.52 | 5649.13 | -8.19% |
| `max_total_waiting_time` (s) | 13648.10 | 12555.4 | 8.01% |

### 4.4. Imbalanced Traffic
| Metric | Fixed-Time | Rule-Based | Reduction (%) |
|---|---:|---:|---:|
| `mean_queue` (vehicles) | 72.87 | 74.19 | -1.81% |
| `max_queue` (vehicles) | 170.0 | 182.0 | -7.06% |
| `mean_total_waiting_time` (s) | 4193.43 | 4506.74 | -7.47% |
| `max_total_waiting_time` (s) | 12751.6 | 12491.2 | 2.04% |
