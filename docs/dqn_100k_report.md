# Kết quả DQN 100.000 bước

Cấu trúc file: cấu hình chung, lịch sử thay đổi mô hình, Phần 1 (toàn bộ kết quả v1), Phần 2 (v2: chẩn đoán, kế hoạch và kết quả). Mỗi bảng kết quả ghi rõ phiên bản.

## Cấu hình chung (đánh giá, giữ nguyên giữa các phiên bản)
- Seed giao thông khi train: 0 đến 9 (không dùng 57, 367, 1024); seed giao thông khi test: 57, 367, 1024 (cùng seed với fixed-time và rule-based của nhánh maianh)
- Thước đo: 720 mẫu mỗi episode (mỗi 5 s, t = 0 đến 3595 s), `mean_queue` và `max_queue` (xe), `mean_total_waiting_time` và `max_total_waiting_time` (tổng thời gian chờ các làn vào, giây)
- Tổng hợp: trung bình ± độ lệch chuẩn mẫu (chia n−1) trên 3 seed test
- Phiên bản SUMO: mọi kết quả đánh giá trong file này chạy bằng SUMO 1.28.0 (cùng phiên bản với fixed-time và rule-based của nhánh maianh). Các mô hình DQN được train bằng SUMO 1.27.1 và không train lại.
- Cấu trúc: code dùng chung ở `DRL/` (gốc repo); `logs/` và `results/` của map này nằm trong `Map_Nga_Tu/`. Mọi lệnh chạy từ thư mục `Map_Nga_Tu/` và gọi code qua `../DRL/`. Các đường dẫn `logs/...`, `results/...` bên dưới đều tính từ `Map_Nga_Tu/`.
- File gốc: `results/drl/<tên mô hình>_eval.jsonl` và `_summary.json`; mô hình và log train nằm trong `logs/`. `logs/` và `results/drl/` chứa toàn bộ v1 (seed 0–4), v2a và v2b. Kết quả chính sách hằng (always SWITCH / always KEEP) nằm ở `results/constant/`. Tỉ lệ đặc trưng bị cắt và tỉ lệ yêu cầu/đổi pha thật nằm trong chính `_eval.jsonl` và `_summary.json` của mỗi lần đánh giá. Các lần chạy thử 20.000 bước ban đầu (v0) đã được xóa khỏi thư mục dự án; số liệu của chúng không dùng trong file này.

## Lịch sử thay đổi mô hình

Mỗi lần đổi code hoặc tham số, ghi vào đây một phiên bản mới (gồm thay đổi, lý do, ngày) và ghi rõ các bảng kết quả bên dưới thuộc phiên bản nào. Phần đánh giá (`evaluate.py`, thước đo, seed test 57, 367, 1024) giữ nguyên giữa các phiên bản.

### v0: bản 20.000 bước (đã chạy, chỉ để tham khảo)
- 20.000 bước, `buffer_size` 50.000; seed test 100 đến 104; thời gian chờ đo trung bình mỗi xe. Không dùng cho so sánh cuối.

### v1: bản đã chạy xong (kết quả ở Phần 1)
- Code: `DRL/traffic_gym.py`, `DRL/train_dqn.py`, `DRL/evaluate.py` (nhánh `ngananhhng`, sửa ngày 15/11/2026)
- Seed DRL 0; seed giao thông khi train 0 đến 9 (không dùng 57, 367, 1024); seed test 57, 367, 1024
- Số bước 100.000, `buffer_size` 100.000, `learning_rate` 1e-3, `batch_size` 64, `gamma` 0,99, `learning_starts` 1.000, `target_update_interval` 500, `exploration_fraction` 0,3, `exploration_final_eps` 0,05; mạng `MlpPolicy` 2 lớp ẩn 64 nơ-ron
- Reward: r = −(1,0 × queue / (2 × 20) + 0,5 × thời gian chờ trung bình mỗi xe / 60), tính mỗi bước 5 giây
- Mô hình lưu: bản ở cuối huấn luyện (không chọn bản tốt nhất)

### v2: đã chẩn đoán High, chuẩn bị train (kết quả và kế hoạch ở Phần 2)
- Code: `DRL/traffic_gym.py`, `DRL/train_dqn.py`, `DRL/evaluate.py` (bản v2)
- Động cơ: DQN v1 không hơn rule-based ở High nhưng hơn ở Imbalance. Ở High, hai mô hình (seed DRL 0 và 1) cho số liệu giống hệt nhau trên cả 3 seed test, nghi ngờ đặc trưng trạng thái bị cắt về 1 (giả thuyết, cần kiểm chứng bằng bước chẩn đoán bên dưới).

| Thay đổi | Trước (v1) | Sau (v2) | Lý do | Trạng thái |
|---|---|---|---|---|
| Reward | −(1,0 × queue / 40 + 0,5 × thời gian chờ trung bình mỗi xe / 60) | −(queue / 40 + tổng thời gian chờ / 1000), cùng nguồn `total_queue` và `total_wait` với `evaluate.py` (cờ `--reward total_wait`; `--reward avg_wait` quay về v1) | reward khớp thước đo đánh giá | đã sửa code, chưa chạy |
| Lưu mô hình | chỉ bản cuối | thêm `logs/<tên>_best_model.zip`: cứ 10.000 bước chạy mô hình trên seed 100, 101, 102 (không phải 57, 367, 1024) và giữ bản có return cao nhất; ghi đường cong vào `logs/<tên>_val.csv` (cờ `--eval-freq`, `--val-seeds`; `--eval-freq 0` tắt) | return đạt đỉnh rồi dao động; chọn bản tốt nhất không dùng seed test | đã sửa code, chưa chạy |
| Hằng số chuẩn hóa quan sát | `Q_SCALE` 20 (queue mỗi nhóm), `V_SCALE` 30 (số xe mỗi nhóm), `W_SCALE` 60 (thời gian chờ mỗi xe) | giữ mặc định, thêm cờ `--q-scale`, `--v-scale`, `--w-scale` để tăng cho lưu lượng nặng; `evaluate.py` tự đọc các giá trị này từ `_config.json` | giá trị v1 hợp với Low, có thể quá nhỏ cho High | đã sửa code, đã chọn `--q-scale 60 --v-scale 90 --w-scale 30` cho High (làm tròn từ gợi ý 56–57, 81–84, 19; w lấy 30 để dư chỗ), chưa train |
| Chẩn đoán đặc trưng bị cắt | không có | `evaluate.py` in tỉ lệ bước mà mỗi đặc trưng bị cắt về 1 và gợi ý hằng số chuẩn hóa (phân vị 95), lưu vào `_summary.json` | kiểm chứng giả thuyết trên | đã chạy trên High v1 (kết quả ở bảng chẩn đoán dưới) |
| Cờ `--tag` (`train_dqn.py`) | tên đầu ra cố định `dqn_<kịch bản>_seed<N>` | thêm hậu tố, ví dụ `--tag v2a` cho `dqn_high_seed0_v2a_*`; `evaluate.py` đọc đúng `_config.json` theo tên có tag | các lần chạy v2 không ghi đè nhau và không đè v1 | đã sửa code |
| Siêu tham số | `learning_rate` 1e-3, `target_update_interval` 500, `exploration_final_eps` 0,05 | mặc định giữ nguyên; đổi được bằng `--learning-rate`, `--target-update-interval`, `--eps-final` | giảm dao động khi học, chưa quyết định giá trị | chưa chạy thử |

