## Multi-Seed Evaluation
Run both controllers using the same list of seeds for each scenario. Aggregate metric values across seeds separately for each controller.

Seeds tested: 57, 367, 1024

**Notation:** This is the VERSION 1 when adapting the original control principle from baseline simple intersection. Therefore it contains large limitations, which will be improved in VERSION 2.

### Low Traffic
| Metric | FT (mean ± SD) | RB (mean ± SD) | Reduction |
|---|---:|---:|---:|
| `mean_queue` (vehicles) | 18.69 ± 0.64 | 19.59 ± 0.37 | −4.85% |
| `max_queue` (vehicles) | 37.00 ± 2.00 | 41.33 ± 0.58 | −11.71% |
| `mean_total_waiting_time` (s) | 770.40 ± 52.81 | 873.77 ± 35.16 | −13.42% |
| `max_total_waiting_time` (s) | 1931.67 ± 80.61 | 2276.97 ± 201.74 | −17.88% |

### Medium Traffic
| Metric | FT (mean ± SD) | RB (mean ± SD) | Reduction |
|---|---:|---:|---:|
| `mean_queue` (vehicles) | 39.77 ± 0.05 | 41.58 ± 0.84 | −4.54% |
| `max_queue` (vehicles) | 82.33 ± 4.04 | 85.33 ± 3.51 | −3.64% |
| `mean_total_waiting_time` (s) | 1960.12 ± 136.17 | 2276.71 ± 166.23 | −16.15% |
| `max_total_waiting_time` (s) | 5179.83 ± 75.99 | 5895.67 ± 976.25 | −13.82% |

### High Traffic
| Metric | FT (mean ± SD) | RB (mean ± SD) | Reduction |
|---|---:|---:|---:|
| `mean_queue` (vehicles) | 82.81 ± 9.31 | 90.11 ± 7.46 | −8.82% |
| `max_queue` (vehicles) | 158.33 ± 11.59 | 171.33 ± 9.02 | −8.21% |
| `mean_total_waiting_time` (s) | 4548.90 ± 649.47 | 5330.16 ± 591.31 | −17.17% |
| `max_total_waiting_time` (s) | 11728.90 ± 1801.88 | 12976.17 ± 2337.53 | −10.63% |

### Imbalance Traffic
| Metric | FT (mean ± SD) | RB (mean ± SD) | Reduction |
|---|---:|---:|---:|
| `mean_queue` (vehicles) | 70.01 ± 2.66 | 72.87 ± 1.16 | −4.08% |
| `max_queue` (vehicles) | 175.00 ± 5.00 | 180.67 ± 8.08 | −3.24% |
| `mean_total_waiting_time` (s) | 4010.71 ± 172.61 | 4493.93 ± 14.01 | −12.05% |
| `max_total_waiting_time` (s) | 12068.13 ± 721.63 | 13941.37 ± 1260.49 | −15.52% |
