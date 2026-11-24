# Tổng kết V1 — Baseline và DRL PPO: Seed 107 / Seed 710

Ngày tổng hợp: **22/11/2026**. Phạm vi: dữ liệu lịch sử; không sửa code/config, không chạy SUMO/train/evaluate.

## 1. Tổng quan kiến trúc V1 & Thời gian thực thi

| Thành phần | Cấu hình chung V1 |
|---|---|
| Nền tảng | SUMO 1.28.0 + TraCI; PPO Stable-Baselines3 2.9.2; 1 TLS, 4 scenario |
| Observation | **6D gộp tổng**: queue, waiting, speed, vehicle_count, phase_id, green_elapsed |
| Thông tin hướng | Không có queue/wait NS–EW trong observation; StateExtractor có sẵn dữ liệu từng làn |
| Chuẩn hóa | Input raw, không VecNormalize; reward raw, không reward scaling/clipping riêng |
| Reward | `r = -(Q + 0.1*W)`; Q là số xe dừng, W là tổng current waiting trên incoming lanes |
| Action | `Discrete(2)`: 0=KEEP, 1=SWITCH; request có thể bị controller ghi đè |
| Thời gian | SUMO step=0.1 s; quyết định mỗi 5 s=50 substeps; episode tối đa 3600 s≈720 quyết định |
| Đèn | **min_green=30 s**, **max_green=75 s**; vàng 3 s; toàn đỏ thực tế 3 s dù YAML all_red_time=0 |
| Mạng | MlpPolicy; actor/critic mỗi nhánh [64,64], Tanh; Adam |
| PPO rollout | **n_steps=2048**, n_envs=1, batch_size=64, n_epochs=10 |
| PPO tối ưu | **lr=3e-4 cố định**; gamma=0.99, gae_lambda=0.95, clip_range=0.2 |
| PPO bổ sung | ent_coef=0, vf_coef=0.5, max_grad_norm=0.5, target_kl=None; normalize_advantage=True |
| Multi-scenario | Random mỗi episode, xác suất kỳ vọng 25%/scenario; không quota cân bằng |

Kiến trúc/defaults lấy từ [Parameter Audit](../parameter_audit_report.md); normalize_advantage không chuẩn hóa input/reward.

| Hạng mục thực thi | Seed 107 | Seed 710 |
|---|---:|---:|
| Budget yêu cầu | 800,000 RL steps | 600,000 RL steps |
| RL steps thực lưu | 800,768 | 600,064 |
| PPO training | 98558.77 s ≈ 27.38 giờ | 74922.30 s ≈ 20.81 giờ |
| PPO evaluation — tổng 4 scenario | 300.29 s | 364.58 s |
| Toàn pipeline | 99558.18 s ≈ 27.66 giờ | 76022.20 s ≈ 21.12 giờ |

Seed710 dùng CUDA theo log; không suy ra thiết bị runtime của seed107 chỉ từ device=auto.
Steps thực lưu vượt nhẹ budget do PPO thu trọn rollout; không phải số gradient updates hay SUMO substeps.
Runtime evaluation ở trên là tổng bốn kịch bản, không phải thời gian riêng cho từng kịch bản.
Nguồn runtime: [107 timings](../seed107/pipeline_timings.json), [710 timings](../seed710/pipeline_timings.json).

## 2. Bảng so sánh kết quả giao thông

Giữ nguyên ý nghĩa chỉ số V1 và làm tròn 2 chữ số; chưa hiệu chỉnh lỗi đo lường.
Ở hai cột baseline, cặp **107 / 710** là hai lần chạy riêng; không lấy trung bình hoặc dùng chung một baseline.