---

## PHẦN 1. KẾT QUẢ V1 (reward cũ, hằng số chuẩn hóa mặc định, lưu mô hình ở cuối huấn luyện)

Gồm: (1.1) seed DRL 0, (1.2) seed DRL 1, (1.3) tổng hợp 2 seed so với rule-based, (1.4) seed DRL 2, (1.5) tổng hợp 3 seed, (1.6) Imbalance với 5 seed (kết quả cuối của v1). Mọi số liệu đánh giá dùng SUMO 1.28.0.

### 1.1 v1, seed DRL 0

#### Tổng hợp 4 kịch bản (v1: DQN 100.000 bước, seed DRL 0)

DQN giảm bao nhiêu so với rule-based (số dương: DQN tốt hơn):

| Kịch bản | mean_queue | max_queue | mean_total_waiting_time | max_total_waiting_time |
|---|---|---|---|---|
| Low | 7,9% | −10,3% | 8,6% | 1,0% |
| Medium | −1,9% | −3,6% | −3,6% | 5,9% |
| High | 2,2% | −3,2% | 1,9% | −6,5% |
| Imbalance | 9,3% | 10,3% | 12,4% | 23,9% |

- DQN tốt hơn fixed-time ở mọi kịch bản trên các thước đo trung bình.
- So với rule-based: DQN rõ ràng tốt hơn ở Imbalance, ngang ở Low, Medium và High (ở High, mô hình này trùng hoàn toàn với chính sách luôn SWITCH, xem mục 2.3 và 2.4).
- Mới có một lần train mỗi kịch bản (seed DRL 0) và 3 seed test.

#### Low

##### DQN 100.000 bước, từng seed

| Seed | mean_queue | max_queue | mean_total_waiting_time | max_total_waiting_time |
|---|---|---|---|---|
| 57 | 3,31 | 13,00 | 47,02 | 263,80 |
| 367 | 3,16 | 14,00 | 44,10 | 243,90 |
| 1024 | 3,53 | 16,00 | 50,03 | 328,00 |
| **Trung bình ± SD** | **3,33 ± 0,19** | **14,33 ± 1,53** | **47,05 ± 2,96** | **278,57 ± 43,95** |

##### So với fixed-time và rule-based (nhánh maianh)

| Metric | Fixed-time | Rule-based | DQN 100k | DQN giảm so với fixed-time | DQN giảm so với rule-based |
|---|---|---|---|---|---|
| mean_queue (xe) | 4,96 ± 0,04 | 3,62 ± 0,11 | 3,33 ± 0,19 | 32,8% | 7,9% |
| max_queue (xe) | 18,00 ± 1,00 | 13,00 ± 1,00 | 14,33 ± 1,53 | 20,4% | −10,3% (kém hơn) |
| mean_total_waiting_time (s) | 97,88 ± 1,07 | 51,50 ± 1,62 | 47,05 ± 2,96 | 51,9% | 8,6% |
| max_total_waiting_time (s) | 567,63 ± 24,16 | 281,50 ± 49,75 | 278,57 ± 43,95 | 50,9% | 1,0% |

##### Nhận xét
- Đường cong huấn luyện: return tăng từ khoảng −100 lên đỉnh khoảng −83 ở episode 45 (khoảng 32.000 bước), sau đó dao động trong khoảng −85 đến −95, chưa hội tụ ổn định. Mô hình lưu là bản cuối, không phải bản tốt nhất.
- DQN tốt hơn fixed-time rõ ràng ở cả bốn thước đo (giảm 20,4% đến 51,9%).
- So với rule-based: DQN nhỉnh hơn ở hai thước đo trung bình (7,9% và 8,6%) nhưng kém hơn ở `max_queue` (−10,3%), và độ lệch chuẩn lớn hơn. Chênh lệch nằm trong độ nhiễu của 3 seed, nên chưa kết luận DQN hơn rule-based.
- Chỉ có một lần train (seed DRL 0) và 3 seed test.

#### Medium

##### DQN 100.000 bước, từng seed

| Seed | mean_queue | max_queue | mean_total_waiting_time | max_total_waiting_time |
|---|---|---|---|---|
| 57 | 9,76 | 28,00 | 137,21 | 562,30 |
| 367 | 9,51 | 32,00 | 134,61 | 559,40 |
| 1024 | 9,71 | 27,00 | 135,69 | 533,10 |
| **Trung bình ± SD** | **9,66 ± 0,13** | **29,00 ± 2,65** | **135,84 ± 1,31** | **551,60 ± 16,09** |

##### So với fixed-time và rule-based (nhánh maianh)

| Metric | Fixed-time | Rule-based | DQN 100k | DQN giảm so với fixed-time | DQN giảm so với rule-based |
|---|---|---|---|---|---|
| mean_queue (xe) | 12,93 ± 0,39 | 9,48 ± 0,18 | 9,66 ± 0,13 | 25,3% | −1,9% (kém hơn) |
| max_queue (xe) | 35,67 ± 2,89 | 28,00 ± 1,00 | 29,00 ± 2,65 | 18,7% | −3,6% (kém hơn) |
| mean_total_waiting_time (s) | 238,83 ± 8,04 | 131,17 ± 2,95 | 135,84 ± 1,31 | 43,1% | −3,6% (kém hơn) |
| max_total_waiting_time (s) | 1037,87 ± 74,52 | 586,27 ± 63,43 | 551,60 ± 16,09 | 46,9% | 5,9% |

##### Nhận xét
- Đường cong huấn luyện: return tăng từ khoảng −220 lên đỉnh khoảng −191 ở episode 57 (khoảng 41.000 bước), sau đó giảm nhẹ và dao động quanh −195 đến −205. Mô hình lưu là bản cuối, kém hơn bản ở đỉnh.
- So với fixed-time: DQN tốt hơn rõ ở cả bốn thước đo (giảm 18,7% đến 46,9%).
- So với rule-based: DQN kém hơn nhẹ ở ba thước đo (1,9% đến 3,6%) và nhỉnh hơn ở `max_total_waiting_time` (5,9%). Chênh lệch nhỏ và nằm trong độ nhiễu của 3 seed, nên coi là ngang nhau, không phải DQN vượt rule-based.
- Chỉ có một lần train (seed DRL 0) và 3 seed test.

#### High

##### DQN 100.000 bước, từng seed

| Seed | mean_queue | max_queue | mean_total_waiting_time | max_total_waiting_time |
|---|---|---|---|---|
| 57 | 37,63 | 98,00 | 613,93 | 2581,80 |
| 367 | 42,38 | 104,00 | 717,46 | 2920,70 |
| 1024 | 43,46 | 85,00 | 711,63 | 2390,80 |
| **Trung bình ± SD** | **41,16 ± 3,10** | **95,67 ± 9,71** | **681,01 ± 58,16** | **2631,10 ± 268,37** |

