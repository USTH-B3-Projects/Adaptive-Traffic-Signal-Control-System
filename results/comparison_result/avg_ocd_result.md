## Multi-Seed Evaluation
Run both controllers using the same list of seeds for each scenario. Aggregate metric values across seeds separately for each controller.

Seeds tested: 57, 367, 1024

### High Traffic
| Metric | Fixed-Time (mean ± SD) | Rule-Based (mean ± SD) | Reduction (%) |
|---|---:|---:|---:|
| `mean_queue` (vehicles) | 81.43 ± 3.88 |  | % |
| `max_queue` (vehicles) |  | 167.00 ± 2.00 | % |
| `mean_total_waiting_time` (s) | 4400.37 ± 210.85 |  | % |
| `max_total_waiting_time` (s) | 11921.10 ± 1297.47 |  | % |

### Imbalance Traffic
| Metric | Fixed-Time (mean ± SD) | Rule-Based (mean ± SD) | Reduction (%) |
|---|---:|---:|---:|
| `mean_queue` (vehicles) | 68.23 ± 2.70 |  | % |
| `max_queue` (vehicles) | 169.33 ± 11.59 |  | % |
| `mean_total_waiting_time` (s) | 3888.35 ± 264.13 |  | % |
| `max_total_waiting_time` (s) | 12912.63 ± 395.82 |  | % |
