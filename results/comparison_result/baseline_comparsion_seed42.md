# Baseline Experimental Results
**Status:** Draft / Initial experiment (seed 42)

**Purpose:** Compare Fixed-Time and Rule-Based traffic signal controllers at a single SUMO intersection.

## 1. Objective
Evaluate the performance of two baseline controllers under the same traffic scenarios and random seeds.
- Baseline controller: Fixed-Time
- Candidate controller: Rule-Based
- Research question: Does the Rule-Based controller improve queue and waiting-time metrics compared with Fixed-Time?

## 2. Experimental Setup

| Parameter | Configuration |
|---|---|
| Simulator | SUMO 1.28.0 |
| Network | Simple intersection |
| Controllers | Fixed-Time; Rule-Based |
| Scenarios | Low; Medium; High; Imbalance |
| Simulation duration | 3600 s (confirm from run configuration) |
| Initial random seed | 42 |
| Additional random seeds | TBD |
| Sampling interval | TBD |
| Data source | `baseline_comparison_seed42.jsonl` |

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
| `mean_queue` (vehicles) | 4.60 | 3.53 | 23.39% |
| `max_queue` (vehicles) | 16 | 12 | 25% |
| `mean_total_waiting_time` (s) | 89.76 | 50.03 | 44.25% |
| `max_total_waiting_time` (s) | 468.3 | 243 | 48.11% |


### 4.2. Medium Traffic
| Metric | Fixed-Time | Rule-Based | Reduction (%) |
|---|---:|---:|---:|
| `mean_queue` (vehicles) | 11.82 | 8.98 | 23.97% |
| `max_queue` (vehicles) | 32 | 26 | 18.75% |
| `mean_total_waiting_time` (s) | 219.65 | 126.96 | 42.2% |
| `max_total_waiting_time` (s) | 913.7 | 555.1 | 39.25% |


### 4.3. High Traffic
| Metric | Fixed-Time | Rule-Based | Reduction (%) |
|---|---:|---:|---:|
| `mean_queue` (vehicles) | 49.02 | 38.16 | 22.16% |
| `max_queue` (vehicles) | 127 | 92 | 27.56% |
| `mean_total_waiting_time` (s) | 1051.28 | 622.24 | 40.81% |
| `max_total_waiting_time` (s) | 3710.9 | 2088.8 | 43.71% |


### 4.4. Imbalanced Traffic
| Metric | Fixed-Time | Rule-Based | Reduction (%) |
|---|---:|---:|---:|
| `mean_queue` (vehicles) | 83.04 | 37.09 | 55.33% |
| `max_queue` (vehicles) | 226 | 129 | 42.92% |
| `mean_total_waiting_time` (s) | 1809.59 | 683.95 | 62.2% |
| `max_total_waiting_time` (s) | 8678.3 | 3891.9 | 55.15% |