##### So với fixed-time và rule-based (nhánh maianh)

| Metric | Fixed-time | Rule-based | DQN 100k | DQN giảm so với fixed-time | DQN giảm so với rule-based |
|---|---|---|---|---|---|
| mean_queue (xe) | 45,58 ± 2,86 | 42,07 ± 3,47 | 41,16 ± 3,10 | 9,7% | 2,2% |
| max_queue (xe) | 93,33 ± 3,21 | 92,67 ± 2,08 | 95,67 ± 9,71 | −2,5% (kém hơn) | −3,2% (kém hơn) |
| mean_total_waiting_time (s) | 939,12 ± 75,53 | 693,94 ± 51,83 | 681,01 ± 58,16 | 27,5% | 1,9% |
| max_total_waiting_time (s) | 3160,43 ± 357,15 | 2471,07 ± 219,77 | 2631,10 ± 268,37 | 16,7% | −6,5% (kém hơn) |

##### Nhận xét
- Đường cong huấn luyện: return rất nhiễu (từ khoảng −560 đến −1100), trung bình trượt tăng từ khoảng −880 lên khoảng −780 trong 20 episode đầu, sau đó dao động quanh −750 đến −800 mà không tăng thêm. Chưa thấy hội tụ rõ.
- Kết quả của mô hình này **trùng từng chữ số** với chính sách cố định luôn SWITCH trên cả 3 seed test (mục 2.4), nên không có bằng chứng DQN dùng trạng thái giao thông ở High.
- So với fixed-time: tốt hơn ở ba thước đo (queue 9,7%, thời gian chờ trung bình 27,5%, `max_total_waiting_time` 16,7%), kém hơn nhẹ ở `max_queue` (−2,5%).
- So với rule-based: queue 2,2%, thời gian chờ trung bình 1,9% (nhỉnh hơn), `max_queue` −3,2%, `max_total_waiting_time` −6,5% (kém hơn). Độ lệch chuẩn giữa các seed test lớn (queue từ 37,63 đến 43,46), nên chênh lệch nằm trong độ nhiễu.
- Chỉ có một lần train (seed DRL 0) và 3 seed test.

#### Imbalance

##### DQN 100.000 bước, từng seed

| Seed | mean_queue | max_queue | mean_total_waiting_time | max_total_waiting_time |
|---|---|---|---|---|
| 57 | 35,11 | 124,00 | 612,90 | 3834,60 |
| 367 | 36,26 | 94,00 | 637,46 | 3624,50 |
| 1024 | 33,54 | 104,00 | 569,34 | 3682,10 |
| **Trung bình ± SD** | **34,97 ± 1,37** | **107,33 ± 15,28** | **606,56 ± 34,50** | **3713,73 ± 108,56** |

##### So với fixed-time và rule-based (nhánh maianh)

| Metric | Fixed-time | Rule-based | DQN 100k | DQN giảm so với fixed-time | DQN giảm so với rule-based |
|---|---|---|---|---|---|
| mean_queue (xe) | 82,78 ± 6,97 | 38,56 ± 4,49 | 34,97 ± 1,37 | 57,8% | 9,3% |
| max_queue (xe) | 259,67 ± 34,12 | 119,67 ± 3,79 | 107,33 ± 15,28 | 58,7% | 10,3% |
| mean_total_waiting_time (s) | 1850,26 ± 111,75 | 692,27 ± 126,49 | 606,56 ± 34,50 | 67,2% | 12,4% |
| max_total_waiting_time (s) | 10014,07 ± 387,89 | 4879,00 ± 1033,06 | 3713,73 ± 108,56 | 62,9% | 23,9% |

##### Nhận xét
- Đường cong huấn luyện: return tăng rõ rệt. Từ khoảng −1450 xuống đáy khoảng −2000 quanh episode 22 (giai đoạn không ổn định), rồi tăng nhanh lên khoảng −600 ở episode 45 (khoảng 32.000 bước) và đi ngang quanh −600 đến −750 đến hết 138 episode. Đây là kịch bản hội tụ rõ nhất trong bốn kịch bản.
- So với fixed-time: DQN giảm 57,8% đến 67,2% ở cả bốn thước đo.
- So với rule-based: DQN tốt hơn ở cả bốn thước đo (9,3% đến 23,9%). Chênh lệch ở `mean_queue` (3,59 xe) và `mean_total_waiting_time` (85,7 s) lớn hơn độ lệch chuẩn của DQN nhưng nhỏ hơn độ lệch chuẩn của rule-based; với 3 seed test và một seed DRL nên chỉ coi là xu hướng.
- Chỉ có một lần train (seed DRL 0) và 3 seed test, nên cần thêm seed DRL 1, 2 để xác nhận.

### 1.2 v1, seed DRL 1

Cùng cấu hình v1, chỉ đổi `--seed 1`.

Các seed DRL khác nhau cho biết mức dao động do huấn luyện. Mỗi bảng dưới đây là một lần train, đánh giá trên seed test 57, 367, 1024.

#### Low, seed DRL 1

Đường cong huấn luyện: return tăng từ khoảng −102 lên khoảng −90 trong 15 episode đầu, rồi tăng chậm lên khoảng −87 đến −88, ít dao động hơn seed 0, không có đỉnh rồi giảm rõ rệt.

| Seed test | mean_queue | max_queue | mean_total_waiting_time | max_total_waiting_time |
|---|---|---|---|---|
| 57 | 3,52 | 12,00 | 50,10 | 260,50 |
| 367 | 3,64 | 13,00 | 53,45 | 301,90 |
| 1024 | 3,72 | 14,00 | 52,80 | 280,60 |
| **Trung bình ± SD** | **3,63 ± 0,10** | **13,00 ± 1,00** | **52,12 ± 1,77** | **281,00 ± 20,70** |

#### Low, so sánh giữa các seed DRL

| Metric | Rule-based | DQN seed 0 | DQN seed 1 | Trung bình 2 seed DRL |
|---|---|---|---|---|
| mean_queue (xe) | 3,62 ± 0,11 | 3,33 ± 0,19 | 3,63 ± 0,10 | 3,48 |
| max_queue (xe) | 13,00 ± 1,00 | 14,33 ± 1,53 | 13,00 ± 1,00 | 13,67 |
| mean_total_waiting_time (s) | 51,50 ± 1,62 | 47,05 ± 2,96 | 52,12 ± 1,77 | 49,58 |
| max_total_waiting_time (s) | 281,50 ± 49,75 | 278,57 ± 43,95 | 281,00 ± 20,70 | 279,78 |

