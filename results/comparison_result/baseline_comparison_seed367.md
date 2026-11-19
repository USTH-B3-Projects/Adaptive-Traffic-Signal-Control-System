# Baseline Experimental Results
**Status:** Draft / Initial experiment (seed 367)

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
| Initial random seed | 367 |
| Data source | `baseline_comparison_seed367.jsonl` |

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
| `mean_queue` (vehicles) | 4.91 | 3.5 | 28.71% |
| `max_queue` (vehicles) | 19 | 14 | 26.32% |
| `mean_total_waiting_time` (s) | 98.1 | 49.76 | 49.27% |
| `max_total_waiting_time` (s) | 567.0 | 322.1 | 43.19% |


### 4.2. Medium Traffic
| Metric | Fixed-Time | Rule-Based | Reduction (%) |
|---|---:|---:|---:|
| `mean_queue` (vehicles) | 12.95 | 9.45 | 27.06% |
| `max_queue` (vehicles) | 34 | 29 | 14.71% |
| `mean_total_waiting_time` (s) | 242.44 | 130.43 | 46.2% |
| `max_total_waiting_time` (s) | 958.8 | 648.6 | 32.35% |


### 4.3. High Traffic
| Metric | Fixed-Time | Rule-Based | Reduction (%) |
|---|---:|---:|---:|
| `mean_queue` (vehicles) | 47.15 | 39.5 | 16.22% |
| `max_queue` (vehicles) | 97 | 95 | 2.06% |
| `mean_total_waiting_time` (s) | 1006.88 | 651.84 | 35.26% |
| `max_total_waiting_time` (s) | 3570.7 | 2217.3 | 37.9% |

### 4.4. Imbalanced Traffic
| Metric | Fixed-Time | Rule-Based | Reduction (%) |
|---|---:|---:|---:|
| `mean_queue` (vehicles) | 82.88 | 43.42 | 47.62% |
| `max_queue` (vehicles) | 242 | 124 | 48.76% |
| `mean_total_waiting_time` (s) | 1888.15 | 833.46 | 55.86% |
| `max_total_waiting_time` (s) | 10379.0 | 6048.2 | 41.73% |
