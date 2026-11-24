# Audit Supplement — Directional State, Fairness và TensorBoard

Ngày: **15/11/2026 (Asia/Bangkok)**. Commit: **d84f3279b808d6292dfd0d37ef9e89f53364170c**.

**Phạm vi:** chỉ đọc mã nguồn và event log có sẵn. Đã chạy đúng một script Python nhỏ bằng `C:\Users\Admin\miniconda3\envs\atsc\python.exe -B -` để đọc TensorBoard qua `EventAccumulator`. Không chạy SUMO, train, evaluate hoặc entry point của dự án; không sửa code/config. Đầu ra duy nhất của bước bổ sung là `results/parameter_audit_supplement.md`; báo cáo audit trước được giữ nguyên.

## 1. Logic phân tách hướng và quyết định của Rule-Based

### 1.1. Toàn bộ code nguyên văn

Nguồn: [RuleBased/rule_based_controller.py:1–43](<D:/grp prj new lap/Adaptive-Traffic-Signal-Control-System/RuleBased/rule_based_controller.py:1>).

```python
def get_group_queues(state):
    lanes = state["tls"]["J"]["lanes"]
    ns_lanes = ["N_in_0", "N_in_1", "S_in_0", "S_in_1"]
    ew_lanes = ["E_in_0", "E_in_1", "W_in_0", "W_in_1"]

    queue_ns = 0
    for lane_id in ns_lanes:
        queue_ns += lanes[lane_id]["halting_count"]

    queue_ew = 0
    for lane_id in ew_lanes:
        queue_ew += lanes[lane_id]["halting_count"]

    return {"NS": queue_ns, "EW": queue_ew}

def get_current_group(state):
    phase_id = state["tls"]["J"]["phase_id"]

    if phase_id in (0, 1):
        return "NS"
    elif phase_id in (4, 5):
        return "EW"
    else:
        return None

def choose_action(state):
    tls = state["tls"]["J"]

    current_group = get_current_group(state)
    if current_group is None or tls["green_elapsed"] < 30:
        return "KEEP"
    if tls["green_elapsed"] >= 75:
        return "SWITCH"

    queues = get_group_queues(state)
    if current_group == "NS":
        other_group = "EW"
    else:
        other_group = "NS"

    if queues[other_group] > queues[current_group]:
        return "SWITCH"
    return "KEEP"
```

### 1.2. Lane IDs và quy tắc chính xác

| Nội dung | Giá trị / điều kiện trong code |
|---|---|
| NS | `N_in_0`, `N_in_1`, `S_in_0`, `S_in_1` |
| EW | `E_in_0`, `E_in_1`, `W_in_0`, `W_in_1` |
| Queue NS | Tổng `halting_count` của 4 làn NS |
| Queue EW | Tổng `halting_count` của 4 làn EW |
| Trục đang xanh | phase 0 hoặc 1 → NS; phase 4 hoặc 5 → EW; còn lại → None |
| Chưa xanh đủ 30 s | `KEEP` |
| Đang pha ngoài hai nhóm xanh | `KEEP` |
| Xanh đạt ít nhất 75 s | `SWITCH`, trước khi xét chênh lệch queue |
| Xanh từ 30 s đến dưới 75 s | `SWITCH` khi `Q_other > Q_current`; ngược lại `KEEP` |
| Hai queue bằng nhau | `KEEP` |
| Ngưỡng kích hoạt | Chênh lệch **dương bất kỳ**; do queue là số nguyên, tối thiểu 1 xe |
| Hysteresis / tỷ lệ / waiting threshold | Không có trong file này |
| Waiting time / speed | Không tham gia công thức chọn action của Rule-Based |

Thứ tự điều kiện quan trọng: kiểm tra phase/green<30 trước, rồi green>=75, rồi so queue. Các số **30 và 75 được hard-code** trong policy; lớp SignalController còn thực thi ràng buộc riêng. `choose_action` trả về **yêu cầu** KEEP/SWITCH, không trực tiếp chỉnh phase SUMO.

### 1.3. Cấu hình liên quan trong runner

Nguồn: [RuleBased/run_rule_based.py:62–66](<D:/grp prj new lap/Adaptive-Traffic-Signal-Control-System/RuleBased/run_rule_based.py:62>).

```python
with Environment(
    settings={"gui": False, "max_episode_seconds": 3600, "simulation_step": 0.1}
) as env:

    state = env.reset(args.scenario, seed=args.seed)
```