Nhận xét (Low):
- Seed 1 kém hơn seed 0 ở `mean_queue` (3,63 so với 3,33) và `mean_total_waiting_time` (52,12 so với 47,05). Seed 1 ngang rule-based, còn seed 0 nhỉnh hơn rule-based khoảng 7,9%. Chênh lệch giữa hai seed DRL xấp xỉ chênh lệch giữa DQN và rule-based, nên kết luận ở Low vẫn là DQN ngang rule-based.
- Trung bình 2 seed DRL: `mean_queue` thấp hơn rule-based khoảng 3,8%, thời gian chờ trung bình thấp hơn khoảng 3,7%, `max_queue` cao hơn khoảng 5,1%. Đây là chênh lệch nhỏ.

#### Medium, seed DRL 1

Đường cong huấn luyện: return tăng từ khoảng −228 lên khoảng −200 trong 25 episode đầu, rồi tiếp tục tăng chậm đến khoảng −196 ở cuối, không giảm lại như seed 0 (seed 0 đạt đỉnh ở episode 57 rồi giảm nhẹ).

| Seed test | mean_queue | max_queue | mean_total_waiting_time | max_total_waiting_time |
|---|---|---|---|---|
| 57 | 9,32 | 27,00 | 128,65 | 521,80 |
| 367 | 9,39 | 29,00 | 131,22 | 622,50 |
| 1024 | 9,81 | 29,00 | 136,93 | 679,40 |
| **Trung bình ± SD** | **9,51 ± 0,26** | **28,33 ± 1,15** | **132,27 ± 4,24** | **607,90 ± 79,81** |

#### Medium, so sánh giữa các seed DRL

| Metric | Rule-based | DQN seed 0 | DQN seed 1 | Trung bình 2 seed DRL |
|---|---|---|---|---|
| mean_queue (xe) | 9,48 ± 0,18 | 9,66 ± 0,13 | 9,51 ± 0,26 | 9,59 |
| max_queue (xe) | 28,00 ± 1,00 | 29,00 ± 2,65 | 28,33 ± 1,15 | 28,67 |
| mean_total_waiting_time (s) | 131,17 ± 2,95 | 135,84 ± 1,31 | 132,27 ± 4,24 | 134,05 |
| max_total_waiting_time (s) | 586,27 ± 63,43 | 551,60 ± 16,09 | 607,90 ± 79,81 | 579,75 |

Nhận xét (Medium):
- Hai seed DRL cho kết quả gần nhau ở `mean_queue` (9,66 và 9,51) và thời gian chờ trung bình (135,84 và 132,27), nên kết quả ở Medium khá ổn định theo seed.
- Trung bình 2 seed DRL kém rule-based nhẹ ở ba thước đo (queue 1,1%, `max_queue` 2,4%, thời gian chờ 2,2%) và nhỉnh hơn 1,1% ở `max_total_waiting_time`. Chênh lệch nhỏ, nằm trong độ lệch chuẩn, nên kết luận ở Medium là DQN ngang rule-based, hơi kém một chút.

#### High, seed DRL 1

Đường cong huấn luyện: return tăng từ khoảng −980 lên khoảng −780 trong 20 episode đầu, đạt đỉnh trung bình trượt khoảng −690 ở episode 42, sau đó dao động quanh −720 đến −800 (có một episode tụt xuống khoảng −1080 ở episode 114). Chưa hội tụ rõ, giống seed 0.

| Seed test | mean_queue | max_queue | mean_total_waiting_time | max_total_waiting_time |
|---|---|---|---|---|
| 57 | 37,63 | 98,00 | 613,93 | 2581,80 |
| 367 | 42,38 | 104,00 | 717,46 | 2920,70 |
| 1024 | 43,46 | 85,00 | 711,63 | 2390,80 |
| **Trung bình ± SD** | **41,16 ± 3,10** | **95,67 ± 9,71** | **681,01 ± 58,16** | **2631,10 ± 268,37** |

#### High, so sánh giữa các seed DRL

| Metric | Rule-based | DQN seed 0 | DQN seed 1 | Trung bình 2 seed DRL |
|---|---|---|---|---|
| mean_queue (xe) | 42,07 ± 3,47 | 41,16 ± 3,10 | 41,16 ± 3,10 | 41,16 |
| max_queue (xe) | 92,67 ± 2,08 | 95,67 ± 9,71 | 95,67 ± 9,71 | 95,67 |
| mean_total_waiting_time (s) | 693,94 ± 51,83 | 681,01 ± 58,16 | 681,01 ± 58,16 | 681,01 |
| max_total_waiting_time (s) | 2471,07 ± 219,77 | 2631,10 ± 268,37 | 2631,10 ± 268,37 | 2631,10 |

Nhận xét (High):
- Hai seed DRL cho kết quả **trùng từng chữ số** trên cả 3 seed test, và trùng với chính sách luôn SWITCH (mục 2.4). Trung bình 2 seed DRL so với rule-based: queue 2,2%, `max_queue` −3,2%, thời gian chờ trung bình 1,9%, `max_total_waiting_time` −6,5%.
- Hai mạng huấn luyện độc lập cho cùng quỹ đạo vì bản cuối của cả hai học thành chính sách "đổi pha ngay khi được phép" (mục 2.3). Giả thuyết giải thích (chưa kiểm chứng riêng): ở High, với hằng số v1, queue và số xe bị cắt về 1 ở phần lớn số bước (mục 2.1), nên quan sát gần như không mang thông tin về mức tắc nghẽn.

#### Imbalance, seed DRL 1

Đường cong huấn luyện: giống seed 0. Return tăng từ khoảng −1600, đáy khoảng −1700 quanh episode 25, rồi tăng nhanh lên khoảng −600 ở episode 40 (khoảng 29.000 bước) và đi ngang quanh −600 đến −750, có một đoạn tụt nhẹ quanh episode 120. Hội tụ rõ.

| Seed test | mean_queue | max_queue | mean_total_waiting_time | max_total_waiting_time |
|---|---|---|---|---|
| 57 | 32,47 | 110,00 | 563,89 | 3887,50 |
| 367 | 38,80 | 105,00 | 704,25 | 4115,60 |
| 1024 | 31,79 | 103,00 | 558,29 | 3687,30 |
| **Trung bình ± SD** | **34,35 ± 3,87** | **106,00 ± 3,61** | **608,81 ± 82,70** | **3896,80 ± 214,30** |

#### Imbalance, so sánh giữa các seed DRL

| Metric | Rule-based | DQN seed 0 | DQN seed 1 | Trung bình 2 seed DRL |
|---|---|---|---|---|
| mean_queue (xe) | 38,56 ± 4,49 | 34,97 ± 1,37 | 34,35 ± 3,87 | 34,66 |
| max_queue (xe) | 119,67 ± 3,79 | 107,33 ± 15,28 | 106,00 ± 3,61 | 106,67 |
| mean_total_waiting_time (s) | 692,27 ± 126,49 | 606,56 ± 34,50 | 608,81 ± 82,70 | 607,69 |
| max_total_waiting_time (s) | 4879,00 ± 1033,06 | 3713,73 ± 108,56 | 3896,80 ± 214,30 | 3805,27 |

