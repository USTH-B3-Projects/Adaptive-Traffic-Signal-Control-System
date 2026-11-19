# Baseline Experimental Results
**Status:** Draft / Initial experiment (seed 57)

**Purpose:** Compare Fixed-Time and Rule-Based traffic signal controllers at a single SUMO intersection.

## 1. Objective
Evaluate the performance of two baseline controllers under the same traffic scenarios and random seeds.
- Baseline controller: Fixed-Time
- Candidate controller: Rule-Based

## 2. Experimental Setup

| Parameter | Configuration |
|---|---|
| Simulator | SUMO 1.28.0 |
| Network | Simple intersection |
| Controllers | Fixed-Time; Rule-Based |
| Scenarios | Low; Medium; High; Imbalance |
| Simulation duration | 3600 s (confirm from run configuration) |
| Initial random seed | 57 |
| Data source | `baseline_comparison_seed57.jsonl` |

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

## 4. Results — Initial Test (Seed 42)
Replace TBD with values from baseline_comparison_seed42.jsonl. Round mean values and percentages to two decimal places; integer maxima can remain integers where applicable.
### 4.1. Low Traffic
| Metric | Fixed-Time | Rule-Based | Reduction (%) |
|---|---:|---:|---:|
| `mean_queue` (vehicles) | 4.98 | 3.67 | 26.47% |
| `max_queue` (vehicles) | 17 | 12 | 29.41% |
| `mean_total_waiting_time` (s) | 96.72 | 52.97 | 45.23% |
| `max_total_waiting_time` (s) | 543.8 | 226.0 | 58.44% |


### 4.2. Medium Traffic
| Metric | Fixed-Time | Rule-Based | Reduction (%) |
|---|---:|---:|---:|
| `mean_queue` (vehicles) | 12.53 | 9.32 | 25.62% |
| `max_queue` (vehicles) | 34 | 27 | 20.59% |
| `mean_total_waiting_time` (s) | 229.62 | 128.65 | 43.97% |
| `max_total_waiting_time` (s) | 1048 | 521.8 | 50.21% |


### 4.3. High Traffic
| Metric | Fixed-Time | Rule-Based | Reduction (%) |
|---|---:|---:|---:|
| `mean_queue` (vehicles) | 42.28 | 40.7 | 3.74% |
| `max_queue` (vehicles) | 92 | 92 | 0% |
| `mean_total_waiting_time` (s) | 857.69 | 678.15 | 20.93% |
| `max_total_waiting_time` (s) | 2919.0 | 2599.5 | 10.95% |

### 4.4. Imbalanced Traffic
| Metric | Fixed-Time | Rule-Based | Reduction (%) |
|---|---:|---:|---:|
| `mean_queue` (vehicles) | 75.76 | 34.55 | 54.39% |
| `max_queue` (vehicles) | 238 | 117 | 50.84% |
| `mean_total_waiting_time` (s) | 1724.50 | 589.32 | 65.83% |
| `max_total_waiting_time` (s) | 9606.7 | 4089.6 | 57.43% |