| Kịch bản | Chỉ số | Fixed-Time (107 / 710) | Rule-Based (107 / 710) | DRL Seed107 | DRL Seed710 |
|---|---|---:|---:|---:|---:|
| low | `queue_length` | 4.65 / 4.29 | 3.75 / 3.54 | 3.22 | 3.55 |
| low | `waiting_time` | 91.26 / 82.31 | 54.44 / 50.40 | 45.26 | 50.04 |
| low | `average_speed` | 8.56 / 8.75 | 7.34 / 7.48 | 7.50 | 7.42 |
| low | `arrived_count` | 1174.00 / 1207.00 | 25.00 / 28.00 | 17.85 | 13.22 |
| low | `vehicles_in_network` | 19.53 / 19.69 | 18.34 / 18.68 | 17.07 | 18.31 |
| medium | `queue_length` | 12.53 / 12.35 | 9.80 / 10.17 | 9.01 | 9.63 |
| medium | `waiting_time` | 233.16 / 221.51 | 139.82 / 146.09 | 125.34 | 135.17 |
| medium | `average_speed` | 8.08 / 8.12 | 6.84 / 6.77 | 6.92 | 6.80 |
| medium | `arrived_count` | 2982.00 / 3014.00 | 76.00 / 72.00 | 36.22 | 35.86 |
| medium | `vehicles_in_network` | 52.82 / 53.27 | 49.34 / 50.31 | 46.92 | 49.32 |
| high | `queue_length` | 51.80 / 49.56 | 38.77 / 42.74 | 33.99 | 54.97 |
| high | `waiting_time` | 1172.51 / 1028.96 | 649.68 / 700.88 | 555.05 | 962.12 |
| high | `average_speed` | 5.42 / 5.63 | 4.16 / 3.99 | 4.60 | 3.40 |
| high | `arrived_count` | 5275.00 / 5389.00 | 113.00 / 130.00 | 72.93 | 52.66 |
| high | `vehicles_in_network` | 143.50 / 141.21 | 126.36 / 134.01 | 116.13 | 153.68 |
| imbalance | `queue_length` | 83.04 / 97.63 | 36.58 / 40.27 | 46.34 | 65.47 |
| imbalance | `waiting_time` | 1962.03 / 2283.80 | 706.89 / 733.60 | 815.19 | 1117.53 |
| imbalance | `average_speed` | 3.42 / 3.10 | 3.60 / 3.44 | 2.89 | 2.32 |
| imbalance | `arrived_count` | 3888.00 / 3961.00 | 142.00 / 123.00 | 44.35 | 46.44 |
| imbalance | `vehicles_in_network` | 185.59 / 213.55 | 110.17 / 119.57 | 128.20 | 166.15 |

Quy ước đơn vị và phép tổng hợp:
Queue là số xe dừng, không phải mét; queue/wait/speed/vehicles_in_network trong bảng là trung bình các snapshot.
Waiting có đơn vị giây: trung bình tổng current waiting trên incoming lanes, không phải waiting trung bình mỗi xe.
Speed có đơn vị m/s; vehicles_in_network là số xe toàn mạng; lower tốt hơn cho queue/wait/backlog.
Arrived_count của baseline là cumulative cuối log; của PPO là mean của cumulative snapshots, nên không tương đương.

Các sai lệch V1 đã xác nhận trong [Audit Supplement](../parameter_audit_supplement.md):
**Lệch seed:** PPO sinh seed SUMO mới từ RNG; baseline truyền thẳng CLI seed, nên traffic không được ghép cặp.
**Thiếu arrivals:** RB/PPO chỉ cộng arrivals của substep cuối mỗi interval; không dùng arrived_count này để kết luận throughput.
**Lệch speed:** Fixed-Time đo toàn mạng, RB/PPO đo incoming lanes; snapshot đầu/cuối interval cũng chưa đồng bộ.

Diễn giải có điều kiện theo số liệu đã lưu:
Seed107 giảm waiting so với RB: low 16.87%, medium 10.35%, **high 14.57%**; imbalance lại tăng 15.32%.
Seed710 gần RB ở low, giảm waiting 7.48% ở medium; **high tăng 37.27%, imbalance tăng 52.33%**.
Do đó không kết luận cả hai seed đều thua RB ở High; lợi thế/kém hơn trên chưa là bằng chứng thống kê công bằng.
Khác seed và khác budget cũng không cho phép quy chênh lệch 107–710 chỉ cho số bước train.

Nguồn số chính: [CSV107](../seed107/summary_final.csv), [CSV710](../seed710/summary_final.csv).
Đã đọc đối chiếu [report107](drl_seed107_report.md), [report710](drl_seed710_report.md).
`results/summary_final.csv` không có trong snapshot này; dùng CSV theo seed thay cho đường dẫn cũ trong report.

## 3. Phân tích hội tụ từ TensorBoard (train/*)