Nhận xét (Imbalance):
- Hai seed DRL cho kết quả gần nhau ở mọi thước đo (queue 34,97 và 34,35; thời gian chờ 606,56 và 608,81), nên kết quả ở Imbalance ổn định theo seed.
- Trung bình 2 seed DRL tốt hơn rule-based ở cả bốn thước đo: queue 10,1%, `max_queue` 10,9%, thời gian chờ trung bình 12,2%, `max_total_waiting_time` 22,0%. Imbalance là kịch bản duy nhất DQN v1 hơn rule-based.

### 1.3 v1, tổng hợp 2 seed DRL (0 và 1) so với rule-based

DQN giảm bao nhiêu so với rule-based (số dương: DQN tốt hơn). Cả bốn kịch bản đều có đủ 2 seed DRL.

| Kịch bản | mean_queue | max_queue | mean_total_waiting_time | max_total_waiting_time |
|---|---|---|---|---|
| Low | 3,8% | −5,1% | 3,7% | 0,6% |
| Medium | −1,1% | −2,4% | −2,2% | 1,1% |
| High | 2,2% | −3,2% | 1,9% | −6,5% |
| Imbalance | 10,1% | 10,9% | 12,2% | 22,0% |

- Imbalance: DQN hơn rule-based khoảng 10–22% và ổn định giữa hai seed. Low và Medium: ngang. High: ngang (hai seed trùng chính sách luôn SWITCH).
- Mới có 2 seed DRL và 3 seed test, nên chưa có độ tin cậy thống kê cao.
- Lưu ý: ở Low, Medium và High, kết quả DQN gần như trùng chính sách cố định "luôn SWITCH" (xem mục 2.4); chỉ ở Imbalance DQN thực sự vượt cả mốc này.

### 1.4 v1, seed DRL 2 (code v2 với `--reward avg_wait --eval-freq 0`, scale mặc định, `--tag v1`; bản cuối `_model`; 3 seed test)

| Kịch bản | mean_queue | max_queue | mean_total_waiting_time | max_total_waiting_time | đổi pha thật (seed 1024) |
|---|---|---|---|---|---|
| Low | 3,59 ± 0,07 | 14,00 ± 2,00 | 51,99 ± 2,20 | 270,17 ± 26,29 | 12,1% |
| Medium | 9,58 ± 0,29 | 28,00 ± 2,00 | 135,08 ± 4,01 | 545,70 ± 29,73 | 12,2% |
| High | 39,66 ± 3,57 | 87,00 ± 4,36 | 640,21 ± 66,44 | 2238,73 ± 162,62 | 12,5% |
| Imbalance | 38,08 ± 8,32 | 118,33 ± 18,01 | 706,74 ± 184,10 | 4132,47 ± 1198,80 | 8,8% |

- Đặc trưng bị cắt (scale mặc định): High queue 38,7%–44,6%, số xe 83,2%–87,5%; Imbalance queue NS 63,3%, số xe NS 96,4%; Low gần như không bị cắt, Medium bị cắt dưới 4% số bước.
- High: số liệu ở seed test 1024 trùng chính sách luôn SWITCH (43,46 / 85,00 / 711,63 / 2390,80), nhưng ở seed test 57 và 367 khác (mean_queue 36,38 và 39,14 so với 37,63 và 42,38), nên mean_queue trung bình 39,66 khác mốc (41,16). Ở hai seed test đó seed DRL 2 có hành vi khác mốc, khác seed DRL 0 và 1 (hai seed này trùng mốc hoàn toàn).
- Imbalance: seed DRL 2 kém hơn hẳn seed 0 và 1 (38,08 so với 34,97 và 34,35) và gần rule-based; độ lệch chuẩn giữa các seed test lớn (queue từ 28,66 đến 44,40), nên kết quả ở Imbalance không ổn định giữa các seed DRL như nhận xét trước (khi mới có 2 seed).
- Seed 2 chưa có đường cong huấn luyện trong file này.

### 1.5 v1, tổng hợp 3 seed DRL (0, 1, 2): trung bình ± độ lệch chuẩn giữa các seed DRL

Mỗi seed DRL được lấy trung bình trên 3 seed test trước; độ lệch chuẩn mẫu (n−1) tính giữa 3 giá trị đó.

| Kịch bản | mean_queue | max_queue | mean_total_waiting_time | max_total_waiting_time |
|---|---|---|---|---|
| Low | 3,52 ± 0,16 | 13,78 ± 0,69 | 50,38 ± 2,89 | 276,58 ± 5,68 |
| Medium | 9,58 ± 0,08 | 28,44 ± 0,51 | 134,39 ± 1,88 | 568,40 ± 34,33 |
| High | 40,66 ± 0,86 | 92,78 ± 5,00 | 667,41 ± 23,55 | 2500,31 ± 226,53 |
| Imbalance | 35,80 ± 2,00 | 110,56 ± 6,77 | 640,70 ± 57,20 | 3914,33 ± 209,92 |

DQN so với rule-based (số dương: DQN tốt hơn), trung bình 3 seed DRL:

| Kịch bản | mean_queue | max_queue | mean_total_waiting_time | max_total_waiting_time |
|---|---|---|---|---|
| Low | 2,8% | −6,0% | 2,2% | 1,7% |
| Medium | −1,1% | −1,6% | −2,5% | 3,0% |
| High | 3,4% | −0,1% | 3,8% | −1,2% |
| Imbalance | 7,2% | 7,6% | 7,4% | 19,8% |

DQN so với chính sách luôn SWITCH (mục 2.4), trung bình 3 seed DRL:

| Kịch bản | mean_queue | max_queue | mean_total_waiting_time | max_total_waiting_time |
|---|---|---|---|---|
| Low | 2,7% | −3,3% | 2,3% | 3,0% |
| Medium | −1,1% | −1,6% | −2,5% | 3,0% |
| High | 1,2% | 3,0% | 2,0% | 5,0% |
| Imbalance | 53,6% | 53,7% | 50,8% | 44,4% |

Kết luận v1 (3 seed DRL, 3 seed test):
- Low, Medium, High: DQN ngang rule-based và ngang chính sách luôn SWITCH (khác biệt vài phần trăm, nhỏ hơn độ lệch chuẩn). Không có bằng chứng DQN tốt hơn.
- Imbalance: DQN hơn rule-based khoảng 7,2%–19,8% và hơn chính sách luôn SWITCH khoảng 44,4%–53,7%. Độ lệch chuẩn giữa các seed DRL khá lớn (queue 2,00; thời gian chờ 57,20), nên mức hơn rule-based có độ tin cậy vừa phải, chưa chắc chắn.

### 1.6 v1, Imbalance với 5 seed DRL (0 đến 4)

Seed 3 và 4 chạy bằng code v2 với `--reward avg_wait --eval-freq 0 --tag v1` (cấu hình tương đương v1), bản cuối `_model`, 3 seed test 57, 367, 1024.