Runner dùng cùng `Environment` ở `DRL/core`, ép `gui=False`, `max_episode_seconds=3600` và `simulation_step=0.1`; seed CLI được truyền thẳng vào `Environment.reset`. Runner không override `decision_interval`, `min_green`, `max_green`, `yellow_time` hoặc `all_red_time`; các giá trị đó đến từ cấu hình chung. Yêu cầu action được tạo tại dòng 74, thực thi ở dòng 88, rồi ghi `executed_action`/`override_reason` ở dòng 91–92. Nguồn: [RuleBased/run_rule_based.py:73–98](<D:/grp prj new lap/Adaptive-Traffic-Signal-Control-System/RuleBased/run_rule_based.py:73>).

## 2. StateExtractor: toàn bộ code và cấu trúc state

### 2.1. Toàn bộ code nguyên văn

Nguồn: [DRL/core/state_extractor.py:1–60](<D:/grp prj new lap/Adaptive-Traffic-Signal-Control-System/DRL/core/state_extractor.py:1>).

```python
"""JSON-ready snapshots of unique incoming lanes for each controlled junction."""
import math

from .signal_controller import SignalController


def _metric(value: float) -> float | None:
    value = float(value)
    return value if math.isfinite(value) and value >= 0 else None


class StateExtractor:
    def __init__(self, connection, signals: SignalController):
        self.connection = connection
        self.signals = signals
        self.incoming = {
            tls: tuple(dict.fromkeys(
                link[0]
                for group in connection.trafficlight.getControlledLinks(tls)
                for link in group
            ))
            for tls in signals.tls_ids
        }

    def extract(self, scenario: str, now: float) -> dict:
        api = self.connection.lane
        lane_data = {}
        for lane in dict.fromkeys(lane for lanes in self.incoming.values() for lane in lanes):
            count = api.getLastStepVehicleNumber(lane)
            halting = api.getLastStepHaltingNumber(lane)
            if count < 0 or halting < 0 or halting > count:
                raise ValueError(f"Invalid vehicle counts for lane {lane}")
            lane_data[lane] = {
                "vehicle_count": count,
                "halting_count": halting,
                "waiting_time": _metric(api.getWaitingTime(lane)),
                "average_speed": _metric(api.getLastStepMeanSpeed(lane)) if count else None,
            }
        tls_data = {}
        for tls, lane_ids in self.incoming.items():
            lanes = {lane: lane_data[lane] for lane in lane_ids}
            total = sum(lane["vehicle_count"] for lane in lanes.values())
            occupied = [lane for lane in lanes.values() if lane["vehicle_count"]]
            waiting = [lane["waiting_time"] for lane in lanes.values()]
            tls_data[tls] = {
                "tls_id": tls,
                **self.signals.snapshot(tls, now),
                "incoming_lane_ids": list(lane_ids),
                "lanes": lanes,
                "totals": {
                    "vehicle_count": total,
                    "halting_count": sum(lane["halting_count"] for lane in lanes.values()),
                    "waiting_time": sum(waiting) if all(v is not None for v in waiting) else None,
                    "average_speed": (
                        sum(lane["average_speed"] * lane["vehicle_count"] for lane in occupied) / total
                        if total and all(lane["average_speed"] is not None for lane in occupied) else None
                    ),
                },
            }
        return {"simulation_time": float(now), "scenario": scenario, "tls": tls_data}
```

### 2.2. Các field snapshot được ghép vào TLS

`**self.signals.snapshot(tls, now)` lấy thêm các field từ hàm sau. Nguồn: [DRL/core/signal_controller.py:148–154](<D:/grp prj new lap/Adaptive-Traffic-Signal-Control-System/DRL/core/signal_controller.py:148>).

```python
    def snapshot(self, tls_id: str, now: float) -> dict:
        s = self._signals[tls_id]
        index = s["index"]
        green = bool(s["masks"][index])
        return dict(phase_id=index, phase_state=s["phases"][index].state,
                    green_elapsed=max(0, now - s["start"]) if green else 0,
                    in_transition=not green)
```

### 2.3. Schema dictionary trả về

Đây là **schema mô tả từ code**, không phải state thu được bằng chạy mô phỏng:

