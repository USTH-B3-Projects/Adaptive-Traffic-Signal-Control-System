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
| `mean_queue` (vehicles) | 5.82 ± 0.08	| 7.16 ± 0.81 |	−23.00% |
| `max_queue` (vehicles) | 14.00 ± 1.73 | 23.00 ± 3.00 | −35.29% |
| `mean_total_waiting_time` (s) | 63.90 ± 0.44 | 98.68 ± 13.67 | −54.42% |
| `max_total_waiting_time` (s) | 250.13 ± 21.49 | 457.80 ± 96.84 | −83.02% |

### Medium Traffic
| Metric | FT (mean ± SD) | RB (mean ± SD) | Reduction |
|---|---:|---:|---:|
| `mean_queue` (vehicles) | 13.72 ± 0.36 | 22.14 ± 0.61 | −61.35% |
| `max_queue` (vehicles) | 31.00 ± 1.00 | 56.33 ± 4.73 | −81.72% |
| `mean_total_waiting_time` (s) | 151.21 ± 3.47 | 331.72 ± 8.41 | −119.37% |
| `max_total_waiting_time` (s) | 413.83 ± 48.14 | 1144.80 ± 48.87 | −176.63% |

### High Traffic
| Metric | FT (mean ± SD) | RB (mean ± SD) | Reduction |
|---|---:|---:|---:|
| `mean_queue` (vehicles) | 23.18 ± 0.31 | 38.46 ± 0.59 | −65.89% |
| `max_queue` (vehicles) | 48.00 ± 3.61 | 92.67 ± 5.69 | −93.06% |
| `mean_total_waiting_time` (s) | 255.94 ± 1.96 | 550.61 ± 10.62 | −115.13% |
| `max_total_waiting_time` (s) | 622.40 ± 43.18 | 1951.87 ± 31.93 | −213.60% |

### Imbalance Traffic
| Metric | FT (mean ± SD) | RB (mean ± SD) | Reduction |
|---|---:|---:|---:|
| `mean_queue` (vehicles) | 26.29 ± 0.22 | 44.27 ± 0.22 | −68.37% |
| `max_queue` (vehicles) | 70.67 ± 4.16 | 123.33 ± 2.31 | −74.53% |
| `mean_total_waiting_time` (s) | 295.64 ± 4.15 | 627.57 ± 1.27 | −112.27% |
| `max_total_waiting_time` (s) | 1101.30 ± 89.33 | 2679.60 ± 54.62 | −143.31% |