| Seed DRL | mean_queue | max_queue | mean_total_waiting_time | max_total_waiting_time | yêu cầu SWITCH / đổi pha thật (seed 1024) |
|---|---|---|---|---|---|
| 0 | 34,97 ± 1,37 | 107,33 ± 15,28 | 606,56 ± 34,50 | 3713,73 ± 108,56 | 61,1% / 8,6% |
| 1 | 34,35 ± 3,87 | 106,00 ± 3,61 | 608,81 ± 82,70 | 3896,80 ± 214,30 | 41,1% / 8,6% |
| 2 | 38,08 ± 8,32 | 118,33 ± 18,01 | 706,74 ± 184,10 | 4132,47 ± 1198,80 | 40,1% / 8,8% |
| 3 | 34,17 ± 7,84 | 107,67 ± 21,96 | 604,16 ± 154,19 | 3069,40 ± 294,27 | 53,5% / 8,3% |
| 4 | 35,21 ± 4,25 | 111,33 ± 5,03 | 637,33 ± 117,17 | 3801,93 ± 923,20 | 6,7% / 8,2% |
| Trung bình ± SD giữa 5 seed DRL | 35,36 ± 1,58 | 110,13 ± 4,99 | 632,72 ± 43,51 | 3722,87 ± 397,30 |  |
| Rule-based (nhánh maianh) | 38,56 ± 4,49 | 119,67 ± 3,79 | 692,27 ± 126,49 | 4879,00 ± 1033,06 |  |
| Luôn SWITCH | 77,13 ± 6,82 | 239,00 ± 21,66 | 1302,12 ± 101,60 | 7040,53 ± 298,17 | 100% / 12,5% |
| Luôn KEEP | 93,44 ± 11,93 | 257,00 ± 26,89 | 2912,17 ± 444,88 | 14723,93 ± 2789,57 | 0% / 6,1% |

- DQN (trung bình 5 seed DRL) hơn rule-based: mean_queue 8,3%, max_queue 8,0%, mean_total_waiting_time 8,6%, max_total_waiting_time 23,7%; hơn chính sách luôn SWITCH: 54,2%, 53,9%, 51,4%, 47,1%.
- Từng seed DRL đều có mean_queue thấp hơn rule-based (hơn từ 1,2% đến 11,4% tùy seed); seed 2 chỉ hơn khoảng 1,2% (nằm trong độ lệch chuẩn), các seed còn lại hơn khoảng 8,7%–11,4%.
- Mọi seed có tỉ lệ đổi pha thật 8,2–8,8%, thấp hơn 12,5% của chính sách luôn SWITCH.
- Seed 4 chỉ yêu cầu SWITCH 6,7% số quyết định nhưng đèn đổi pha thật ở 8,2%. Để kiểm tra có phải chính sách "luôn KEEP" (chỉ đổi pha khi bị ép ở xanh tối đa 75 s) hay không, đã chạy `--constant keep` (3 seed test): mean_queue 93,44 ± 11,93, max_queue 257,00 ± 26,89, mean_total_waiting_time 2912,17 ± 444,88, max_total_waiting_time 14723,93 ± 2789,57, đổi pha thật 6,1%. Mốc này kém xa seed 4 (35,21; 637,33), nên seed 4 không phải "luôn KEEP": nó đổi pha có chủ động theo trạng thái (đổi pha thật 8,2% so với 6,1%), chỉ là kém hơn các seed 0, 1, 3.
- Kết luận: ở Imbalance, DQN hơn rule-based khoảng 8,0%–23,7% trung bình 5 seed DRL, nhưng độ lớn khác nhau giữa các seed (1,2% đến 11,4%).

---

## PHẦN 2. KẾT QUẢ V2

### 2.1 Chẩn đoán và kế hoạch

Kế hoạch chạy v2:
1. Chẩn đoán trên các mô hình v1 đã có (không cần train lại): chạy `evaluate.py` v2 với mô hình v1 của High và Imbalance để xem tỉ lệ đặc trưng bị cắt và hằng số chuẩn hóa gợi ý. Kết quả chẩn đoán điền vào bảng dưới.
2. Nếu tỉ lệ bị cắt cao (ví dụ trên 30% số bước) ở High, train lại High (và Imbalance nếu cần) với `--q-scale`, `--v-scale`, `--w-scale` theo gợi ý.
3. Train v2 (reward mới, lưu mô hình tốt nhất) cho cả 4 kịch bản, rồi đánh giá bằng `evaluate.py` trên seed 57, 367, 1024 và ghi rõ dùng `_best_model` hay `_model`.

Kết quả chẩn đoán trên mô hình v1 (High và Imbalance; tỉ lệ bị cắt lấy từ lần đánh giá trên 3 seed test). Kết luận High: giả thuyết đúng. Với hằng số mặc định (20, 30, 60), khoảng 40–46% số bước queue bị cắt về 1 và khoảng 82–86% số bước số xe bị cắt về 1, nên mô hình không phân biệt được mức tắc nghẽn từ trung bình đến nặng. Thời gian chờ không bị cắt:

| Mô hình v1 | queue bị cắt (tỉ lệ bước) | số xe bị cắt | thời gian chờ bị cắt | hằng số gợi ý (q, v, w) |
|---|---|---|---|---|
| High seed 0 | 45,6% (NS), 40,0% (EW) | 86,3% (NS), 81,9% (EW) | 0% | 55, 80, 18 |
| High seed 1 | 45,6% (NS), 40,0% (EW) | 86,3% (NS), 81,9% (EW) | 0% | 55, 80, 18 |
| Imbalance seed 0 | NS 60,9%, EW 0,1% | NS 98,5% (EW không bị cắt) | không ghi nhận | 75, 113, 27 |
| Imbalance seed 1 | NS 58,9%, EW 0,0% | NS 97,5% (EW không bị cắt) | không ghi nhận | 73, 111, 27 |

Kế hoạch train v2 cho High (seed DRL 0), tách từng thay đổi để biết cải thiện đến từ đâu (kết quả ở mục 2.2):

| Cấu hình | Reward | Scale (q, v, w) | Tag | Lệnh |
|---|---|---|---|---|
| v2a | `avg_wait` (như v1) | 60, 90, 30 | `v2a` | `python ../DRL/train_dqn.py --scenario high --seed 0 --q-scale 60 --v-scale 90 --w-scale 30 --reward avg_wait --tag v2a` |
| v2b | `total_wait` (mới) | 60, 90, 30 | `v2b` | `python ../DRL/train_dqn.py --scenario high --seed 0 --q-scale 60 --v-scale 90 --w-scale 30 --reward total_wait --tag v2b` |

Đánh giá bằng mô hình tốt nhất: `python ../DRL/evaluate.py --scenario high --model logs/dqn_high_seed0_v2b_best_model` (v2a tương tự). So v2a với v1 cho thấy tác dụng của scale; so v2b với v2a cho thấy tác dụng của reward.

Nhận định Imbalance: hướng NS bị bão hòa nặng với hằng số v1 (queue NS bị cắt khoảng 57–63% số bước, số xe NS bị cắt khoảng 96–99%; hướng EW gần như không bị cắt), nên scale v1 cũng quá nhỏ cho Imbalance. DQN v1 vẫn hơn rule-based nên đây là cơ hội cải thiện thêm, không phải lỗi. Quyết định: thử Imbalance với scale mới sau khi có kết quả High (`--q-scale 70 --v-scale 110 --w-scale 30`); mỗi lần train khoảng 1 giờ. Low và Medium giữ kết quả v1 (chưa chẩn đoán).

