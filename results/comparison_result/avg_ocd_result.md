## Multi-Seed Evaluation
Run both controllers using the same list of seeds for each scenario. Aggregate metric values across seeds separately for each controller.

Seeds tested: 57, 367, 1024

$$
\text{Reduction}=
\frac{\overline{FT}-\overline{RB}}{\overline{FT}}\times100\%
$$

### Low Traffic
| Metric | FT (mean ± SD) | RB (mean ± SD) | Reduction |
|---|---:|---:|---:|
| `mean_queue` (vehicles) | 18.63 ± 0.58 | 18.81 ± 0.68 | −0.97% |
| `max_queue` (vehicles) | 37.33 ± 2.08 | 40.67 ± 3.06 | −8.93% |
| `mean_total_waiting_time` (s) | 769.97 ± 52.65 | 844.16 ± 34.91 | −9.64% |
| `max_total_waiting_time` (s) | 2004.23 ± 68.03 | 2402.50 ± 394.19 | −19.87% |

### Medium Traffic
| Metric | FT (mean ± SD) | RB (mean ± SD) | Reduction |
|---|---:|---:|---:|
| `mean_queue` (vehicles) | 39.11 ± 0.70 | 41.57 ± 1.39 | −6.27% |
| `max_queue` (vehicles) | 77.33 ± 1.15 | 87.00 ± 5.00 | −12.50% |
| `mean_total_waiting_time` (s) | 1906.26 ± 67.94 | 2203.15 ± 192.10 | −15.57% |
| `max_total_waiting_time` (s) | 5331.37 ± 353.31 | 5664.57 ± 1257.87 | −6.25% |

### High Traffic
| Metric | FT (mean ± SD) | RB (mean ± SD) | Reduction |
|---|---:|---:|---:|
| `mean_queue` (vehicles) | 81.43 ± 3.88 | 91.22 ± 5.94 | −12.02% |
| `max_queue` (vehicles) | 167.00 ± 2.00 | 175.00 ± 10.82 | −4.79% |
| `mean_total_waiting_time` (s) | 4400.37 ± 210.85 | 5535.34 ± 617.31 | −25.79% |
| `max_total_waiting_time` (s) | 11921.10 ± 1297.47 | 17033.20 ± 5863.25 | −42.88% |

### Imbalance Traffic
| Metric | FT (mean ± SD) | RB (mean ± SD) | Reduction |
|---|---:|---:|---:|
| `mean_queue` (vehicles) | 68.23 ± 2.70 | 73.45 ± 2.66 | −7.66% |
| `max_queue` (vehicles) | 169.33 ± 11.59 | 177.67 ± 12.42 | −4.92% |
| `mean_total_waiting_time` (s) | 3888.35 ± 264.13 | 4607.46 ± 210.39 | −18.49% |
| `max_total_waiting_time` (s) | 12912.63 ± 395.82 | 14599.93 ± 1539.71 | −13.07% |