```text
state: dict
├── simulation_time: float                    # giây mô phỏng
├── scenario: str                             # low / medium / high / imbalance
└── tls: dict[tls_id, dict]
    └── <tls_id>                              # J ở ngã tư hiện tại
        ├── tls_id: str
        ├── phase_id: int
        ├── phase_state: str                  # chuỗi r/G/g/y/s của chương trình
        ├── green_elapsed: number             # giây; 0 khi chuyển tiếp
        ├── in_transition: bool
        ├── incoming_lane_ids: list[str]
        ├── lanes: dict[lane_id, dict]
        │   └── <lane_id>
        │       ├── vehicle_count: int
        │       ├── halting_count: int
        │       ├── waiting_time: float | None
        │       └── average_speed: float | None
        └── totals: dict
            ├── vehicle_count: int
            ├── halting_count: int
            ├── waiting_time: float | None
            └── average_speed: float | None
```

Đường dẫn chính xác tới biến directional có sẵn:

- `state["tls"]["J"]["lanes"][lane_id]["halting_count"]`.
- `state["tls"]["J"]["lanes"][lane_id]["vehicle_count"]`.
- `state["tls"]["J"]["lanes"][lane_id]["waiting_time"]`.
- `state["tls"]["J"]["lanes"][lane_id]["average_speed"]`.

**Không có key NS/EW hoặc nhóm hướng trong state trả về.** Nhóm NS/EW được Rule-Based tạo bên ngoài bằng lane IDs. `incoming_lane_ids` được phát hiện từ controlled links và loại trùng, không dựa vào danh sách hard-code của Rule-Based.

### 2.4. Đơn vị và phép gộp cần giữ đúng

| Field | Ý nghĩa / quy tắc trong source |
|---|---|
| `halting_count` | Số xe dừng; không phải queue length theo mét |
| `vehicle_count` | Số xe trên incoming lane ở last step; không phải tổng xe toàn mạng |
| `waiting_time` | Lấy `lane.getWaitingTime`; tổng current waiting của xe trên làn, đơn vị giây; không phải tổng trip delay tích lũy |
| `average_speed` cấp làn | Lấy `lane.getLastStepMeanSpeed` nếu có xe; làn rỗng trả None |
| `_metric` | Đổi giá trị không hữu hạn hoặc âm thành None; giá trị hợp lệ đổi float |
| `totals.vehicle_count` | Tổng vehicle_count trên các làn vào duy nhất của TLS |
| `totals.halting_count` | Tổng halting_count trên các làn vào |
| `totals.waiting_time` | Chỉ tính tổng khi tất cả lane waiting_time đều khác None; nếu thiếu thì None |
| `totals.average_speed` | Trung bình có trọng số vehicle_count trên các làn có xe; None nếu tổng xe=0 hoặc một làn có xe bị thiếu speed |
| `simulation_time` | Ép float từ now; không phải timestamp thời gian thực |

Với các tập lane ở mục 1, dữ liệu hiện có đủ để tính **Q_NS, Q_EW, N_NS, N_EW, W_NS, W_EW và speed từng trục có trọng số số xe** mà không cần thêm phép đo TraCI. Đây là nhận xét về dữ liệu sẵn có, chưa chọn shape hay triển khai observation mới. Khi gộp waiting phải giữ rõ chính sách None; khi gộp speed không lấy trung bình đơn giản của các lane mean.

Observation PPO hiện tại chỉ lấy totals cùng phase_id/green_elapsed ở [DRL/gym_env.py:30–44](<D:/grp prj new lap/Adaptive-Traffic-Signal-Control-System/DRL/gym_env.py:30>), nên dữ liệu từng làn đã có trong state nhưng bị bỏ khi encode cho policy.

## 3. Code gây lệch arrivals, average_speed và seed

Các đoạn sau giữ nguyên source, kể cả thụt lề; chúng chỉ được trích dẫn, không thực thi.

### 3.1. Arrivals: đọc ở cuối interval thay vì cộng từng simulationStep

Nguồn: [DRL/core/environment.py:81–107](<D:/grp prj new lap/Adaptive-Traffic-Signal-Control-System/DRL/core/environment.py:81>) trong `Environment.step`.

