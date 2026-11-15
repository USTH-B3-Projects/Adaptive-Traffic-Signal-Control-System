## Multi-Seed Evaluation
Run both controllers using the same list of seeds for each scenario. Aggregate metric values across seeds separately for each controller.

Seeds tested: 57, 367, 1024

**Notation:** This is the VERSION 1 when adapting the original control principle from baseline simple intersection. Therefore it contains large limitations, which will be improved in VERSION 2.

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
