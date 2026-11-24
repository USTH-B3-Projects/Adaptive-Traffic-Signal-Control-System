# Parameter Audit — Adaptive Traffic Signal Control System

Ngày kiểm toán: **15/11/2026 (Asia/Bangkok)**. Commit được đọc: **d84f3279b808d6292dfd0d37ef9e89f53364170c**.

**Phạm vi và phương pháp:** chỉ đọc mã nguồn, YAML/XML, nguồn thư viện đã cài, metadata JSON trong ZIP model và CSV có sẵn. Không import/chạy entry point train, evaluation, runner baseline hoặc bộ sinh SUMO; không khởi tạo môi trường, model hay simulator. File duy nhất được tạo là báo cáo này. Các phép tính trên CSV lịch sử là phân tích dữ liệu có sẵn, không phải chạy evaluation mới.

Đã dò cả `DRL/` và `TraCI/`: hiện có **DRL/**, không tồn tại **TraCI/**. Log cũ có nhắc `TraCI.train_multiscenario` là dấu vết cấu trúc trước đây. Đã đọc trực tiếp tất cả file được yêu cầu trong cấu trúc hiện tại, thêm `core/scenario_loader.py`, `core/simulation.py`, hai pipeline ở root, bốn SUMO scenario, chương trình đèn trong additional-file và chương trình nhúng trong network.

**Phân biệt nguồn giá trị:**

- **Explicit:** khai báo trong code/config của dự án.
- **Default SB3:** không truyền ở call `PPO(...)`, xác minh bằng mã nguồn **Stable-Baselines3 2.9.2** trong `C:/Users/Admin/miniconda3/envs/atsc/Lib/site-packages/stable_baselines3/`. Các liên kết mang nhãn `SB3/...` trỏ đến thư mục này.
- **Historical:** đọc artifact đã tồn tại; không coi là cấu hình bắt buộc cho lần chạy mới.
- **Derived / Nhận định:** suy ra tĩnh từ code hoặc tính trên CSV; rủi ro hội tụ là đánh giá kỹ thuật, chưa phải bằng chứng nhân quả qua thí nghiệm.

**Kết luận chính:** thời lượng đèn hiện không bị random hóa; PPO và Rule-Based dùng cùng lớp ràng buộc 30–75 s, vàng 3 s và toàn đỏ thực tế 3 s. Các rủi ro lớn hơn nằm ở observation tổng hợp không phân biệt hướng, input/reward chưa chuẩn hóa, phân bố reward khác nhiều giữa kịch bản, seed đánh giá không khớp baseline và các lỗi đo arrivals. Không có cơ sở kết luận chỉ một siêu tham số PPO gây mất hội tụ.

## 1. Bảng 1 — Bảng kiểm soát tham số tổng hợp

| Nhóm | Tên tham số | Giá trị hiện tại | File & Dòng code | Đánh giá kỹ thuật / Luật VN | Rủi ro gây khó hội tụ |
|---|---|---|---|---|---|
| Thời gian | `simulation_step` | **0.1 s** từ YAML; default nội bộ của loader là 1 s nhưng bị YAML ghi đè | [DRL/configs/traci.yaml:1](<D:/grp prj new lap/Adaptive-Traffic-Signal-Control-System/DRL/configs/traci.yaml:1>); [DRL/core/scenario_loader.py:10–12](<D:/grp prj new lap/Adaptive-Traffic-Signal-Control-System/DRL/core/scenario_loader.py:10>) | Thời gian mô phỏng, không phải thời gian chạy trên máy. RB/FT còn hard-code 0.1 s | Thấp hiện tại; đổi YAML một mình có thể gây lệch baseline |
| Thời gian | `decision_interval` | **5 s** | [DRL/configs/traci.yaml:2](<D:/grp prj new lap/Adaptive-Traffic-Signal-Control-System/DRL/configs/traci.yaml:2>); [DRL/core/environment.py:74–84](<D:/grp prj new lap/Adaptive-Traffic-Signal-Control-System/DRL/core/environment.py:74>) | Một hành động cho mỗi khoảng tối đa 5 s; kiểm tra đèn vẫn chạy từng bước SUMO | Trung bình: coarse decision so với pha chuyển tiếp 3 s |
| Thời gian | Simulation steps / quyết định | **5 / 0.1 = 50** bình thường | [DRL/core/environment.py:75–93](<D:/grp prj new lap/Adaptive-Traffic-Signal-Control-System/DRL/core/environment.py:75>) | Có thể ít hơn khi hết episode/nhu cầu; không phải 5 bước | Nhầm đơn vị dẫn đến sai tuning và sai throughput |
| Thời gian | `min_green` | **30 s** | [DRL/configs/traci.yaml:3](<D:/grp prj new lap/Adaptive-Traffic-Signal-Control-System/DRL/configs/traci.yaml:3>); [DRL/core/signal_controller.py:141–142](<D:/grp prj new lap/Adaptive-Traffic-Signal-Control-System/DRL/core/signal_controller.py:141>) | Giới hạn cho một **green stage liên tục**, gồm startup và main; lớn hơn ngưỡng xanh 15 s tại A.2 | Hạn chế số quyết định có tác dụng, không tự nó là lỗi |
| Thời gian | `max_green` | **75 s** | [DRL/configs/traci.yaml:4](<D:/grp prj new lap/Adaptive-Traffic-Signal-Control-System/DRL/configs/traci.yaml:4>); [DRL/core/signal_controller.py:99–123](<D:/grp prj new lap/Adaptive-Traffic-Signal-Control-System/DRL/core/signal_controller.py:99>) | Cưỡng bức chuyển ở deadline, không phải chờ policy yêu cầu hoặc chờ lần quyết định kế tiếp | Thấp; credit assignment cần phân biệt switch tự động |
| Thời gian | `yellow_time` | **3 s**; XML cũng 3 s | [DRL/configs/traci.yaml:5](<D:/grp prj new lap/Adaptive-Traffic-Signal-Control-System/DRL/configs/traci.yaml:5>); [DRL/core/signal_controller.py:42](<D:/grp prj new lap/Adaptive-Traffic-Signal-Control-System/DRL/core/signal_controller.py:42>); [SUMO/Map_Nga_tu/config/traffic_light.add.xml:6](<D:/grp prj new lap/Adaptive-Traffic-Signal-Control-System/SUMO/Map_Nga_tu/config/traffic_light.add.xml:6>) | Dùng max(thời lượng XML, ngưỡng cấu hình); không được suy ra đủ clearance thực tế chỉ từ số này | Không phải lỗi PPO; cần thiết kế theo hình học/tốc độ |
| Thời gian | `all_red_time` | **Cấu hình 0 s, thực thi 3 s** ở mỗi chuyển trục | [DRL/configs/traci.yaml:6](<D:/grp prj new lap/Adaptive-Traffic-Signal-Control-System/DRL/configs/traci.yaml:6>); [DRL/core/signal_controller.py:42–46](<D:/grp prj new lap/Adaptive-Traffic-Signal-Control-System/DRL/core/signal_controller.py:42>); [SUMO/Map_Nga_tu/config/traffic_light.add.xml:7–11](<D:/grp prj new lap/Adaptive-Traffic-Signal-Control-System/SUMO/Map_Nga_tu/config/traffic_light.add.xml:7>) | 0 là ngưỡng kéo dài, không xóa pha toàn đỏ đã có | Cao nếu đọc nhầm cấu hình và thiết kế sai chu kỳ |
| Thời gian | `max_episode_seconds` | **null** cho PPO; Rule-Based override **3600 s** | [DRL/configs/traci.yaml:8](<D:/grp prj new lap/Adaptive-Traffic-Signal-Control-System/DRL/configs/traci.yaml:8>); [RuleBased/run_rule_based.py:62–64](<D:/grp prj new lap/Adaptive-Traffic-Signal-Control-System/RuleBased/run_rule_based.py:62>) | null không đồng nghĩa episode vô hạn vì còn SUMO scenario end | Thấp với input hiện tại; nguy cơ drift khi đổi end |
| Thời gian | Episode thực tế | Bốn scenario begin=0, end=**3600 s** → tối đa **36,000 SUMO steps**, **720 quyết định** | [SUMO/Map_Nga_tu/Map_Low/simulation.sumocfg:8–12](<D:/grp prj new lap/Adaptive-Traffic-Signal-Control-System/SUMO/Map_Nga_tu/Map_Low/simulation.sumocfg:8>); [DRL/core/environment.py:37–45](<D:/grp prj new lap/Adaptive-Traffic-Signal-Control-System/DRL/core/environment.py:37>) | Kết thúc sớm nếu không còn xe/nhu cầu. Main config ngoài mapping có end=3720 s, không phải input train | Medium/High có thể còn backlog ở cutoff; không có giai đoạn xả xe trong 4 scenario |
| Thời gian | `green_elapsed` | `max(0, now - start)`; **giây mô phỏng**, 0 khi chuyển tiếp | [DRL/core/signal_controller.py:99–108](<D:/grp prj new lap/Adaptive-Traffic-Signal-Control-System/DRL/core/signal_controller.py:99>); [DRL/core/signal_controller.py:148–154](<D:/grp prj new lap/Adaptive-Traffic-Signal-Control-System/DRL/core/signal_controller.py:148>) | Cộng liên tục qua startup/main cùng mask G/g; không đếm số step, không dùng đồng hồ wall-clock | Thấp; phase ID riêng lẻ không đồng nghĩa green stage riêng |
| Điều khiển | Random thời lượng đèn | **Không có** import/call random hay jitter trong controller | [DRL/core/signal_controller.py:1–154](<D:/grp prj new lap/Adaptive-Traffic-Signal-Control-System/DRL/core/signal_controller.py:1>) | Chuyển do action hợp lệ, deadline hoặc phase progression; randomness của traffic/PPO nằm ngoài controller | Không có rủi ro random duration trực tiếp |
| Điều khiển | Startup / main | Startup **3 s**; main XML **48 s**. Fixed-Time xanh tổng **51 s**; adaptive thay main theo min/max | [SUMO/Map_Nga_tu/config/traffic_light.add.xml:4–9](<D:/grp prj new lap/Adaptive-Traffic-Signal-Control-System/SUMO/Map_Nga_tu/config/traffic_light.add.xml:4>); [DRL/core/signal_controller.py:47–65](<D:/grp prj new lap/Adaptive-Traffic-Signal-Control-System/DRL/core/signal_controller.py:47>); [DRL/core/signal_controller.py:134–144](<D:/grp prj new lap/Adaptive-Traffic-Signal-Control-System/DRL/core/signal_controller.py:134>) | Hai phase cùng G/g mask là một stage dù ký tự `s` khác nhau | Không được gán nhầm startup 3 s là toàn bộ thời lượng xanh |
| Điều khiển | TLS / pha | 1 TLS `J`; **8 phase index 0…7**, **2 green stages** NS/EW | [SUMO/Map_Nga_tu/config/traffic_light.add.xml:3–12](<D:/grp prj new lap/Adaptive-Traffic-Signal-Control-System/SUMO/Map_Nga_tu/config/traffic_light.add.xml:3>); [DRL/gym_env.py:21](<D:/grp prj new lap/Adaptive-Traffic-Signal-Control-System/DRL/gym_env.py:21>); [DRL/gym_env.py:59–64](<D:/grp prj new lap/Adaptive-Traffic-Signal-Control-System/DRL/gym_env.py:59>) | Môi trường DRL từ chối số TLS khác 1; mapping Rule-Based hard-code J và phase IDs | Không sẵn cho Ô Chợ Dừa hoặc đổi chương trình pha |
| Điều khiển | Đỏ ≥15 s cho mọi movement | **Không có invariant/min_red riêng**; xem phân tích 1.2 | [DRL/core/signal_controller.py:126–154](<D:/grp prj new lap/Adaptive-Traffic-Signal-Control-System/DRL/core/signal_controller.py:126>); [SUMO/Map_Nga_tu/config/traffic_light.add.xml:4–11](<D:/grp prj new lap/Adaptive-Traffic-Signal-Control-System/SUMO/Map_Nga_tu/config/traffic_light.add.xml:4>) | A.2 xác nhận ngưỡng **xanh**, không phải ngưỡng đỏ phổ quát | Phải tách tính đúng chương trình đèn và kết luận pháp lý |
| Runtime | `gui` | **false**; FT/RB cũng ép false | [DRL/configs/traci.yaml:7](<D:/grp prj new lap/Adaptive-Traffic-Signal-Control-System/DRL/configs/traci.yaml:7>); [FixedTime/run_fixed_time.py:35](<D:/grp prj new lap/Adaptive-Traffic-Signal-Control-System/FixedTime/run_fixed_time.py:35>); [RuleBased/run_rule_based.py:63](<D:/grp prj new lap/Adaptive-Traffic-Signal-Control-System/RuleBased/run_rule_based.py:63>) | Headless ở pipeline hiện tại; không thay đổi thời gian mô phỏng thành wall-clock | Chủ yếu chi phí chạy, không phải tham số hội tụ |
| Runtime | `sumo_binary` | **null** → tìm `sumo` qua PATH, sau đó SUMO_HOME/bin | [DRL/configs/traci.yaml:9](<D:/grp prj new lap/Adaptive-Traffic-Signal-Control-System/DRL/configs/traci.yaml:9>); [DRL/core/simulation.py:35](<D:/grp prj new lap/Adaptive-Traffic-Signal-Control-System/DRL/core/simulation.py:35>) | Chưa pin đường dẫn/version SUMO tại config | Đổi binary có thể đổi động lực học/tái lập |
| Runtime | `seed` cấu hình và precedence | YAML **null**, XML **42**; ưu tiên reset argument → YAML → XML | [DRL/configs/traci.yaml:10](<D:/grp prj new lap/Adaptive-Traffic-Signal-Control-System/DRL/configs/traci.yaml:10>); [DRL/core/environment.py:29](<D:/grp prj new lap/Adaptive-Traffic-Signal-Control-System/DRL/core/environment.py:29>); [SUMO/Map_Nga_tu/Map_Low/simulation.sumocfg:19](<D:/grp prj new lap/Adaptive-Traffic-Signal-Control-System/SUMO/Map_Nga_tu/Map_Low/simulation.sumocfg:19>) | CLI/reset thường ghi đè XML; wrapper PPO còn remap seed | Cao cho fairness nếu chỉ nhìn seed trong XML |
| SUMO | Cảnh báo va chạm | `collision.check-junctions=true`, `collision.action=warn`, lateral resolution=**0.325 m** | [SUMO/Map_Nga_tu/Map_Low/simulation.sumocfg:13–16](<D:/grp prj new lap/Adaptive-Traffic-Signal-Control-System/SUMO/Map_Nga_tu/Map_Low/simulation.sumocfg:13>) | Va chạm không tự dừng run hoặc trở thành constraint/reward của PPO | Policy có thể tối ưu chỉ số ùn tắc mà không bị phạt va chạm |
| SUMO | Network | 4 hướng, 2 làn vào/hướng, 250 m/làn, giới hạn tốc độ làn vào 13.9 m/s | [SUMO/Map_Nga_tu/network/intersection.net.xml:90–120](<D:/grp prj new lap/Adaptive-Traffic-Signal-Control-System/SUMO/Map_Nga_tu/network/intersection.net.xml:90>) | Cùng network cho 4 scenario | Hữu hạn storage, nguy cơ hàng chờ lan ra ngoài vùng quan sát |
| SUMO | Nhu cầu | Low **1200**, Medium **3000**, High **5400**, Imbalance **4200 xe/h** kỳ vọng; Imbalance N/S=1800, E/W=300 | [SUMO/Map_Nga_tu/generate_scenarios.py:12–19](<D:/grp prj new lap/Adaptive-Traffic-Signal-Control-System/SUMO/Map_Nga_tu/generate_scenarios.py:12>); XML traffic của từng scenario, flow dòng 24–59 | Đã đối chiếu trực tiếp 36 flow/scenario; 80% motor,17% car,3% bus; rẽ 70/15/15 | Reward có scale rất khác giữa kịch bản; không cân bằng theo chỉ số |
| SUMO | Vehicle dynamics | Krauss/SL2015; motorcycle `tau=0.6`, car=1.2, bus=1.5 s; `sigma=0.5`; departSpeed=0 | [SUMO/Map_Nga_tu/Map_Low/traffic.rou.xml:3–11](<D:/grp prj new lap/Adaptive-Traffic-Signal-Control-System/SUMO/Map_Nga_tu/Map_Low/traffic.rou.xml:3>); [SUMO/Map_Nga_tu/Map_Low/traffic.rou.xml:24](<D:/grp prj new lap/Adaptive-Traffic-Signal-Control-System/SUMO/Map_Nga_tu/Map_Low/traffic.rou.xml:24>) | 0.1 s < các tau này; có randomness trong vehicle behavior, không phải đèn | Nhiễu traffic cần common evaluation seeds |
| MDP | Action space | **Discrete(2)**; `0=KEEP`, `1=SWITCH` | [DRL/gym_env.py:22](<D:/grp prj new lap/Adaptive-Traffic-Signal-Control-System/DRL/gym_env.py:22>); [DRL/gym_env.py:70–77](<D:/grp prj new lap/Adaptive-Traffic-Signal-Control-System/DRL/gym_env.py:70>) | Không phải Box, không chọn thời lượng xanh trực tiếp | Đơn giản; thiếu action masking nhưng không phải hành động không an toàn |
| MDP | SWITCH khi chưa min | Thực thi **KEEP**, reason=`min_green`; startup=`startup_phase`; trong transition=`NOOP` | [DRL/core/signal_controller.py:126–146](<D:/grp prj new lap/Adaptive-Traffic-Signal-Control-System/DRL/core/signal_controller.py:126>) | Request bị bỏ qua, không xếp hàng; KEEP cũng bị cưỡng bức chuyển ở max | Nhiều action khác nhau có cùng tác động; gradient có thể nhiễu |
| MDP | Observation shape/dtype | **(6,)**, **float32**; tổng quát ghi 6×TLS nhưng expected TLS=1 | [DRL/gym_env.py:20–28](<D:/grp prj new lap/Adaptive-Traffic-Signal-Control-System/DRL/gym_env.py:20>); [DRL/gym_env.py:65–68](<D:/grp prj new lap/Adaptive-Traffic-Signal-Control-System/DRL/gym_env.py:65>) | 6 scalars tổng TLS, không phải dữ liệu từng hướng/làn | **Cao:** mất phân bố nhu cầu NS/EW |
| MDP | Observation low/high | **low=0.0, high=+inf** cho cả 6 chiều | [DRL/gym_env.py:23–28](<D:/grp prj new lap/Adaptive-Traffic-Signal-Control-System/DRL/gym_env.py:23>) | Giới hạn khai báo, không phải phép chuẩn hóa. Chi tiết từng chiều ở 1.3 | Dải giá trị chênh lớn |
| MDP | Observation normalization | **Không**; không VecNormalize/RescaleObservation trong đường train | [DRL/gym_env.py:30–44](<D:/grp prj new lap/Adaptive-Traffic-Signal-Control-System/DRL/gym_env.py:30>); [DRL/train_multiscenario.py:69–82](<D:/grp prj new lap/Adaptive-Traffic-Signal-Control-System/DRL/train_multiscenario.py:69>) | SB3 Box-vector chỉ cast float, không scale /255 như ảnh | **Cao:** Tanh có thể bão hòa với waiting/time lớn |
| MDP | Phase encoding / thông tin hướng | phase ID raw 0…7; **không one-hot**, không queue NS/EW, không scenario ID, không thời gian còn lại | [DRL/gym_env.py:34–42](<D:/grp prj new lap/Adaptive-Traffic-Signal-Control-System/DRL/gym_env.py:34>) | RB nhìn được queue từng trục; PPO không có cùng thông tin | **Cao:** observation aliasing / partial observability |
| MDP | Missing continuous metric | `None` được đổi thành **0.0** trong observation/reward | [DRL/gym_env.py:37–38](<D:/grp prj new lap/Adaptive-Traffic-Signal-Control-System/DRL/gym_env.py:37>); [DRL/gym_env.py:51](<D:/grp prj new lap/Adaptive-Traffic-Signal-Control-System/DRL/gym_env.py:51>); [DRL/core/state_extractor.py:7–9](<D:/grp prj new lap/Adaptive-Traffic-Signal-Control-System/DRL/core/state_extractor.py:7>) | Không có cờ missing; missing waiting có thể được coi là không chờ | Có thể che dữ liệu không hợp lệ |
| Reward | Công thức | `r = -(Q + 0.1 * W)` | [DRL/gym_env.py:46–52](<D:/grp prj new lap/Adaptive-Traffic-Signal-Control-System/DRL/gym_env.py:46>) | Q=halting vehicles; W=tổng current waiting giây trên làn vào | Chỉ tối ưu queue/wait; thiếu fairness theo hướng và safety |
| Reward | Trọng số | Queue **1.0**, waiting **0.1**; throughput/speed/collision/switch penalty **không có** | [DRL/gym_env.py:46–52](<D:/grp prj new lap/Adaptive-Traffic-Signal-Control-System/DRL/gym_env.py:46>) | Một đơn vị reward tương đương 1 xe dừng hoặc 10 s tổng waiting | W thường chi phối ở tải cao; xem 1.4 |
| Reward | Sampling / thời lượng | Một snapshot **cuối** decision interval; không tích phân 50 bước, không nhân/chia duration | [DRL/core/environment.py:94](<D:/grp prj new lap/Adaptive-Traffic-Signal-Control-System/DRL/core/environment.py:94>); [DRL/gym_env.py:92](<D:/grp prj new lap/Adaptive-Traffic-Signal-Control-System/DRL/gym_env.py:92>) | Không phải tổng waiting toàn hành trình hay time-integrated reward | Chất lượng signal phụ thuộc thời điểm lấy mẫu; đổi interval làm đổi objective |
| Reward | Scaling / clipping | **Không scale/clipping riêng reward**; giá trị không dương, không có ngưỡng dưới cấu hình | [DRL/gym_env.py:46–52](<D:/grp prj new lap/Adaptive-Traffic-Signal-Control-System/DRL/gym_env.py:46>); [DRL/train_multiscenario.py:69–82](<D:/grp prj new lap/Adaptive-Traffic-Signal-Control-System/DRL/train_multiscenario.py:69>) | Hệ số 0.1 là trọng số, không phải reward normalization | Value target lớn, scale khác giữa scenario |
| PPO | Tham số thực sự truyền | `"MlpPolicy", env, seed=args.seed, verbose=1, tensorboard_log=str(args.log_dir), device=args.device` | [DRL/train_multiscenario.py:75–82](<D:/grp prj new lap/Adaptive-Traffic-Signal-Control-System/DRL/train_multiscenario.py:75>) | Các siêu tham số khác đều ngầm dùng default thư viện | Không pin dependency làm khó tái lập |
| PPO | `total_timesteps` | CLI mặc định **800,000**, truyền vào `learn`; pipeline710 mặc định **600,000** | [DRL/train_multiscenario.py:54–55](<D:/grp prj new lap/Adaptive-Traffic-Signal-Control-System/DRL/train_multiscenario.py:54>); [DRL/train_multiscenario.py:84](<D:/grp prj new lap/Adaptive-Traffic-Signal-Control-System/DRL/train_multiscenario.py:84>); [run_pipeline_seed710.py:92–93](<D:/grp prj new lap/Adaptive-Traffic-Signal-Control-System/run_pipeline_seed710.py:92>) | Bước quyết định RL, không phải bước 0.1 s của SUMO | So sánh 2 seed cũng đổi budget nên bị nhiễu |
| PPO | `n_steps` | **2048 / env / rollout**, Default SB3 | [SB3/ppo/ppo.py:85](<C:/Users/Admin/miniconda3/envs/atsc/Lib/site-packages/stable_baselines3/ppo/ppo.py:85>) | 1 env → 2048 mẫu/update, tương đương ~2.84 episode 720 bước | Mỗi rollout chưa bảo đảm có đủ 4 scenario |
| PPO | `batch_size` | **64**, Default SB3 | [SB3/ppo/ppo.py:86](<C:/Users/Admin/miniconda3/envs/atsc/Lib/site-packages/stable_baselines3/ppo/ppo.py:86>) | 2048/64=32 minibatch, chia hết | Không có lỗi chia minibatch |
| PPO | `n_epochs` | **10**, Default SB3 | [SB3/ppo/ppo.py:87](<C:/Users/Admin/miniconda3/envs/atsc/Lib/site-packages/stable_baselines3/ppo/ppo.py:87>) | 320 minibatch optimizer steps/rollout nếu không early stop | Không đủ cơ sở gọi cao/thấp gây lỗi khi chưa có ablation |
| PPO | `learning_rate` | **3e-4**, giá trị cố định, không lịch giảm | [SB3/ppo/ppo.py:84](<C:/Users/Admin/miniconda3/envs/atsc/Lib/site-packages/stable_baselines3/ppo/ppo.py:84>); [SB3/common/base_class.py:276](<C:/Users/Admin/miniconda3/envs/atsc/Lib/site-packages/stable_baselines3/common/base_class.py:276>) | SB3 bọc constant FloatSchedule; không có schedule trong dự án | Trung bình: chưa tune cho input/reward raw |
| PPO | `gamma` | **0.99**, Default SB3 | [SB3/ppo/ppo.py:88](<C:/Users/Admin/miniconda3/envs/atsc/Lib/site-packages/stable_baselines3/ppo/ppo.py:88>) | Horizon xấp xỉ 100 quyết định =500 s ở interval 5 s | Có thể thiên về lợi ích ngắn hơn episode 3600 s |
| PPO | `gae_lambda` | **0.95**, Default SB3 | [SB3/ppo/ppo.py:89](<C:/Users/Admin/miniconda3/envs/atsc/Lib/site-packages/stable_baselines3/ppo/ppo.py:89>) | gamma×lambda=0.9405; thang suy giảm GAE ~16.8 quyết định=84 s | Tín hiệu dài hạn cần critic học tốt |
| PPO | `clip_range` | **0.2**, constant schedule | [SB3/ppo/ppo.py:90](<C:/Users/Admin/miniconda3/envs/atsc/Lib/site-packages/stable_baselines3/ppo/ppo.py:90>); [SB3/ppo/ppo.py:177](<C:/Users/Admin/miniconda3/envs/atsc/Lib/site-packages/stable_baselines3/ppo/ppo.py:177>) | Clip policy ratio, **không clip reward/observation** | Không bảo đảm giới hạn KL tuyệt đối |
| PPO | `clip_range_vf` | **None** | [SB3/ppo/ppo.py:91](<C:/Users/Admin/miniconda3/envs/atsc/Lib/site-packages/stable_baselines3/ppo/ppo.py:91>) | Không clip thay đổi value prediction theo tham số này | Có thể nhạy khi reward scale lớn |
| PPO | `normalize_advantage` | **True** | [SB3/ppo/ppo.py:92](<C:/Users/Admin/miniconda3/envs/atsc/Lib/site-packages/stable_baselines3/ppo/ppo.py:92>); [SB3/ppo/ppo.py:216–219](<C:/Users/Admin/miniconda3/envs/atsc/Lib/site-packages/stable_baselines3/ppo/ppo.py:216>) | Chuẩn hóa advantage trong minibatch; không chuẩn hóa input hay value target | Giảm một phần scale policy gradient, không giải quyết toàn bộ vấn đề |
| PPO | `ent_coef` | **0.0** | [SB3/ppo/ppo.py:93](<C:/Users/Admin/miniconda3/envs/atsc/Lib/site-packages/stable_baselines3/ppo/ppo.py:93>) | Không có entropy bonus; vẫn sampling stochastic policy khi train | Nguy cơ giảm khám phá sớm; cần kiểm entropy/KL để xác nhận |
| PPO | `vf_coef` | **0.5** | [SB3/ppo/ppo.py:94](<C:/Users/Admin/miniconda3/envs/atsc/Lib/site-packages/stable_baselines3/ppo/ppo.py:94>) | Hệ số value loss | Reward lớn có thể làm value loss lấn át |
| PPO | `max_grad_norm` | **0.5** | [SB3/ppo/ppo.py:95](<C:/Users/Admin/miniconda3/envs/atsc/Lib/site-packages/stable_baselines3/ppo/ppo.py:95>) | Gradient clipping, **không phải reward clipping** | Không loại bỏ tanh saturation hoặc mất thông tin |
| PPO | `target_kl` | **None** | [SB3/ppo/ppo.py:100](<C:/Users/Admin/miniconda3/envs/atsc/Lib/site-packages/stable_baselines3/ppo/ppo.py:100>) | Không có early stop theo KL threshold | Rủi ro update lớn chưa được kiểm soát bằng KL cap |
| PPO | `use_sde / sde_sample_freq` | **False / -1** | [SB3/ppo/ppo.py:96–97](<C:/Users/Admin/miniconda3/envs/atsc/Lib/site-packages/stable_baselines3/ppo/ppo.py:96>) | gSDE không dùng; Discrete action dùng categorical distribution | Không nên bật gSDE như cách sửa cho Discrete |
| PPO | Rollout buffer | `rollout_buffer_class=None` → mặc định RolloutBuffer; kwargs=None | [SB3/ppo/ppo.py:98–99](<C:/Users/Admin/miniconda3/envs/atsc/Lib/site-packages/stable_baselines3/ppo/ppo.py:98>); [SB3/common/on_policy_algorithm.py:122–125](<C:/Users/Admin/miniconda3/envs/atsc/Lib/site-packages/stable_baselines3/common/on_policy_algorithm.py:122>) | Không custom replay; đây là on-policy PPO | Không có replay để cân bằng lại scenario cũ |
| PPO | `n_envs` / wrappers | **1**; Monitor(MultiScenarioEnv) rồi SB3 DummyVecEnv | [DRL/train_multiscenario.py:69](<D:/grp prj new lap/Adaptive-Traffic-Signal-Control-System/DRL/train_multiscenario.py:69>); [SB3/common/base_class.py:224](<C:/Users/Admin/miniconda3/envs/atsc/Lib/site-packages/stable_baselines3/common/base_class.py:224>); metadata ZIP | Không multi-process/vector song song; Monitor chỉ ghi thống kê | Chạy lâu; rollout có ít episode để trộn |
| PPO | `stats_window_size` | **100 episodes**, Default SB3 | [SB3/ppo/ppo.py:101](<C:/Users/Admin/miniconda3/envs/atsc/Lib/site-packages/stable_baselines3/ppo/ppo.py:101>) | Reward mean gộp nhiều scenario và cửa sổ di chuyển | Không thể dùng một đường reward gộp để kết luận hội tụ từng tải |
| PPO | `device` | Train CLI mặc định **auto**; pipeline710 ép **cuda** | [DRL/train_multiscenario.py:58](<D:/grp prj new lap/Adaptive-Traffic-Signal-Control-System/DRL/train_multiscenario.py:58>); [DRL/train_multiscenario.py:81](<D:/grp prj new lap/Adaptive-Traffic-Signal-Control-System/DRL/train_multiscenario.py:81>); [run_pipeline_seed710.py:128–129](<D:/grp prj new lap/Adaptive-Traffic-Signal-Control-System/run_pipeline_seed710.py:128>) | auto chọn theo khả dụng; không xác minh runtime GPU trong audit | Chủ yếu ảnh hưởng runtime/reproducibility, không phải bằng chứng lỗi học |
| PPO | `seed` | Train CLI **107**; pipeline710 **710**; đánh giá CLI mặc định **42** | [DRL/train_multiscenario.py:54](<D:/grp prj new lap/Adaptive-Traffic-Signal-Control-System/DRL/train_multiscenario.py:54>); [run_pipeline_seed710.py:92](<D:/grp prj new lap/Adaptive-Traffic-Signal-Control-System/run_pipeline_seed710.py:92>); [DRL/evaluate.py:103](<D:/grp prj new lap/Adaptive-Traffic-Signal-Control-System/DRL/evaluate.py:103>) | Seed policy/env khác seed SUMO thực sau wrapper | **Cao cho fairness**, xem 2 |
| PPO | Checkpoint / validation | Lưu mỗi **50,000 callback steps**; không EvalCallback/best-model selection | [DRL/train_multiscenario.py:70–85](<D:/grp prj new lap/Adaptive-Traffic-Signal-Control-System/DRL/train_multiscenario.py:70>) | Lưu checkpoint không chứng minh checkpoint đó tốt nhất | Không theo dõi generalization/collapse từng scenario khi train |
| Network | `policy_kwargs` | Không truyền → **None → {}**; artifact hai model đều {} | [DRL/train_multiscenario.py:75–82](<D:/grp prj new lap/Adaptive-Traffic-Signal-Control-System/DRL/train_multiscenario.py:75>); [SB3/common/base_class.py:133](<C:/Users/Admin/miniconda3/envs/atsc/Lib/site-packages/stable_baselines3/common/base_class.py:133>) | Mạng hoàn toàn dùng default ActorCriticPolicy | Khó biết cấu hình nếu chỉ đọc call trong dự án |
| Network | `net_arch` | **dict(pi=[64,64], vf=[64,64])**, Default SB3 | [SB3/common/policies.py:495–500](<C:/Users/Admin/miniconda3/envs/atsc/Lib/site-packages/stable_baselines3/common/policies.py:495>) | Mỗi nhánh MLP 6→64→64; actor head 2 logits, critic head 1 value | Không có recurrent memory để bù observation thiếu hướng |
| Network | `activation_fn` | **torch.nn.Tanh** | [SB3/common/policies.py:453–455](<C:/Users/Admin/miniconda3/envs/atsc/Lib/site-packages/stable_baselines3/common/policies.py:453>) | Input vector raw đi vào Tanh | **Cao:** waiting hàng trăm/hàng nghìn có thể gây bão hòa |
| Network | Feature extraction / normalization | FlattenExtractor, share_features_extractor=True, normalize_images=True | [SB3/common/policies.py:461–464](<C:/Users/Admin/miniconda3/envs/atsc/Lib/site-packages/stable_baselines3/common/policies.py:461>); [SB3/common/preprocessing.py:117–120](<C:/Users/Admin/miniconda3/envs/atsc/Lib/site-packages/stable_baselines3/common/preprocessing.py:117>) | normalize_images không áp dụng cho Box vector (6,) này | Không được nhầm default này là observation normalization |
| Network | Init / optimizer | `ortho_init=True`; **Adam**, mặc định policy thêm `eps=1e-5` | [SB3/common/policies.py:455](<C:/Users/Admin/miniconda3/envs/atsc/Lib/site-packages/stable_baselines3/common/policies.py:455>); [SB3/common/policies.py:465–472](<C:/Users/Admin/miniconda3/envs/atsc/Lib/site-packages/stable_baselines3/common/policies.py:465>) | Không custom optimizer trong code dự án | Không thấy lỗi cấu hình trực tiếp |
| Scenario | Chọn scenario | Random uniform integer trên 4 lựa chọn, **P=0.25/scenario/reset** | [DRL/train_multiscenario.py:15](<D:/grp prj new lap/Adaptive-Traffic-Signal-Control-System/DRL/train_multiscenario.py:15>); [DRL/train_multiscenario.py:33–39](<D:/grp prj new lap/Adaptive-Traffic-Signal-Control-System/DRL/train_multiscenario.py:33>) | Không round-robin; không quota hay bộ đếm số episode từng scenario | Tỷ lệ chỉ cân bằng theo kỳ vọng, không cân bằng tuyệt đối |
| Scenario | Episode seed | `train_seed + episode_index` rồi wrapper sinh số nguyên làm seed SUMO | [DRL/train_multiscenario.py:37–39](<D:/grp prj new lap/Adaptive-Traffic-Signal-Control-System/DRL/train_multiscenario.py:37>); [DRL/gym_env.py:54–58](<D:/grp prj new lap/Adaptive-Traffic-Signal-Control-System/DRL/gym_env.py:54>) | Tăng seed không đồng nghĩa traffic seed truyền thẳng | Cần lưu seed thực cho tái lập |
| Evaluation | Policy / repetitions | `deterministic=True`; 1 episode/scenario/CLI seed | [DRL/evaluate.py:23–33](<D:/grp prj new lap/Adaptive-Traffic-Signal-Control-System/DRL/evaluate.py:23>); [DRL/evaluate.py:110–114](<D:/grp prj new lap/Adaptive-Traffic-Signal-Control-System/DRL/evaluate.py:110>) | Train stochastic, đánh giá greedy là thiết kế phổ biến; thiếu repeated held-out seeds | Không đủ dữ liệu để kết luận độ bền hoặc hội tụ |
| Reproducibility | Dependencies | `DRL/requirements.txt` chỉ có **PyYAML>=6.0,<7** | [DRL/requirements.txt:1](<D:/grp prj new lap/Adaptive-Traffic-Signal-Control-System/DRL/requirements.txt:1>) | Không khai báo/pin SB3, gymnasium, numpy, torch, matplotlib, tensorboard | **Cao:** lần cài mới có thể đổi default hoặc không chạy được |

### 1.1. Thứ tự ưu tiên cấu hình và cấu hình thực sự có hiệu lực

`ScenarioLoader.DEFAULTS → traci.yaml → Environment(settings=...)`. Khi khởi động SUMO, `Simulation.start` truyền `--step-length` theo settings và `--seed` theo seed đã chọn, nên các tham số này có thể ghi đè `.sumocfg`. Nguồn: [DRL/core/scenario_loader.py:29–35](<D:/grp prj new lap/Adaptive-Traffic-Signal-Control-System/DRL/core/scenario_loader.py:29>), [DRL/core/environment.py:13–17](<D:/grp prj new lap/Adaptive-Traffic-Signal-Control-System/DRL/core/environment.py:13>), [DRL/core/environment.py:28–31](<D:/grp prj new lap/Adaptive-Traffic-Signal-Control-System/DRL/core/environment.py:28>), [DRL/core/simulation.py:84–91](<D:/grp prj new lap/Adaptive-Traffic-Signal-Control-System/DRL/core/simulation.py:84>).

Cả bốn entry trong `scenarios.yaml` đều trỏ đến `SUMO/Map_Nga_tu/Map_*/simulation.sumocfg`. Chúng dùng cùng network và cùng `config/traffic_light.add.xml`, begin=0, end=3600, step-length=0.1, seed XML=42. `config/intersection.sumocfg` có end=3720 nhưng **không nằm trong mapping huấn luyện**.

Network còn nhúng program `0` với các pha 42/3/42/3 s, nhưng additional-file được cấu hình nạp program `test` có 8 pha và cycle 114 s. Không lấy các giá trị 42 s trong `.net.xml` để mô tả Fixed-Time của pipeline hiện tại. Nguồn: [SUMO/Map_Nga_tu/network/intersection.net.xml:123–128](<D:/grp prj new lap/Adaptive-Traffic-Signal-Control-System/SUMO/Map_Nga_tu/network/intersection.net.xml:123>), [SUMO/Map_Nga_tu/Map_Low/simulation.sumocfg:4–6](<D:/grp prj new lap/Adaptive-Traffic-Signal-Control-System/SUMO/Map_Nga_tu/Map_Low/simulation.sumocfg:4>), [SUMO/Map_Nga_tu/config/traffic_light.add.xml:3–12](<D:/grp prj new lap/Adaptive-Traffic-Signal-Control-System/SUMO/Map_Nga_tu/config/traffic_light.add.xml:3>). Đây là kết luận từ cấu hình nạp file, chưa xác minh lại bằng runtime trong lần audit này.

### 1.2. Thời lượng, startup, đỏ của hướng xung đột và luật Việt Nam

**Đối chiếu pháp lý:** QCVN 41:2024/BGTVT, Phụ lục A.2 ghi: “Thời gian đèn xanh tối thiểu cho một hướng giao thông ít nhất là 15 giây”. Ngưỡng được kiểm chứng là **xanh**, không phải quy định phổ quát “đỏ tối thiểu 15 s”. Vì vậy không dùng giả định đỏ 15 s để kết luận vi phạm luật. [Bản Công báo chính thức, trang in 87, trang PDF 86](https://congbaocdn.chinhphu.vn/CongBaoCP/VanBan/2024/11/43387/53148-1-20241359-136051-2024-tt-bgtvt.pdf#page=86).

Phân tích tĩnh chương trình hiện tại, không phải phép chứng nhận tuân thủ toàn bộ quy chuẩn:

- `min_green=30` đáp ứng ngưỡng xanh vừa nêu cho **stage xanh hoàn chỉnh**. Hai pha startup 3 s và main có cùng mask G/g, vì vậy đây là một khoảng xanh liên tục; không phải hai xanh độc lập, trong đó một xanh chỉ dài 3 s.
- `green_elapsed` dùng hiệu hai mốc `connection.simulation.getTime()`. 30 s tương đương 300 bước SUMO 0.1 s. Máy chạy nhanh/chậm không làm thay đổi giá trị này.
- Deadline xanh tối đa được xử lý mỗi bước 0.1 s. `setPhaseDuration(..., 1e9)` chỉ khóa bộ tự chạy của SUMO để controller quản lý, **không phải xanh một tỷ giây**.
- Switch do policy chỉ được xét trên lưới 5 s. Khi xanh mới bắt đầu ngoài lưới, yêu cầu sớm nhất sau min có thể tới muộn thêm dưới 5 s. Ví dụ t=30 chuyển NS→vàng 3→toàn đỏ 3→EW bắt đầu t=36; quyết định t=65 mới đạt 29 s, t=70 đạt 34 s. Không có random can thiệp thời lượng này.
- **Đối với movement đi thẳng/luồng chính**, khoảng `r` hoàn chỉnh từ sau yellow của chính nó tới xanh kế tiếp bằng `3 + G_hướng_kia + 3 + 3 = G_hướng_kia + 9`. Vì G_hướng_kia nằm trong [30,75], đỏ trọn chu kỳ nằm trong **[39,84] s**; Fixed-Time là **60 s**. Đỏ ban đầu của EW ở t=0 chỉ là phần quan sát được trước xanh đầu tiên: `G_NS + 6`, không phải toàn bộ interval đỏ của một chu kỳ trước đó.
- **Không bảo đảm đỏ ≥15 s cho mọi movement:** một số right-turn link đổi `G → y → r → r → s`. Hai pha `r` trước `s` chỉ là **3+3=6 s**. `s` là chuyển động dừng/nhường rồi đi theo mô hình SUMO, không phải đỏ; luồng rẽ trái `g` cũng có thể cùng mở với luồng đối diện ưu tiên. Không thể suy ra mọi chuyển động hình học xung đột đều bị đỏ suốt xanh của hướng kia.
- Không có biến `red_elapsed`, `min_red` hay assert “mọi đỏ ≥15 s”. Việc kiểm xung đột trong `_check_conflicts` tập trung vào protected `G`; không biến các luồng permissive `g/s` thành protected riêng.
- Episode có thể cắt giữa pha ở t=3600. Phần xanh/đỏ quan sát trong một episode không nhất thiết là một interval hoàn chỉnh. Nếu đổi program/startup offset hoặc mở rộng map, cần kiểm toán lại toàn bộ liên kết.

Nguồn suy luận chương trình: [DRL/core/signal_controller.py:33–42](<D:/grp prj new lap/Adaptive-Traffic-Signal-Control-System/DRL/core/signal_controller.py:33>), [DRL/core/signal_controller.py:47–78](<D:/grp prj new lap/Adaptive-Traffic-Signal-Control-System/DRL/core/signal_controller.py:47>), [DRL/core/signal_controller.py:86–97](<D:/grp prj new lap/Adaptive-Traffic-Signal-Control-System/DRL/core/signal_controller.py:86>), [DRL/core/signal_controller.py:99–154](<D:/grp prj new lap/Adaptive-Traffic-Signal-Control-System/DRL/core/signal_controller.py:99>), [SUMO/Map_Nga_tu/config/traffic_light.add.xml:4–11](<D:/grp prj new lap/Adaptive-Traffic-Signal-Control-System/SUMO/Map_Nga_tu/config/traffic_light.add.xml:4>). Không xác lập vàng 3 s/toàn đỏ 3 s là đủ cho mọi tốc độ hoặc hình học ngoài thực tế chỉ bằng việc chúng tồn tại trong XML.

### 1.3. Observation thực tế và mức độ quan sát của agent

Vector theo thứ tự chính xác:

| Index | Biến đầu vào | Ý nghĩa / đơn vị | Miền khai báo | Miền có ý nghĩa với cấu hình hiện tại | Normalize? |
|---|---|---|---|---|---|
| 0 | `totals["halting_count"]` | Số xe dừng trên các làn vào (xe), không phải queue mét | [0,+inf) | Không âm, không vượt vehicle_count | Không |
| 1 | `totals["waiting_time"] or 0.0` | Tổng current/consecutive waiting của xe trên làn vào (s); không phải accumulated trip delay | [0,+inf) | Không âm; có thể hàng trăm/hàng nghìn; missing bị đổi 0 | Không |
| 2 | `totals["average_speed"] or 0.0` | Tốc độ trung bình có trọng số số xe trên làn vào (m/s) | [0,+inf) | Không âm; giới hạn vType/lane đầu vào tới 13.9 m/s; giá trị thực chưa đo lại | Không |
| 3 | `totals["vehicle_count"]` | Tổng xe đang nằm trên làn vào (xe), không phải toàn mạng | [0,+inf) | Không âm, hữu hạn theo storage và traffic | Không |
| 4 | `phase_id` | Chỉ số phase của TLS J | [0,+inf) | Số nguyên 0…7 nhưng cast float32 | Không; không one-hot |
| 5 | `green_elapsed` | Thời gian xanh đã chạy (s) | [0,+inf) | Tới khoảng 75 trước boundary; reset 0 khi chuyển tiếp | Không |

Nguồn: [DRL/gym_env.py:30–44](<D:/grp prj new lap/Adaptive-Traffic-Signal-Control-System/DRL/gym_env.py:30>), [DRL/core/state_extractor.py:25–60](<D:/grp prj new lap/Adaptive-Traffic-Signal-Control-System/DRL/core/state_extractor.py:25>). StateExtractor đọc từng incoming lane duy nhất; waiting là tổng, speed là trung bình trọng số theo số xe. Mạng chỉ nhận 6 số trên, không nhận toàn bộ dictionary state.

**Điểm mất thông tin:** hai trạng thái có cùng tổng queue/wait/speed/count và cùng phase/elapsed nhưng queue dồn vào hai hướng khác nhau cho **cùng observation**. Hành động tốt nhất có thể trái nhau. Rule-Based lại đọc queue NS/EW riêng. Đây là hạn chế cấu trúc về observability, không thể sửa chỉ bằng tăng `total_timesteps` hay tăng kích thước MLP.

Không có action-mask hoặc dữ liệu `executed_action`/`override_reason` đưa vào observation. Các phase ID cho biết loại pha nhưng không cung cấp elapsed của yellow/all-red; cũng không có countdown tới cuối episode. Model MLP không có bộ nhớ tuần tự để bù toàn bộ thông tin bị bỏ.

### 1.4. Reward: công thức, đơn vị và độ lớn

Công thức đúng theo code: **r_t = -(Q_t + 0.1 W_t)**.

- Q_t: tổng halting_count tại thời điểm cuối interval.
- W_t: tổng waiting_time current snapshot tại thời điểm đó.
- Reward được tính **một lần mỗi quyết định**, không phải mỗi substep 0.1 s. Không tích phân traffic trong 5 s.
- Không có reward clipping, running normalization, chia theo demand/lane capacity, throughput bonus, collision penalty hoặc switch penalty.
- Monitor không chuẩn hóa reward. `normalize_advantage=True` của PPO không chuẩn hóa reward và không làm value target về [-1,1].
- Ví dụ minh họa đại số, không phải phép đo: Q=10,W=100 → r=-20; Q=100,W=2000 → r=-300. Nếu giữ các mức này suốt 720 quyết định, undiscounted episode return tương ứng -14,400 và -216,000.
- Không có giới hạn dưới cấu hình cho reward; với dữ liệu hữu hạn của một episode giá trị vẫn hữu hạn. Không kết luận reward lớn đồng nghĩa PPO chắc chắn không hội tụ.

**Độ lớn từ CSV lịch sử có sẵn**, tái tính bằng đúng công thức trên; mỗi scenario có 720 dòng (không chạy model hoặc SUMO):

| Artifact | Scenario | Mean reward / quyết định | Reward nhỏ nhất | Undiscounted return / episode |
|---|---|---:|---:|---:|
| seed107 | low | -7.7494 | -35.29 | -5,579.55 |
| seed107 | medium | -21.5454 | -77.51 | -15,512.69 |
| seed107 | high | -89.4910 | -356.37 | -64,433.54 |
| seed107 | imbalance | -127.8636 | -543.26 | -92,061.80 |
| seed710 | low | -8.5558 | -38.03 | -6,160.17 |
| seed710 | medium | -23.1519 | -85.41 | -16,669.36 |
| seed710 | high | -151.1814 | -473.59 | -108,850.62 |
| seed710 | imbalance | -177.2209 | -718.67 | -127,599.03 |

Nguồn trực tiếp: [evaluation/seed107/metrics.csv](../evaluation/seed107/metrics.csv), [evaluation/seed710/metrics.csv](../evaluation/seed710/metrics.csv). Đây là độ lớn reward **suy ra cho dữ liệu đánh giá đã lưu**, không phải training return mới hay chứng minh learning curve hội tụ. Chênh lệch low→imbalance khoảng 16.5–20.7 lần theo trị tuyệt đối mean reward cho thấy chọn đều số episode không đồng nghĩa cân bằng scale học.

### 1.5. PPO defaults, budget và Multi-Scenario

Các giá trị default đã đối chiếu cả mã thư viện SB3 2.9.2 lẫn JSON `data` trong hai archive model. Chỉ đọc ZIP/JSON; không giải mã pickle hoặc `PPO.load`:

| Artifact model | Seed lưu | Requested budget từ pipeline | `num_timesteps` lưu | `n_envs` | `policy_kwargs` | Phiên bản SB3 lưu |
|---|---:|---:|---:|---:|---|---|
| `models/seed107/ppo_seed107_final.zip` | 107 | 800,000 | **800,768** | 1 | {} | 2.9.2 |
| `models/seed710/ppo_seed710_final.zip` | 710 | 600,000 | **600,064** | 1 | {} | 2.9.2 |

Vượt budget nhỏ là phù hợp với thu thập trọn rollout 2048: ceil(800000/2048)=391 rollouts; ceil(600000/2048)=293. Không nên báo 800,000 là số cập nhật weights hoặc số substep SUMO. `n_steps=2048` ứng với 10,240 s mô phỏng và 102,400 substeps cho mỗi rollout đầy đủ (qua nhiều episode). Với minibatch64 và n_epochs10, mỗi rollout có 32×10=320 minibatch optimizer steps nếu không ngắt.

`learning_rate=3e-4` và `clip_range=0.2` là hằng số được SB3 bọc schedule, không tự giảm theo tiến độ. Các schedule serialized trong model không được thực thi trong audit. `policy_kwargs={}` không có nghĩa mạng rỗng: MlpPolicy nhận default pi/vf hai lớp 64, Tanh, orthogonal init, Adam.

`MultiScenarioEnv.reset` lấy một integer đều trên [0,4), do đó xác suất lý thuyết mỗi scenario là 25%. **Không round-robin, không bảo đảm số episode bằng nhau**, không stratify trong rollout/minibatch, không log counter riêng từng scenario. Khoảng 2.84 episode/rollout cũng không bảo đảm một update thấy đủ bốn scenario. Không có scenario ID đầu vào policy; agent dùng cùng policy 6-D cho cả bốn tải.

Scenario RNG được seed qua `super().reset(seed=seed)` khi SB3 khởi tạo/reset với seed; sau các reset không truyền seed, RNG tiếp tục. Seed từng episode phía inner env là `base_seed + episode_index`, rồi lại được map thành traffic seed mới trong `TrafficSignalEnv.reset`. Dòng reset không đóng env cũ trước khi thay, nhưng đường kết thúc bình thường đã được `Environment.step` đóng; việc reset giữa episode hoặc lỗi ngoài đường này vẫn cần chú ý vòng đời tài nguyên. Không chạy để thử tình huống đó trong audit.

## 2. Bảng 2 — Đối chiếu công bằng ba phương pháp

| Thông số / cơ chế | Fixed-Time | Rule-Based | DRL PPO | Nhận định công bằng và nguồn |
|---|---|---|---|---|
| Input scenario/network | Cùng mapping bốn scenario | Cùng mapping | Cùng mapping | Khớp hiện tại; `scenarios.yaml:1–4` và entry point tương ứng |
| Simulation step | **0.1 s hard-code** | **0.1 s override** | **0.1 s từ YAML** | Khớp hiện tại; đổi YAML một mình sẽ lệch. [FixedTime/run_fixed_time.py:33–37](<D:/grp prj new lap/Adaptive-Traffic-Signal-Control-System/FixedTime/run_fixed_time.py:33>); [RuleBased/run_rule_based.py:62–64](<D:/grp prj new lap/Adaptive-Traffic-Signal-Control-System/RuleBased/run_rule_based.py:62>); [DRL/configs/traci.yaml:1](<D:/grp prj new lap/Adaptive-Traffic-Signal-Control-System/DRL/configs/traci.yaml:1>) |
| Quyền quản lý đèn | SUMO chạy chương trình static | SignalController | Cùng SignalController | FT không gọi SignalController; không gán min/max của YAML cho FT chỉ vì runner có load settings |
| `min_green` | Không có guard adaptive; xanh luôn **51 s** | Guard policy **30 s hard-code** + controller **30 s YAML** | Controller **30 s YAML** | 51 thuộc [30,75]; khác chiến lược, không tự động là thiên vị. [SUMO/Map_Nga_tu/config/traffic_light.add.xml:4–9](<D:/grp prj new lap/Adaptive-Traffic-Signal-Control-System/SUMO/Map_Nga_tu/config/traffic_light.add.xml:4>); [RuleBased/rule_based_controller.py:30–33](<D:/grp prj new lap/Adaptive-Traffic-Signal-Control-System/RuleBased/rule_based_controller.py:30>); [DRL/core/signal_controller.py:141–142](<D:/grp prj new lap/Adaptive-Traffic-Signal-Control-System/DRL/core/signal_controller.py:141>) |
| `max_green` | Không có guard adaptive; xanh luôn **51 s** | Policy75 hard-code + controller75 | Controller75 | RB/DRL cùng giới hạn hiện tại; nguy cơ drift nếu chỉ đổi YAML. [RuleBased/rule_based_controller.py:32–33](<D:/grp prj new lap/Adaptive-Traffic-Signal-Control-System/RuleBased/rule_based_controller.py:32>); [DRL/core/signal_controller.py:108–123](<D:/grp prj new lap/Adaptive-Traffic-Signal-Control-System/DRL/core/signal_controller.py:108>) |
| Startup xanh | 3 s rồi main48 s | 3 s bắt buộc, không nhận switch ở startup | Giống RB | Cùng startup; tổng xanh adaptive gồm startup |
| Vàng | XML **3 s** mỗi chuyển trục | max(XML3,YAML3)=**3 s** | Giống RB | Khớp hiện tại. [DRL/core/signal_controller.py:42](<D:/grp prj new lap/Adaptive-Traffic-Signal-Control-System/DRL/core/signal_controller.py:42>); [SUMO/Map_Nga_tu/config/traffic_light.add.xml:6–10](<D:/grp prj new lap/Adaptive-Traffic-Signal-Control-System/SUMO/Map_Nga_tu/config/traffic_light.add.xml:6>) |
| Toàn đỏ | XML **3 s** | max(XML3,YAML0)=**3 s** | Giống RB | Khớp thực tế; YAML0 không loại clearance. [SUMO/Map_Nga_tu/config/traffic_light.add.xml:7–11](<D:/grp prj new lap/Adaptive-Traffic-Signal-Control-System/SUMO/Map_Nga_tu/config/traffic_light.add.xml:7>) |
| Decision interval | **Không có quyết định policy**; sampling log5 s | Quyết định tối đa **5 s** | Quyết định tối đa **5 s** | Không được gọi sampling5 s của FT là điều khiển5 s. [FixedTime/run_fixed_time.py:78–106](<D:/grp prj new lap/Adaptive-Traffic-Signal-Control-System/FixedTime/run_fixed_time.py:78>); [DRL/core/environment.py:75–93](<D:/grp prj new lap/Adaptive-Traffic-Signal-Control-System/DRL/core/environment.py:75>) |
| Enforcement min/max | Theo XML fixed51 s | Mỗi bước SUMO0.1 s trong Environment | Giống RB | Max75 không phụ thuộc vòng quyết định5 s |
| Cycle | **114 s** =2×(51+3+3) | Biến thiên; bound lý thuyết **72–162 s** cho cycle hoàn chỉnh | Cùng bound | Chênh cycle là bản chất phương pháp; không phải FT bị min/max sai |
| Đỏ luồng chính / steady cycle | **60 s** | **39–84 s** theo G hướng kia | Cùng bound | Không áp dụng cho mọi permissive movement; xem1.2 |
| Episode horizon | Runner while time<**3600** hard-code | max_episode_seconds=3600, còn scenario end | YAML cap=null, scenario end=3600 | Khớp horizon hiện tại; cách kết thúc không hoàn toàn đồng nhất |
| Demand exhausted | Không kiểm tra sớm trong while của runner | Kết thúc khi minExpectedNumber=0 | Giống RB | Có thể khác horizon nếu scenario kết thúc nhu cầu sớm |
| Seed mô phỏng | CLI seed **truyền thẳng SUMO** | CLI seed **truyền thẳng Environment/SUMO** | CLI seed đi qua RNG rồi tạo **seed SUMO khác** | **Không khớp traffic seed** dù cùng tên seed; [FixedTime/run_fixed_time.py:73](<D:/grp prj new lap/Adaptive-Traffic-Signal-Control-System/FixedTime/run_fixed_time.py:73>); [RuleBased/run_rule_based.py:66](<D:/grp prj new lap/Adaptive-Traffic-Signal-Control-System/RuleBased/run_rule_based.py:66>); [DRL/gym_env.py:54–58](<D:/grp prj new lap/Adaptive-Traffic-Signal-Control-System/DRL/gym_env.py:54>) |
| Thông tin quyết định | Không có observation policy | Queue **NS/EW riêng**, phase, elapsed | Chỉ tổng queue/wait/speed/count, phase, elapsed | **Thông tin không tương đương**; RB có lợi thế thông tin hướng |
| Hàng chờ / waiting | 8 incoming lanes, snapshot log trước bước | Cùng incoming lanes, snapshot trước env.step | Snapshot cuối env.step | Không lệch đơn vị nhưng lệch lưới lấy mẫu đầu/cuối (0…3595 so với5…3600) |
| Average speed | **Toàn mạng** qua vehicle IDs | **Chỉ incoming lanes** | **Chỉ incoming lanes** | **Không cùng phạm vi đo**, chưa so trực tiếp được; [FixedTime/run_fixed_time.py:92–96](<D:/grp prj new lap/Adaptive-Traffic-Signal-Control-System/FixedTime/run_fixed_time.py:92>); [RuleBased/run_rule_based.py:94–96](<D:/grp prj new lap/Adaptive-Traffic-Signal-Control-System/RuleBased/run_rule_based.py:94>); [DRL/gym_env.py:84–91](<D:/grp prj new lap/Adaptive-Traffic-Signal-Control-System/DRL/gym_env.py:84>) |
| Arrivals | Cộng mỗi substep0.1 s | Cộng info chỉ chứa arrivals của substep cuối/5 s | Cùng lỗi info | **RB/PPO đếm thiếu**; [FixedTime/run_fixed_time.py:104–106](<D:/grp prj new lap/Adaptive-Traffic-Signal-Control-System/FixedTime/run_fixed_time.py:104>); [DRL/core/environment.py:81–104](<D:/grp prj new lap/Adaptive-Traffic-Signal-Control-System/DRL/core/environment.py:81>) |
| Giá trị arrivals tổng hợp | Giá trị cumulative cuối log | Giá trị cumulative cuối log, vốn đếm thiếu | Mean của cumulative snapshots trong summary | **Khác ý nghĩa**; [run_pipeline_seed107.py:88–99](<D:/grp prj new lap/Adaptive-Traffic-Signal-Control-System/run_pipeline_seed107.py:88>); [run_pipeline_seed107.py:124–132](<D:/grp prj new lap/Adaptive-Traffic-Signal-Control-System/run_pipeline_seed107.py:124>) |
| Safety policy | Phụ thuộc cùng XML và SUMO | Kiểm protected G + phase timing | Cùng RB, không collision penalty | Chưa chứng minh collision-free; collision.action=warn cho phép tiếp tục |

**Fairness verdict:** RB và PPO đang khớp min/max/yellow/all-red/decision interval và dùng cùng engine ràng buộc. Fixed-Time có 51 s xanh, nằm trong miền [30,75], cùng vàng/toàn đỏ 3 s; không thấy việc cố tình cấp timing an toàn ưu ái một bên từ cấu hình hiện tại. **Fairness tổng thể chưa đạt** do traffic seed, input information và định nghĩa/sampling metric khác nhau. Không đổi tham số hay chạy lại bất kỳ phương pháp nào trong lần audit này.

**Chi tiết lỗi đếm arrivals:** `Environment.step` thực hiện 50 `simulationStep` nhưng chỉ gọi `getArrivedNumber()` khi xây info sau vòng lặp. Đây là số xe đến của bước SUMO cuối, không phải tổng 5 s. RB và evaluate cộng các mẫu thiếu này lại. Kết luận lần này dựa trên vị trí gọi trong mã nguồn; không dùng một lần chạy mô phỏng mới để chứng minh.

**Chi tiết seed:** gọi `env.reset(seed=107)` ở PPO seed RNG của Gymnasium, rồi `np_random.integers(0,2**31-1)` sinh traffic seed; FT/RB lại dùng107 trực tiếp. Dùng cùng CLI flag không đồng nghĩa common random traffic. Cần phân biệt seed policy, seed chọn scenario và seed SUMO trong báo cáo thực nghiệm.

## 3. Trích xuất nguyên văn bốn đoạn code cốt lõi

Các khối bên dưới được lấy trực tiếp theo dòng từ source, giữ nguyên nội dung và thụt lề. Không phải code đề xuất thay thế.

### 3.1. Điều kiện chuyển pha, max-green deadline và green_elapsed

Nguồn: [DRL/core/signal_controller.py:99–154](<D:/grp prj new lap/Adaptive-Traffic-Signal-Control-System/DRL/core/signal_controller.py:99>). Cả `advance` và `request` đều cần đọc: min nằm trong request, max nằm trong deadline/advance.

```python
    def _next(self, tls: str, now: float) -> None:
        s = self._signals[tls]
        previous = s["masks"][s["index"]]
        s["index"] = (s["index"] + 1) % len(s["phases"])
        index = s["index"]
        mask = s["masks"][index]
        if mask and mask != previous:
            s["start"] = now
        final = mask and s["masks"][(index + 1) % len(s["phases"])] != mask
        s["deadline"] = s["start"] + self.maximum if final else now + s["durations"][index]
        self.connection.trafficlight.setPhase(tls, index)
        self.connection.trafficlight.setPhaseDuration(tls, 1e9)

    def advance(self, now: float) -> list[dict]:
        events = []
        for tls, s in self._signals.items():
            while now >= s["deadline"] - 1e-8:
                boundary = s["deadline"]
                if now > boundary + 1e-8:
                    raise ValueError("advance must run at every simulation boundary")
                mask = s["masks"][s["index"]]
                final = mask and s["masks"][(s["index"] + 1) % len(s["phases"])] != mask
                self._next(tls, boundary)
                events.append(dict(tls_id=tls, requested_action=None, executed_action="SWITCH" if final else "NOOP",
                                   override_reason="max_green" if final else "phase_progression", sim_time=boundary))
        return events

    def request(self, actions: dict[str, str], now: float) -> dict[str, dict]:
        if set(actions) - set(self.tls_ids) or any(a not in ("KEEP", "SWITCH") for a in actions.values()):
            raise ValueError("actions must map known TLS IDs to KEEP or SWITCH")
        results = {}
        for tls, action in actions.items():
            s = self._signals[tls]
            index = s["index"]
            mask = s["masks"][index]
            final = mask and s["masks"][(index + 1) % len(s["phases"])] != mask
            executed, reason = action, None
            if not mask:
                executed, reason = "NOOP", "in_transition"
            elif action == "SWITCH":
                if not final:
                    executed, reason = "KEEP", "startup_phase"
                elif now - s["start"] < self.minimum:
                    executed, reason = "KEEP", "min_green"
                else:
                    self._next(tls, now)
            results[tls] = dict(requested_action=action, executed_action=executed, override_reason=reason)
        return results

    def snapshot(self, tls_id: str, now: float) -> dict:
        s = self._signals[tls_id]
        index = s["index"]
        green = bool(s["masks"][index])
        return dict(phase_id=index, phase_state=s["phases"][index].state,
                    green_elapsed=max(0, now - s["start"]) if green else 0,
                    in_transition=not green)