```python
            while not terminated and now < deadline - 1e-8:
                self.connection.simulationStep()
                now = self.connection.simulation.getTime()
                events = self.signals.advance(now)
                for event in events:
                    if event["override_reason"] == "max_green":
                        decisions[event["tls_id"]].update(
                            executed_action="SWITCH", override_reason="max_green")
                automatic.extend(events)
                terminated = self.connection.simulation.getMinExpectedNumber() == 0
                truncated = not terminated and self._end is not None and now >= self._end - 1e-8
                if terminated or truncated:
                    break
            self._state = self.extractor.extract(self.scenario.name, now)
            info = {
                key: {tls: decision[key] for tls, decision in decisions.items()}
                for key in ("requested_action", "executed_action", "override_reason")
            }
            info.update(
                sim_time=now,
                phase_id={tls: value["phase_id"] for tls, value in self._state["tls"].items()},
                green_elapsed={tls: value["green_elapsed"] for tls, value in self._state["tls"].items()},
                automatic_events=automatic,
                arrived_count=self.connection.simulation.getArrivedNumber(),
                vehicles_in_network=self.connection.vehicle.getIDCount(),
                end_reason="demand_exhausted" if terminated else "time_limit" if truncated else None,
            )
```

**Vị trí gây lệch:** vòng lặp có nhiều `simulationStep()`, nhưng `getArrivedNumber()` chỉ được gọi ở dòng 104, sau vòng lặp. Với interval 5 s và step 0.1 s, một interval bình thường có 50 substeps; `info["arrived_count"]` chỉ chứa arrivals của substep cuối, không chứa tổng cả interval.

Rule-Based cộng giá trị info này ở [RuleBased/run_rule_based.py:88–89](<D:/grp prj new lap/Adaptive-Traffic-Signal-Control-System/RuleBased/run_rule_based.py:88>); DRL evaluate cộng nó ở [DRL/evaluate.py:31–41](<D:/grp prj new lap/Adaptive-Traffic-Signal-Control-System/DRL/evaluate.py:31>). Cộng các giá trị đã thiếu không khôi phục các arrivals ở substep trước. Fixed-Time lại cộng `getArrivedNumber()` ngay sau mỗi simulationStep ở [FixedTime/run_fixed_time.py:104–106](<D:/grp prj new lap/Adaptive-Traffic-Signal-Control-System/FixedTime/run_fixed_time.py:104>).

Đây là lỗi đo lường; reward hiện tại chỉ chứa queue/wait nên lỗi arrivals không trực tiếp nằm trong công thức reward.

### 3.2. Average speed: toàn mạng ở Fixed-Time, incoming lanes ở PPO

**Fixed-Time**, nguồn [FixedTime/run_fixed_time.py:92–97](<D:/grp prj new lap/Adaptive-Traffic-Signal-Control-System/FixedTime/run_fixed_time.py:92>):

```python
                    "average_speed": (
                        sum(connection.vehicle.getSpeed(vehicle_id)
                            for vehicle_id in connection.vehicle.getIDList())
                        / connection.vehicle.getIDCount()
                        if connection.vehicle.getIDCount() else 0.0
                    ),
```

`connection.vehicle.getIDList()` lấy danh sách xe toàn mạng. Vì vậy đây là trung bình tốc độ toàn mạng, gồm xe trên các phần mạng khác ngoài incoming lanes.

**PPO**, nguồn [DRL/gym_env.py:84–91](<D:/grp prj new lap/Adaptive-Traffic-Signal-Control-System/DRL/gym_env.py:84>):

```python
        vehicles = sum(
            tls["totals"]["vehicle_count"] for tls in state["tls"].values()
        )
        speed_weight = sum(
            (tls["totals"]["average_speed"] or 0.0) * tls["totals"]["vehicle_count"]
            for tls in state["tls"].values()
        )
        info["average_speed"] = speed_weight / vehicles if vehicles else 0.0
```

`state["tls"][...]["totals"]` chỉ tổng hợp các incoming lanes do StateExtractor phát hiện. Trong map một TLS, speed PPO chính là speed có trọng số xe trên các làn vào. Rule-Based cũng ghi speed từ `state["tls"]["J"]["totals"]["average_speed"]` ở [RuleBased/run_rule_based.py:94–96](<D:/grp prj new lap/Adaptive-Traffic-Signal-Control-System/RuleBased/run_rule_based.py:94>).

Hai chỉ số đều mang tên average_speed và đơn vị m/s nhưng **khác tập xe được đo**, nên chưa thể so trực tiếp. Ngoài ra, Fixed-Time lấy snapshot trước bước, còn speed Rule-Based/PPO được đọc sau env.step; phải tách lệch phạm vi với lệch thời điểm lấy mẫu.