Ghi chú:
- `TOTAL_WAIT_SCALE` = 1000 là giá trị chọn ban đầu, chưa thử nghiệm.
- Return của v2 dùng reward khác v1 nên không so trực tiếp được với đường cong v1.
- Thay đổi quan sát chỉ áp dụng khi truyền các cờ `--q-scale`... lúc train; mô hình v1 vẫn đánh giá đúng với `evaluate.py` v2 (dùng hằng số mặc định).

### 2.2 Kết quả train v2 (High, seed DRL 0, bản `_best_model`)

High, đánh giá trên seed test 57, 367, 1024 bằng `_best_model`. Số liệu fixed-time và rule-based lấy từ nhánh maianh.

| Mô hình | mean_queue | max_queue | mean_total_waiting_time | max_total_waiting_time |
|---|---|---|---|---|
| Fixed-time | 45,58 ± 2,86 | 93,33 ± 3,21 | 939,12 ± 75,53 | 3160,43 ± 357,15 |
| Rule-based | 42,07 ± 3,47 | 92,67 ± 2,08 | 693,94 ± 51,83 | 2471,07 ± 219,77 |
| Luôn SWITCH | 41,16 ± 3,10 | 95,67 ± 9,71 | 681,01 ± 58,16 | 2631,10 ± 268,37 |
| DQN v1, seed DRL 0 | 41,16 ± 3,10 | 95,67 ± 9,71 | 681,01 ± 58,16 | 2631,10 ± 268,37 |
| DQN v1, seed DRL 1 | 41,16 ± 3,10 | 95,67 ± 9,71 | 681,01 ± 58,16 | 2631,10 ± 268,37 |
| DQN v1, trung bình 2 seed DRL | 41,16 | 95,67 | 681,01 | 2631,10 |
| DQN v2a_best (chỉ đổi scale), seed DRL 0 | 41,52 ± 5,40 | 93,33 ± 4,51 | 712,94 ± 119,28 | 2602,20 ± 282,43 |
| DQN v2b_best (scale và reward mới), seed DRL 0 | 41,28 ± 2,85 | 92,67 ± 10,02 | 680,89 ± 58,30 | 2804,90 ± 370,05 |

Đặc trưng bị cắt về 1 sau khi đổi scale (60, 90, 30): v2a: queue NS 0,5%, queue EW 4,4%, số xe EW 2,4%, thời gian chờ EW 0%; v2b: queue NS 2,7%, queue EW 1,0%, số xe NS 1,3%, số xe EW 0,4%, thời gian chờ NS 0%. Ở v1 các đặc trưng này bị cắt 39–88% số bước.

Nhận xét v2 (High):
- Scale mới hết bão hòa quan sát, nhưng các chỉ số trung bình (`mean_queue`, `mean_total_waiting_time`) ngang v1 và ngang rule-based (khác biệt nhỏ hơn độ lệch chuẩn).
- Các chỉ số cực đại không cải thiện so với v1: `max_queue` 93,33 (v2a) và 92,67 (v2b) so với 92,78 của v1 (3 seed DRL); `max_total_waiting_time` 2602 (v2a) và 2805 (v2b) so với 2500 của v1.
- So với rule-based (số âm là DQN kém hơn): v2a: queue 1,3%, `max_queue` −0,7%, thời gian chờ −2,7%, `max_total_waiting_time` −5,3%; v2b: 1,9%, 0,0%, 1,9%, −13,5%. So với fixed-time, DQN v2 tốt hơn ở `mean_queue` (8,9% và 9,4%), thời gian chờ trung bình (24,1% và 27,5%) và `max_total_waiting_time` (17,7% và 11,2%); `max_queue` ngang.
- v2a và v2b khác nhau trong phạm vi độ lệch chuẩn, và mới có một seed DRL, nên chưa kết luận reward mới tốt hơn hay kém hơn.
- Chưa train seed DRL 1 cho v2. Bản cuối `_model` được đánh giá ở mục 2.3.

### 2.3 Phát hiện: bản cuối ở High suy biến thành chính sách "đổi pha ngay khi được phép"

Đánh giá bản cuối (`_model`) của v1 seed 0, v1 seed 1, v2a và v2b ở High cho cùng một kết quả, và kết quả đó trùng khớp từng chữ số với chính sách cố định luôn SWITCH (kể cả từng seed test, ví dụ seed 1024: 43,46 / 85,00 / 711,63 / 2390,80):

| Mô hình (High, bản cuối) | mean_queue | max_queue | mean_total_waiting_time | max_total_waiting_time |
|---|---|---|---|---|
| v1 seed 0 | 41,16 ± 3,10 | 95,67 ± 9,71 | 681,01 ± 58,16 | 2631,10 ± 268,37 |
| v1 seed 1 | 41,16 ± 3,10 | 95,67 ± 9,71 | 681,01 ± 58,16 | 2631,10 ± 268,37 |
| v2a_model | 41,16 ± 3,10 | 95,67 ± 9,71 | 681,01 ± 58,16 | 2631,10 ± 268,37 |
| v2b_model | 41,16 ± 3,10 | 95,67 ± 9,71 | 681,01 ± 58,16 | 2631,10 ± 268,37 |
| Luôn SWITCH (chính sách cố định) | 41,16 ± 3,10 | 95,67 ± 9,71 | 681,01 ± 58,16 | 2631,10 ± 268,37 |

Các mạng huấn luyện độc lập (khác seed, khác scale quan sát và khác reward) cho quỹ đạo giống hệt nhau, nên chính sách không phụ thuộc trạng thái. Kiểm tra bằng `DRL/check_policy.py` (20.000 quan sát ngẫu nhiên trong [0, 1]^11) cho v1 seed 1, v2a và v2b:

| Mô hình (High) | tỉ lệ chọn SWITCH trên quan sát ngẫu nhiên | Q(SWITCH) − Q(KEEP) trung bình |
|---|---|---|
| v1 seed 1 (cuối) | 99,1% | +1,319 |
| v2a (cuối) | 98,5% | +1,167 |
| v2b (cuối) | 89,8% | +1,756 |
| v2a_best | 66,9% | +0,115 |
| v2b_best | 80,6% | +2,053 |

(`check_policy.py` chưa chạy cho v1 seed 0.) Khi chạy thật (seed test 1024), v2b (cuối) yêu cầu SWITCH ở 91,9% số quyết định, v1 seed 0 chỉ yêu cầu 23,8%, nhưng đèn đều chỉ đổi pha thật ở 12,5% số quyết định, vì yêu cầu trước khi hết thời gian đèn xanh tối thiểu (30 s) bị bỏ qua; vì vậy hành vi thực tế trùng chính sách luôn SWITCH dù tỉ lệ yêu cầu khác nhau.

