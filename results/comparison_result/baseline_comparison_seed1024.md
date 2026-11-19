# Baseline Experimental Results
**Status:** Draft / Initial experiment (seed 1024)

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
| Initial random seed | 1024 |
| Data source | `baseline_comparison_seed1024.jsonl` |

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
| `mean_queue` (vehicles) | 4.99 | 3.70 | 25.87% |
| `max_queue` (vehicles) | 18 | 13 | 27.78% |
| `mean_total_waiting_time` (s) | 98.82 | 51.75 | 47.63% |
| `max_total_waiting_time` (s) | 592.1 | 296.4 | 49.94% |


### 4.2. Medium Traffic
| Metric | Fixed-Time | Rule-Based | Reduction (%) |
|---|---:|---:|---:|
| `mean_queue` (vehicles) | 13.31 | 9.68 | 27.29% |
| `max_queue` (vehicles) | 39 | 28 | 28.21 |
| `mean_total_waiting_time` (s) | 244.44 | 134.41 | 45.01% |
| `max_total_waiting_time` (s) | 1106.8 | 588.4 | 46.84% |


### 4.3. High Traffic
| Metric | Fixed-Time | Rule-Based | Reduction (%) |
|---|---:|---:|---:|
| `mean_queue` (vehicles) | 47.32 | 46.02 | 2.74% |
| `max_queue` (vehicles) | 91 | 91 | 0% |
| `mean_total_waiting_time` (s) | 952.80 | 751.83 | 21.09% |
| `max_total_waiting_time` (s) | 2991.6 | 2596.4 | 13.21% |

### 4.4. Imbalanced Traffic
| Metric | Fixed-Time | Rule-Based | Reduction (%) |
|---|---:|---:|---:|
| `mean_queue` (vehicles) | 89.69 | 37.71 | 57.96% |
| `max_queue` (vehicles) | 299 | 118 | 60.54% |
| `mean_total_waiting_time` (s) | 1938.14 | 654.03 | 66.25% |
| `max_total_waiting_time` (s) | 10056.5 | 4499.2 | 55.26% |