### 3.3. Seed: PPO tạo seed SUMO khác từ RNG đã seed

Nguồn: [DRL/gym_env.py:54–58](<D:/grp prj new lap/Adaptive-Traffic-Signal-Control-System/DRL/gym_env.py:54>).

```python
    def reset(self, *, seed: int | None = None, options=None):
        super().reset(seed=seed)
        state = self._environment.reset(
            self.scenario, seed=int(self.np_random.integers(0, 2**31 - 1))
        )
```

`super().reset(seed=seed)` seed RNG Gymnasium; `self.np_random.integers(0, 2**31 - 1)` sau đó sinh một số nguyên mới để truyền vào core Environment/SUMO. Vì vậy CLI/reset seed ban đầu không được dùng trực tiếp làm traffic seed.

Đối chiếu: Rule-Based truyền `seed=args.seed` ở mục 1.3; Fixed-Time truyền `seed=args.seed` vào `simulation.start` ở [FixedTime/run_fixed_time.py:73](<D:/grp prj new lap/Adaptive-Traffic-Signal-Control-System/FixedTime/run_fixed_time.py:73>). Cùng CLI seed giữa ba phương pháp chưa có nghĩa cùng seed SUMO. Không chạy RNG hay môi trường để sinh số seed minh họa trong bước bổ sung này.

## 4. Chỉ số train/* từ log TensorBoard có sẵn

### 4.1. Phương pháp trích xuất

- Interpreter: `C:\Users\Admin\miniconda3\envs\atsc\python.exe`, tùy chọn `-B` để không sinh bytecode.
- Reader: `tensorboard.backend.event_processing.event_accumulator.EventAccumulator`.
- Dùng `size_guidance={"scalars": 0}` để đọc toàn bộ scalar samples, không reservoir sampling; `purge_orphaned_data=False` để không tự loại record do restart.
- Đọc từng event file riêng, sắp mẫu theo `(step, wall_time)`. Không gộp hai run, không smoothing hay nội suy.
- Đầu/cuối là record ở step đầu/cuối. Min/max là cực trị số học và kèm step tương ứng; nếu bằng nhau lấy record đầu theo thứ tự đã sắp.
- Mean là trung bình số học của **các scalar đã log**, dùng `math.fsum(values)/n`; không phải mean trên toàn bộ minibatch, episode hoặc scenario.
- **Cả 10 chuỗi đều đầy đủ tag, không có NaN/Inf và không trùng step.** Seed710 có 292 mẫu/tag; overnight có 390 mẫu/tag.
- Giá trị dưới đây giữ biểu diễn số đọc được và mean tính bằng Python; `step` là global RL timesteps ghi trong event, không phải substep SUMO hay số gradient update.
- Các `train/*` này bắt đầu tại step **4096**. Không tự điền giá trị step 0 hoặc 2048.

### runs/ppo_seed710

Event file: `runs/ppo_seed710/PPO_1/events.out.tfevents.1794253623.DESKTOP-JOM6VM1.16568.0`.

| Chỉ số | Số mẫu | Đầu: giá trị @ step | Min: giá trị @ step | Max: giá trị @ step | Trung bình | Cuối: giá trị @ step |
|---|---:|---:|---:|---:|---:|---:|
| `train/value_loss` | 292 | 916385.6875 @ 4096 | 1831.27392578125 @ 528384 | 22950840 @ 86016 | 3522991.3643949325 | 3473017.5 @ 600064 |
| `train/entropy_loss` | 292 | -0.6851572394371033 @ 4096 | -0.685667872428894 @ 6144 | -0.12665848433971405 @ 460800 | -0.4751855689675024 | -0.4359149634838104 @ 600064 |
| `train/approx_kl` | 292 | 0.013238885439932346 @ 4096 | 0.000036564641050063074 @ 372736 | 0.04104343056678772 @ 368640 | 0.0027751023204373644 | 0.007122336886823177 @ 600064 |
| `train/explained_variance` | 292 | -0.0008754730224609375 @ 4096 | -0.23651564121246338 @ 460800 | 0.8396852612495422 @ 565248 | 0.04950952387019379 | 0.028570711612701416 @ 600064 |
| `train/policy_gradient_loss` | 292 | -0.003390080062672496 @ 4096 | -0.008708213455975056 @ 169984 | 0.0017605460016056895 @ 546816 | -0.0022683409518708376 | -0.0022729365155100822 @ 600064 |