Chỉ tổng hợp số đã trích trong [Audit Supplement, mục4](../parameter_audit_supplement.md); không đọc/chạy model mới.
Seed107 tương ứng runs/ppo_overnight (390 mẫu/tag); seed710 là runs/ppo_seed710 (292 mẫu/tag).
Mean trên các scalar đã log; min/max toàn chuỗi, không smoothing. Số hiển thị được làm tròn.

| Chỉ số | 107 mean | 107 min … max | 107 cuối | 710 mean | 710 min … max | 710 cuối |
|---|---:|---:|---:|---:|---:|---:|
| `train/value_loss` | 3.4670e+6 | 1.6910e+3 … 1.1126e+8 | 7.4202e+5 | 3.5230e+6 | 1.8313e+3 … 2.2951e+7 | 3.4730e+6 |
| `train/explained_variance` | 0.063883 | -1.332045 … 0.867931 | 0.392334 | 0.049510 | -0.236516 … 0.839685 | 0.028571 |
| `train/approx_kl` | 0.003066 | 0.000014 … 0.036893 | 0.003077 | 0.002775 | 0.000037 … 0.041043 | 0.007122 |
| `train/entropy_loss` | -0.469096 | -0.693056 … -0.230427 | -0.383993 | -0.475186 | -0.685668 … -0.126658 | -0.435915 |

Giá trị cuối được log tại RL step800768 (107) và600064 (710); chuỗi train/* bắt đầu tại4096.
**Critic:** explained_variance mean chỉ≈0.064/0.050, có đoạn âm; cuối seed710≈0.029 cho thấy dự đoán return yếu.
Value_loss có biên độ rất lớn, cuối seed710 cao hơn seed107; loss tuyệt đối còn phụ thuộc scale reward/return.
**Policy:** entropy_loss âm là âm entropy; gần0 hơn nghĩa ít entropy hơn, không phải tăng khám phá.
Approx_KL mean≈0.003 nhưng max≈0.037/0.041; mean nhỏ không bảo đảm mọi update nhỏ, target_kl hiện không đặt.

Cơ chế có thể góp phần gây mất ổn định, chưa được chứng minh nhân quả bằng ablation:
Input raw đi vào Tanh và reward raw khác scale giữa các tải gây khó tối ưu critic; advantage normalization không sửa value target.
Observation gộp mất hướng, trong khi RB so trực tiếp Q_NS/Q_EW; bất lợi rõ với Imbalance có nhu cầu NS gấp6 lần EW.
Chọn scenario ngẫu nhiên, mỗi rollout≈2.84 episode nên không bảo đảm đủ4 tải; lr cố định/ent_coef=0 là rủi ro cần kiểm chứng.
V1 chưa chứng minh vượt RB ổn định trên mọi tải; riêng seed107 High có kết quả tốt hơn theo bảng.
Log train/* gộp scenario không xác định riêng chất lượng critic High/Imbalance, cũng không chứng minh checkpoint500k tốt nhất.

## 4. Kết luận & Cơ sở nâng cấp lên V2 (Seed 100)

- **Đồng bộ đánh giá:** sửa arrivals từng substep, thống nhất phạm vi/sampling speed và định nghĩa metric; lưu seed SUMO thực, dùng bộ seed đánh giá chung và nhiều lần lặp cho cả3 phương pháp.
- **Nâng observation:** đưa queue/vehicle/wait theo NS–EW từ lanes vào policy, chuẩn hóa từng biến và mã hóa phase rõ ràng; kiểm tra action bị override/masking thay vì chỉ tăng budget.
- **Ổn định reward và PPO:** kiểm soát scale reward/return giữa tải, khai báo explicit PPO/dependencies; kiểm chứng LR schedule, entropy và target_KL bằng thí nghiệm có đối chứng, theo dõi critic riêng từng scenario.
- **Thiết kế run Seed100:** cố định cấu hình V2 và budget, cân bằng lấy mẫu scenario, validation trên seed tách train; chọn best checkpoint theo metric giao thông đã sửa, giữ nguyên artifact V1 để đối chiếu.

Seed100 là lượt V2 dự kiến; báo cáo này không xác nhận đã triển khai các cải tiến hoặc đã huấn luyện V2.