```

### 3.2. Hàm tạo observation thực sự đưa vào PPO

Nguồn: [DRL/gym_env.py:30–44](<D:/grp prj new lap/Adaptive-Traffic-Signal-Control-System/DRL/gym_env.py:30>). StateExtractor vẫn giữ dữ liệu lane-level, nhưng hàm này chỉ lấy totals.

```python
    def _observation(self, state: Mapping) -> np.ndarray:
        values = []
        for tls_id in self._tls_ids:
            totals = state["tls"][tls_id]["totals"]
            values.extend(
                (
                    totals["halting_count"],
                    totals["waiting_time"] or 0.0,
                    totals["average_speed"] or 0.0,
                    totals["vehicle_count"],
                    state["tls"][tls_id]["phase_id"],
                    state["tls"][tls_id]["green_elapsed"],
                )
            )
        return np.asarray(values, dtype=np.float32)
```

### 3.3. Hàm reward

Nguồn: [DRL/gym_env.py:46–52](<D:/grp prj new lap/Adaptive-Traffic-Signal-Control-System/DRL/gym_env.py:46>).

```python
    def _reward(self, state: Mapping) -> float:
        queue = 0.0
        waiting = 0.0
        for tls in state["tls"].values():
            queue += tls["totals"]["halting_count"]
            waiting += tls["totals"]["waiting_time"] or 0.0
        return -(queue + 0.1 * waiting)