### runs/ppo_overnight

Event file: `runs/ppo_overnight/PPO_1/events.out.tfevents.1794000392.DESKTOP-JOM6VM1.2656.0`.

| Chỉ số | Số mẫu | Đầu: giá trị @ step | Min: giá trị @ step | Max: giá trị @ step | Trung bình | Cuối: giá trị @ step |
|---|---:|---:|---:|---:|---:|---:|
| `train/value_loss` | 390 | 6135873 @ 4096 | 1690.97216796875 @ 516096 | 111255520 @ 90112 | 3466996.9376890524 | 742015.125 @ 800768 |
| `train/entropy_loss` | 390 | -0.6930564045906067 @ 4096 | -0.6930564045906067 @ 4096 | -0.23042675852775574 @ 399360 | -0.46909644244573057 | -0.3839928209781647 @ 800768 |
| `train/approx_kl` | 390 | 0.00014583294978365302 @ 4096 | 0.000014010074664838612 @ 49152 | 0.036893002688884735 @ 385024 | 0.0030657836059197925 | 0.0030773868784308434 @ 800768 |
| `train/explained_variance` | 390 | 0.00011068582534790039 @ 4096 | -1.3320446014404297 @ 700416 | 0.8679311871528625 @ 593920 | 0.06388317881486355 | 0.3923337459564209 @ 800768 |
| `train/policy_gradient_loss` | 390 | -0.00010129963629879057 @ 4096 | -0.015456045046448708 @ 606208 | 0.0027074036188423634 @ 512000 | -0.002015283877153706 | -0.0030862754210829735 @ 800768 |

### 4.2. Diễn giải kỹ thuật có giới hạn

| Chỉ số | Nhận xét từ số đã trích |
|---|---|
| `train/value_loss` | Seed710 đạt max **22,950,840** và cuối **3,473,017.5**; overnight đạt max **111,255,520** và cuối **742,015.125**. Có khoảng dao động cực lớn giữa min/max. Giá trị tuyệt đối phụ thuộc scale reward/return; chưa thể quy toàn bộ cho learning rate hoặc tuyên bố policy phân kỳ chỉ từ loss |
| `train/entropy_loss` | Đây là loss mang dấu âm của entropy. **Min âm hơn → entropy cao hơn; max gần 0 hơn → policy ít entropy hơn.** Với 2 action, entropy tối đa lý thuyết ln(2)≈0.6931; overnight đầu gần -0.6931 phù hợp gần phân bố đều. Max entropy_loss không phải “đỉnh khám phá” |
| `train/approx_kl` | Mean khoảng **0.002775** và **0.003066**, nhưng max lần lượt **0.041043** và **0.036893**. Mean nhỏ không loại trừ update có KL lớn hơn nhiều. Không kết luận quá ngưỡng cấu hình vì target_kl hiện không đặt |
| `train/explained_variance` | Seed710 mean **0.04951**, cuối **0.02857**; overnight mean **0.06388**, cuối **0.39233**. Critic có khả năng giải thích return thấp trên nhiều batch được log. Cả hai có đoạn âm; overnight min **-1.33204** ở700416. Max 0.83969/0.86793 không chứng minh chất lượng đó được duy trì đến cuối |
| `train/policy_gradient_loss` | Mean khoảng **-0.002268** và **-0.002015**. Dấu âm, trị tuyệt đối nhỏ hoặc max dương không tự xác nhận policy tốt/xấu; đây là PPO surrogate-loss statistic, không phải traffic performance hoặc policy-gradient norm |

**Kết luận từ phần log:** có dấu hiệu critic học chưa ổn định trên các batch đã log; overnight kết thúc với explained variance tốt hơn seed710, nhưng cả hai mean còn thấp. Không đủ dữ liệu từ năm scalar này để khẳng định policy đã hội tụ, xác định checkpoint tốt nhất hoặc quy nguyên nhân cho một tham số. Multi-scenario và reward scale khác nhau có thể góp phần làm thống kê thay đổi; cần tách đây là giả thuyết kỹ thuật, chưa phải quan hệ nhân quả đã kiểm chứng.

**Toàn vẹn:** trước/sau bước bổ sung đã đối chiếu SHA-256 của **191 tệp Git-tracked**; không tệp nào thay đổi. Không tạo script trong dự án và không sửa báo cáo parameter audit trước. Chỉ tạo báo cáo supplement này.