Chính sách cố định luôn SWITCH (`python ../DRL/evaluate.py --scenario high --constant switch`: luôn yêu cầu SWITCH; đèn chỉ đổi khi hết 30 s xanh tối thiểu, thực tế đổi ở 12,5% số quyết định) cho kết quả **trùng từng chữ số** với cả bốn mô hình trên.

Kết luận: ở High, DQN bản cuối (v1 seed 0 và 1, v2a, v2b) chỉ học được "đổi pha ngay khi được phép" (chu kỳ ngắn cố định), không dùng trạng thái giao thông. Hai bản `_best_model` ít cực đoan hơn (yêu cầu SWITCH 20,7% và 36,8% số quyết định ở seed test 1024; 66,9% và 80,6% quan sát ngẫu nhiên) nên có số liệu khác, nhưng khác biệt nhỏ và mới có một seed DRL. Hệ quả cho báo cáo: ở High không kết luận DQN học được điều khiển thích nghi; mốc "luôn SWITCH" cần có trong bảng so sánh.

### 2.4 Mốc "luôn SWITCH" ở cả 4 kịch bản (3 seed test 57, 367, 1024; mean ± SD)

Chính sách cố định: luôn yêu cầu SWITCH, đèn đổi pha ngay khi hết 30 s xanh tối thiểu (thực tế đổi pha ở 12,5% số quyết định). Chạy bằng `python ../DRL/evaluate.py --scenario <kịch bản> --constant switch`.

| Kịch bản | mean_queue | max_queue | mean_total_waiting_time | max_total_waiting_time |
|---|---|---|---|---|
| Low | 3,62 ± 0,10 | 13,33 ± 1,15 | 51,56 ± 1,64 | 285,20 ± 51,79 |
| Medium | 9,48 ± 0,18 | 28,00 ± 1,00 | 131,17 ± 2,95 | 586,27 ± 63,43 |
| High | 41,16 ± 3,10 | 95,67 ± 9,71 | 681,01 ± 58,16 | 2631,10 ± 268,37 |
| Imbalance | 77,13 ± 6,82 | 239,00 ± 21,66 | 1302,12 ± 101,60 | 7040,53 ± 298,17 |

So sánh với rule-based và DQN v1 (trung bình 2 seed DRL):
- Low: mốc luôn SWITCH gần như trùng rule-based (3,62 so với 3,62; 51,56 so với 51,50). DQN v1 ngang cả hai; seed 0 tốt hơn nhẹ ở thời gian chờ (47,05), seed 1 không (52,12).
- Medium: mốc luôn SWITCH **trùng rule-based đến từng chữ số** ở cả bốn thước đo (9,48; 28,00; 131,17; 586,27), nên trên 3 seed test rule-based ở Medium cho cùng kết quả với luôn đổi pha ngay khi được phép. DQN v1 (9,59; 134,05) ngang cả hai, kém nhẹ.
- High: DQN bản cuối trùng hoàn toàn với mốc luôn SWITCH; rule-based nhỉnh hơn nhẹ ở `mean_queue` (42,07 so với 41,16) và thời gian chờ (693,94 so với 681,01) nhưng nằm trong độ lệch chuẩn (xem 2.3).
- Imbalance: mốc luôn SWITCH (77,13; 1302,12) tốt hơn fixed-time (82,78; 1850,26) nhưng kém xa rule-based (38,56; 692,27). DQN v1 (34,66; 607,69) giảm khoảng 55,1% queue, 53,3% thời gian chờ và 46,0% `max_total_waiting_time` so với mốc này, nên ở Imbalance DQN thực sự học được chính sách phụ thuộc trạng thái (cấp xanh theo hướng đông xe). Đây là kết quả có ý nghĩa của DRL trong nghiên cứu này.

Hệ quả cho báo cáo: ở Low, Medium và High, rule-based và DQN không khác chính sách chu kỳ ngắn cố định một cách đáng kể, nên không kết luận DQN thắng; chỉ ở Imbalance DQN vượt cả rule-based và mốc cố định.

Bằng chứng DQN ở Imbalance phụ thuộc trạng thái:
- `check_policy.py` (quan sát ngẫu nhiên, chỉ phát hiện chính sách một hành động; không đo được tính thích nghi): chọn SWITCH ở Low seed 0/1: 73,9%/47,9%; Medium: 38,3%/78,1%; Imbalance: 87,7%/53,1%.
- Tỉ lệ đổi pha khi chạy thật (seed test 1024, từ `evaluate.py`): Imbalance seed 0 yêu cầu SWITCH 61,1% và đèn đổi pha thật ở 8,6% số quyết định; seed 1 yêu cầu 41,1%, đổi pha thật 8,6%; chính sách luôn SWITCH yêu cầu 100% và đổi pha thật 12,5%. DQN đổi pha ít hơn chu kỳ ngắn cố định khoảng 31%.
- Kết hợp với mean_queue giảm khoảng 55,1% so với mốc luôn SWITCH, đây là bằng chứng ở Imbalance DQN dùng trạng thái giao thông để quyết định (chưa đo từng seed 57 và 367; mới ghi seed 1024).

### 2.5 Imbalance v2a (chỉ đổi scale, seed DRL 0, `--q-scale 70 --v-scale 110 --w-scale 30 --reward avg_wait`)

| Mô hình (Imbalance) | mean_queue | max_queue | mean_total_waiting_time | max_total_waiting_time |
|---|---|---|---|---|
| Rule-based | 38,56 ± 4,49 | 119,67 ± 3,79 | 692,27 ± 126,49 | 4879,00 ± 1033,06 |
| DQN v1, seed DRL 0 | 34,97 ± 1,37 | 107,33 ± 15,28 | 606,56 ± 34,50 | 3713,73 ± 108,56 |
| DQN v1, seed DRL 1 | 34,35 ± 3,87 | 106,00 ± 3,61 | 608,81 ± 82,70 | 3896,80 ± 214,30 |
| DQN v2a_best, seed DRL 0 | 35,79 ± 4,85 | 106,00 ± 3,61 | 656,72 ± 70,78 | 3905,47 ± 1092,20 |
| DQN v2a_model (bản cuối), seed DRL 0 | 35,79 ± 4,85 | 106,00 ± 3,61 | 656,72 ± 70,78 | 3905,47 ± 1092,20 |

- Đặc trưng bị cắt sau khi đổi scale: queue NS 8,0%, số xe NS 6,9%, thời gian chờ EW 4,8%, thời gian chờ NS 0,5% (v1: queue NS 57–63%, số xe NS 96–99%).
- Tỉ lệ đổi pha khi chạy thật (seed 1024): yêu cầu SWITCH 33,6–35,3%, đổi pha thật 8,3% (v1: 8,2–8,8%).
- Kết luận: đổi scale không cải thiện Imbalance; v2a ngang hoặc kém v1 nhẹ (khác biệt trong phạm vi độ lệch chuẩn), vẫn hơn rule-based (7,2% queue, 11,4% `max_queue`, 5,1% thời gian chờ, 20,0% `max_total_waiting_time`). Kết quả chính của Imbalance giữ là v1. `_best_model` và `_model` cho cùng kết quả.
