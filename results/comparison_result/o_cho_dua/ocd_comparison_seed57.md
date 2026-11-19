# O Cho Dua's Experimental Results
**Status:** Draft / Initial experiment (seed 57)

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
| Initial random seed | 57 |
| Data source | `ocd_comparison_seed57.jsonl` |

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

## 4. Results Test (Seed 57)

### 4.1. Low Traffic
| Metric | Fixed-Time | Rule-Based | Reduction (%) |
|---|---:|---:|---:|
| `mean_queue` (vehicles) | 19.43 | 19.53 | -0.51% |
| `max_queue` (vehicles) | 39.0 | 41.0 | -5.13% |
| `mean_total_waiting_time` (s) | 828.22 | 908.43 | -9.68% |
| `max_total_waiting_time` (s) | 1858.7 | 2214.3 | -19.13% |

### 4.2. Medium Traffic
| Metric | Fixed-Time | Rule-Based | Reduction (%) |
|---|---:|---:|---:|
| `mean_queue` (vehicles) | 39.73 | 41.06 | -3.33% |
| `max_queue` (vehicles) | 78.0 | 85.0 | -8.97% |
| `mean_total_waiting_time` (s) | 1863.32 | 2097.49 | -12.57% |
| `max_total_waiting_time` (s) | 5266.6 | 5402.8 | -2.59% |

### 4.3. High Traffic
| Metric | Fixed-Time | Rule-Based | Reduction (%) |
|---|---:|---:|---:|
| `mean_queue` (vehicles) | 73.28 | 95.45 | -30.26% |
| `max_queue` (vehicles) | 146.0 | 180.0 | -23.29% |
| `mean_total_waiting_time` (s) | 3925.37 | 5693.49 | -45.04% |
| `max_total_waiting_time` (s) | 10073.4 | 15495.5 | -53.83% |

### 4.4. Imbalanced Traffic
| Metric | Fixed-Time | Rule-Based | Reduction (%) |
|---|---:|---:|---:|
| `mean_queue` (vehicles) | 69.57 | 72.02 | -3.52% |
| `max_queue` (vehicles) | 180.0 | 188.0 | -4.44% |
| `mean_total_waiting_time` (s) | 3988.31 | 4478.97 | -12.30% |
| `max_total_waiting_time` (s) | 11313.6 | 14558.7 | -28.68% |
