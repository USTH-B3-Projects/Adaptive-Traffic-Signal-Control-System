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
| Scenarios | High; Imbalance |
| Simulation duration | 3600 s; 10800 s (confirm from run configuration) |
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