```

### 3.4. MultiScenarioEnv và khởi tạo PPO

Nguồn: [DRL/train_multiscenario.py:18–88](<D:/grp prj new lap/Adaptive-Traffic-Signal-Control-System/DRL/train_multiscenario.py:18>). Trích nguyên đoạn liên tục, bao gồm CLI defaults, Monitor, checkpoint, PPO constructor và lời gọi learn để xác định nơi truyền total_timesteps. **Đoạn này chỉ được trích dẫn, không được thực thi trong audit.**

```python
class MultiScenarioEnv(gym.Env):
    """Select a demand scenario on every episode reset."""

    metadata = {"render_modes": []}

    def __init__(self, seed: int):
        super().__init__()
        self._seed = seed
        self._episode = 0
        self._env = None
        self.action_space = spaces.Discrete(2)
        self.observation_space = spaces.Box(
            low=0.0, high=np.inf, shape=(6,), dtype=np.float32
        )

    def reset(self, *, seed=None, options=None):
        super().reset(seed=seed)
        scenario = SCENARIOS[int(self.np_random.integers(len(SCENARIOS)))]
        self._env = TrafficSignalEnv(scenario)
        episode_seed = self._seed + self._episode
        self._episode += 1
        return self._env.reset(seed=episode_seed)

    def step(self, action):
        if self._env is None:
            raise RuntimeError("reset must be called before step")
        return self._env.step(action)

    def close(self):
        if self._env is not None:
            self._env.close()
            self._env = None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=107)
    parser.add_argument("--timesteps", type=int, default=800_000)
    parser.add_argument("--model", type=Path, default=Path("models/ppo_final"))
    parser.add_argument("--log-dir", type=Path, default=Path("runs/ppo_overnight"))
    parser.add_argument("--device", default="auto", choices=("auto", "cpu", "cuda"))
    parser.add_argument("--checkpoint-prefix", default="ppo_multiscenario")
    parser.add_argument(
        "--checkpoint-dir", type=Path, default=Path("models/checkpoints")
    )
    args = parser.parse_args()
    if args.seed < 0 or args.timesteps <= 0:
        parser.error("--seed must be nonnegative and --timesteps must be positive")

    args.log_dir.mkdir(parents=True, exist_ok=True)
    args.checkpoint_dir.mkdir(parents=True, exist_ok=True)
    env = Monitor(MultiScenarioEnv(args.seed))
    callback = CheckpointCallback(
        save_freq=50_000,
        save_path=str(args.checkpoint_dir),
        name_prefix=args.checkpoint_prefix,
    )
    model = PPO(
        "MlpPolicy",
        env,
        seed=args.seed,
        verbose=1,
        tensorboard_log=str(args.log_dir),
        device=args.device,
    )
    try:
        model.learn(total_timesteps=args.timesteps, callback=callback)
        model.save(str(args.model))
    finally:
        env.close()
    print(f"Saved model: {args.model}.zip")
