## Multi-Seed Evaluation (To Be Completed)
Run both controllers using the same list of seeds for each scenario. Aggregate metric values across seeds separately for each controller.

Seeds tested: 57, 367, 1024

### Low Traffic
| Metric | Fixed-Time (mean ± SD) | Rule-Based (mean ± SD) | Reduction (%) |
|---|---:|---:|---:|
| `mean_queue` | 4.96 ± 0.04 | 3.62 ± 0.11 | 27.01% |
| `max_queue` | 18.00 ± 1.00 | 13.00 ± 1.00 | 27.78% |
| `mean_total_waiting_time` | 97.88 ± 1.07 | 51.50 ± 1.62 | 47.39% |
| `max_total_waiting_time` | 567.63 ± 24.16 | 281.50 ± 49.75 | 50.41% |

### Medium Traffic
| Metric | Fixed-Time (mean ± SD) | Rule-Based (mean ± SD) | Reduction (%) |
|---|---:|---:|---:|
| `mean_queue` | 12.93 ± 0.39 | 9.48 ± 0.18 | 26.67% |
| `max_queue` | 35.67 ± 2.89 | 28.00 ± 1.00 | 21.50% |
| `mean_total_waiting_time` | 238.83 ± 8.04 | 131.17 ± 2.95 | 45.08% |
| `max_total_waiting_time` | 1037.87 ± 74.52 | 586.27 ± 63.43 | 43.51% |

### High Traffic
| Metric | Fixed-Time (mean ± SD) | Rule-Based (mean ± SD) | Reduction (%) |
|---|---:|---:|---:|
| `mean_queue` | 45.58 ± 2.86 | 42.07 ± 3.47 | 7.70% |
| `max_queue` | 93.33 ± 3.21 | 92.67 ± 2.08 | 0.71% |
| `mean_total_waiting_time` | 939.12 ± 75.53 | 693.94 ± 51.83 | 26.11% |
| `max_total_waiting_time` | 3160.43 ± 357.15 | 2471.07 ± 219.77 | 21.81% |

### Imbalance Traffic
| Scenario | Metric | Fixed-Time (mean ± SD) | Rule-Based (mean ± SD) | Reduction (%) |
|---|---:|---:|---:|
| `mean_queue` | 82.78 ± 6.97 | 38.56 ± 4.49 | 53.42% |
| `max_queue` | 259.67 ± 34.12 | 119.67 ± 3.79 | 53.92% |
| `mean_total_waiting_time` | 1850.26 ± 111.75 | 692.27 ± 126.49 | 62.59% |
| `max_total_waiting_time` | 10014.07 ± 387.89 | 4879.00 ± 1033.06 | 51.28% |

Number of repetitions per scenario: 3/controller