```

## 4. Danh sách điểm bất hợp lý và thứ tự cần xem xét trước khi train lại

Mức ưu tiên dưới đây dựa trên tác động kỹ thuật; **không đồng nhất lỗi đánh giá với nguyên nhân gây PPO không hội tụ**.

| Ưu tiên | Phát hiện | Tác động / kết luận giới hạn | Nguồn |
|---|---|---|---|
| **P0** | Observation không có queue/wait theo NS/EW; RB có thông tin này | Policy không phân biệt được nhiều trạng thái cần action trái nhau. Tăng timesteps không khôi phục dữ liệu đã bỏ | [DRL/gym_env.py:30–44](<D:/grp prj new lap/Adaptive-Traffic-Signal-Control-System/DRL/gym_env.py:30>); [RuleBased/rule_based_controller.py:1–14](<D:/grp prj new lap/Adaptive-Traffic-Signal-Control-System/RuleBased/rule_based_controller.py:1>) |
| **P0** | Input raw [0,+inf), Tanh MLP, không observation normalization | Khác scale hàng nghìn giây so với phase0…7 dễ gây bão hòa. Đây là nguy cơ, chưa đo activation/gradient | [DRL/gym_env.py:23–44](<D:/grp prj new lap/Adaptive-Traffic-Signal-Control-System/DRL/gym_env.py:23>); [SB3/common/policies.py:454](<C:/Users/Admin/miniconda3/envs/atsc/Lib/site-packages/stable_baselines3/common/policies.py:454>) |
| **P0** | Seed SUMO của PPO bị remap, baseline truyền thẳng seed | So sánh không cùng điều kiện ngẫu nhiên; không đủ cơ sở xếp hạng chỉ từ một episode/scenario | [DRL/gym_env.py:54–58](<D:/grp prj new lap/Adaptive-Traffic-Signal-Control-System/DRL/gym_env.py:54>); [FixedTime/run_fixed_time.py:73](<D:/grp prj new lap/Adaptive-Traffic-Signal-Control-System/FixedTime/run_fixed_time.py:73>) |
| **P0** | Arrivals chỉ lấy substep cuối interval | Sai throughput và chỉ số phụ thuộc arrivals; **không trực tiếp đổi reward hiện tại** vì reward không chứa arrivals | [DRL/core/environment.py:81–104](<D:/grp prj new lap/Adaptive-Traffic-Signal-Control-System/DRL/core/environment.py:81>); [DRL/gym_env.py:46–52](<D:/grp prj new lap/Adaptive-Traffic-Signal-Control-System/DRL/gym_env.py:46>) |
| **P0** | Average speed khác phạm vi, arrived_count mean vs final; delay/vehicle lấy mean waiting snapshot chia arrivals | Các bảng hiện có dễ dẫn tới kết luận sai. Công thức delay này không phải tổng trip delay/xe | [FixedTime/run_fixed_time.py:92–96](<D:/grp prj new lap/Adaptive-Traffic-Signal-Control-System/FixedTime/run_fixed_time.py:92>); [run_pipeline_seed107.py:88–132](<D:/grp prj new lap/Adaptive-Traffic-Signal-Control-System/run_pipeline_seed107.py:88>) |
| **P1** | Reward không normalization, W không bị chặn, khác scale mạnh giữa tải | Critic/gradient có thể bị kịch bản tải cao chi phối; advantage normalization không chuẩn hóa value target | [DRL/gym_env.py:46–52](<D:/grp prj new lap/Adaptive-Traffic-Signal-Control-System/DRL/gym_env.py:46>); dữ liệu1.4 |
| **P1** | Random scenario không quota; rollout chỉ ~2.84 episodes | Không bảo đảm đủ/cân bằng4 tải trong mỗi update; không có breakdown train metrics riêng theo scenario | [DRL/train_multiscenario.py:33–39](<D:/grp prj new lap/Adaptive-Traffic-Signal-Control-System/DRL/train_multiscenario.py:33>); [SB3/ppo/ppo.py:85](<C:/Users/Admin/miniconda3/envs/atsc/Lib/site-packages/stable_baselines3/ppo/ppo.py:85>) |
| **P1** | ent_coef=0, target_kl=None, LR cố định3e-4 | Không entropy bonus/KL early-stop/LR decay. Cần log/ablation để biết có phải nguyên nhân collapse; không kết luận default sai chỉ vì là default | [SB3/ppo/ppo.py:84–100](<C:/Users/Admin/miniconda3/envs/atsc/Lib/site-packages/stable_baselines3/ppo/ppo.py:84>) |
| **P1** | Không action mask, requested SWITCH thường thành KEEP/NOOP | Nhiều decision không có quyền can thiệp; policy credit assignment kém trực tiếp | [DRL/core/signal_controller.py:126–146](<D:/grp prj new lap/Adaptive-Traffic-Signal-Control-System/DRL/core/signal_controller.py:126>) |
| **P1** | Chỉ checkpoint định kỳ, không validation/best-model selection | Không có bằng chứng checkpoint500k hay model cuối tốt nhất; đánh giá hiện tại chỉ final model theo pipeline | [DRL/train_multiscenario.py:69–85](<D:/grp prj new lap/Adaptive-Traffic-Signal-Control-System/DRL/train_multiscenario.py:69>); `run_pipeline_seed107.py`/`run_pipeline_seed710.py` |
| **P1** | Train cutoff3600 còn demand tới3600; không drain; không observation thời gian còn lại | Chưa đo hết độ trễ của xe chưa hoàn thành; cần phân biệt horizon objective và completion metrics. Không tự kết luận PPO time-limit bootstrap sai | Bốn scenario XML; [DRL/core/environment.py:37–45](<D:/grp prj new lap/Adaptive-Traffic-Signal-Control-System/DRL/core/environment.py:37>); [DRL/gym_env.py:34–42](<D:/grp prj new lap/Adaptive-Traffic-Signal-Control-System/DRL/gym_env.py:34>) |
| **P1** | Không collision reward/termination; collision.action=warn | Giảm queue không chứng minh an toàn. Safety timing guard không thay validation các luồng permissive | [DRL/gym_env.py:46–52](<D:/grp prj new lap/Adaptive-Traffic-Signal-Control-System/DRL/gym_env.py:46>); scenario processing; [DRL/core/signal_controller.py:86–97](<D:/grp prj new lap/Adaptive-Traffic-Signal-Control-System/DRL/core/signal_controller.py:86>) |
| **P1** | RB hard-code30/75, FT/RB hard-code0.1; FT sampling5 và cutoff3600 | Hiện khớp, nhưng chỉ đổi YAML sẽ làm audit fairness lỗi thời | [RuleBased/rule_based_controller.py:30–33](<D:/grp prj new lap/Adaptive-Traffic-Signal-Control-System/RuleBased/rule_based_controller.py:30>); [FixedTime/run_fixed_time.py:33–37](<D:/grp prj new lap/Adaptive-Traffic-Signal-Control-System/FixedTime/run_fixed_time.py:33>); [FixedTime/run_fixed_time.py:80–106](<D:/grp prj new lap/Adaptive-Traffic-Signal-Control-System/FixedTime/run_fixed_time.py:80>) |
| **P1** | Dependencies không đầy đủ/pin; hầu hết PPO params không explicit | Default có thể đổi ở môi trường cài mới. SB3 hiện tại và archive đều2.9.2 nên audit này có nguồn xác định | [DRL/requirements.txt:1](<D:/grp prj new lap/Adaptive-Traffic-Signal-Control-System/DRL/requirements.txt:1>); [DRL/train_multiscenario.py:75–82](<D:/grp prj new lap/Adaptive-Traffic-Signal-Control-System/DRL/train_multiscenario.py:75>) |
| **P2** | Phase ID ordinal; không flag missing; None→0 | Thứ tự phase có khoảng cách số học không có nghĩa; lỗi sensor có thể bị coi là trạng thái tốt | [DRL/gym_env.py:34–42](<D:/grp prj new lap/Adaptive-Traffic-Signal-Control-System/DRL/gym_env.py:34>); [DRL/core/state_extractor.py:7–9](<D:/grp prj new lap/Adaptive-Traffic-Signal-Control-System/DRL/core/state_extractor.py:7>) |
| **P2** | min_red>=15 không được kiểm; giả định đỏ15 bị nhầm với xanh15 | **Không xác nhận vi phạm pháp luật từ giả định này.** Xanh hoàn chỉnh30/51 s đáp ứng ngưỡng15 đã kiểm; chưa chứng nhận an toàn/tuân thủ toàn hệ thống | Mục1.2; [QCVN A.2](https://congbaocdn.chinhphu.vn/CongBaoCP/VanBan/2024/11/43387/53148-1-20241359-136051-2024-tt-bgtvt.pdf#page=86) |
| **P2** | Program0 trong network và programtest additional có timing khác | Dễ audit nhầm42 s thay51 s nếu chỉ đọc net.xml; cần giữ rõ active-program provenance khi sửa đầu vào | [SUMO/Map_Nga_tu/network/intersection.net.xml:123–128](<D:/grp prj new lap/Adaptive-Traffic-Signal-Control-System/SUMO/Map_Nga_tu/network/intersection.net.xml:123>); [SUMO/Map_Nga_tu/config/traffic_light.add.xml:3–12](<D:/grp prj new lap/Adaptive-Traffic-Signal-Control-System/SUMO/Map_Nga_tu/config/traffic_light.add.xml:3>) |

**Trước khi huấn luyện lại:** nên chốt thiết kế observation, thống nhất seeds/metrics, thống nhất nguồn tham số và ghi explicit cấu hình PPO/dependencies; sau đó mới thiết kế thay đổi reward/siêu tham số có kiểm soát. Đây là đề nghị để người đọc duyệt, chưa áp dụng thay đổi nào.

**Giới hạn của báo cáo:** không chạy train/evaluation/simulation/tests; không đo learning curve mới, reward distribution của lần train sắp tới, activation saturation, KL, collision rate hay chứng minh hội tụ. Phần timing/fairness là phân tích tĩnh của source và input đang có. Dữ liệu reward chỉ được tái tính từ CSV lịch sử, không suy diễn thành hiệu năng hiện tại sau thay đổi.

**Kiểm tra toàn vẹn:** so sánh SHA-256 trước/sau trên **62 tệp nguồn/cấu hình/tài liệu đầu vào** đã đọc dưới DRL, FixedTime, RuleBased, SUMO và ba script root liên quan. Không thay đổi các tệp này; đầu ra duy nhất là `results/parameter_audit_report.md`.

