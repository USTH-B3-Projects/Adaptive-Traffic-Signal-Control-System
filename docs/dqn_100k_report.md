# Kết quả DQN 100.000 bước

Cấu trúc file: cấu hình chung, lịch sử thay đổi mô hình, Phần 1 (toàn bộ kết quả v1), Phần 2 (v2: chẩn đoán, kế hoạch và kết quả). Mỗi bảng kết quả ghi rõ phiên bản.

## Cấu hình chung (đánh giá, giữ nguyên giữa các phiên bản)
- Seed giao thông khi train: 0 đến 9 (không dùng 57, 367, 1024); seed giao thông khi test: 57, 367, 1024 (cùng seed với fixed-time và rule-based của nhánh maianh)
- Thước đo: 720 mẫu mỗi episode (mỗi 5 s, t = 0 đến 3595 s), `mean_queue` và `max_queue` (xe), `mean_total_waiting_time` và `max_total_waiting_time` (tổng thời gian chờ các làn vào, giây)
- Tổng hợp: trung bình ± độ lệch chuẩn mẫu (chia n−1) trên 3 seed test
- Cấu trúc: code dùng chung ở `DRL/` (gốc repo); `logs/` và `results/` của map này nằm trong `Map_Nga_Tu/`. Mọi lệnh chạy từ thư mục `Map_Nga_Tu/` và gọi code qua `../DRL/`. Các đường dẫn `logs/...`, `results/...` bên dưới đều tính từ `Map_Nga_Tu/`.
- File gốc: `results/drl/<tên mô hình>_eval.jsonl` và `_summary.json`; mô hình và log train nằm trong `logs/`. `logs/` và `results/drl/` chứa toàn bộ v1 (seed 0–4), v2a và v2b. Kết quả chính sách hằng (always SWITCH / always KEEP) nằm ở `results/constant/`. Kết quả chẩn đoán (tỉ lệ bị cắt, switch requested/executed, v2b ở High, Imbalance seed 0 và 1) nằm ở `results/diag/`. Các lần chạy thử 20.000 bước ban đầu (v0) đã được xóa khỏi thư mục dự án; số liệu của chúng chỉ còn trong mục v0 bên dưới

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
- Động cơ: DQN v1 kém rule-based ở High nhưng hơn rõ ở Imbalance. Ở High, hai mô hình (seed DRL 0 và 1) cho số liệu giống hệt nhau trên hai seed test (57 và 367), nghi ngờ đặc trưng trạng thái bị cắt về 1 (giả thuyết, cần kiểm chứng bằng bước chẩn đoán bên dưới).

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

Gồm: (1.1) seed DRL 0, (1.2) seed DRL 1, (1.3) tổng hợp 2 seed so với rule-based, (1.4) seed DRL 2, (1.5) tổng hợp 3 seed, (1.6) Imbalance với 5 seed (kết quả cuối của v1).

### 1.1 v1, seed DRL 0

#### Tổng hợp 4 kịch bản (v1: DQN 100.000 bước, seed DRL 0)

DQN giảm bao nhiêu so với rule-based (số dương: DQN tốt hơn):

| Kịch bản | mean_queue | max_queue | mean_total_waiting_time | max_total_waiting_time |
|---|---|---|---|---|
| Low | 7,5% | −10,2% | 7,6% | 1,0% |
| Medium | −1,6% | −4,8% | −2,5% | 4,9% |
| High | −4,0% | −14,0% | −6,3% | −41,3% |
| Imbalance | 16,2% | 16,7% | 19,0% | 27,9% |

- DQN tốt hơn fixed-time ở mọi kịch bản trên các thước đo trung bình.
- So với rule-based: DQN rõ ràng tốt hơn ở Imbalance, ngang ở Low và Medium, kém hơn ở High.
- Mới có một lần train mỗi kịch bản (seed DRL 0) và 3 seed test.

#### Low

##### DQN 100.000 bước, từng seed

| Seed | mean_queue | max_queue | mean_total_waiting_time | max_total_waiting_time |
|---|---|---|---|---|
| 57 | 3,31 | 13,00 | 47,03 | 264,50 |
| 367 | 3,15 | 14,00 | 44,09 | 243,70 |
| 1024 | 3,58 | 16,00 | 51,60 | 328,10 |
| **Trung bình ± SD** | **3,35 ± 0,21** | **14,33 ± 1,53** | **47,57 ± 3,79** | **278,77 ± 43,97** |

##### So với fixed-time, rule-based (nhánh maianh) và DQN 20.000 bước

| Metric | Fixed-time | Rule-based | DQN 20k | DQN 100k |
|---|---|---|---|---|
| mean_queue (xe) | 4,96 ± 0,04 | 3,62 ± 0,11 | 3,49 ± 0,06 | 3,35 ± 0,21 |
| max_queue (xe) | 18,00 ± 1,00 | 13,00 ± 1,00 | 13,33 ± 0,58 | 14,33 ± 1,53 |
| mean_total_waiting_time (s) | 97,88 ± 1,07 | 51,50 ± 1,62 | 50,47 ± 0,98 | 47,57 ± 3,79 |
| max_total_waiting_time (s) | 567,63 ± 24,16 | 281,50 ± 49,75 | 261,47 ± 3,57 | 278,77 ± 43,97 |

Số fixed-time và rule-based lấy từ `avg_baseline_result.md` của nhánh maianh (3 seed 57, 367, 1024), cần đối chiếu lại với bản mới nhất của nhánh.

##### DQN 100k giảm so với (số dương: DQN tốt hơn)

| Metric | So với fixed-time | So với rule-based |
|---|---|---|
| mean_queue | 32,5% | 7,5% |
| max_queue | 20,4% | −10,2% (kém hơn) |
| mean_total_waiting_time | 51,4% | 7,6% |
| max_total_waiting_time | 50,9% | 1,0% |

##### Nhận xét
- Đường cong huấn luyện: return tăng từ khoảng −100 lên đỉnh khoảng −83 ở episode 45 (khoảng 32.000 bước), sau đó dao động trong khoảng −85 đến −95, chưa hội tụ ổn định. Mô hình lưu là bản cuối, không phải bản tốt nhất.
- DQN tốt hơn fixed-time rõ ràng ở cả bốn thước đo.
- So với rule-based: DQN nhỉnh hơn ở hai thước đo trung bình (khoảng 7,5%) nhưng kém hơn ở `max_queue`, và độ lệch chuẩn lớn hơn. Chênh lệch nằm trong độ nhiễu của 3 seed, nên chưa kết luận DQN hơn rule-based.
- So với bản 20.000 bước: bản 100.000 nhỉnh hơn ở hai thước đo trung bình và kém hơn ở hai thước đo cực đại, độ lệch chuẩn tăng. Tăng bước không cải thiện rõ ở Low.
- Chỉ có một lần train (seed DRL 0) và 3 seed test.

#### Medium

##### DQN 100.000 bước, từng seed

| Seed | mean_queue | max_queue | mean_total_waiting_time | max_total_waiting_time |
|---|---|---|---|---|
| 57 | 9,76 | 27,00 | 137,53 | 560,60 |
| 367 | 9,38 | 31,00 | 129,92 | 561,20 |
| 1024 | 9,75 | 30,00 | 135,91 | 550,20 |
| **Trung bình ± SD** | **9,63 ± 0,21** | **29,33 ± 2,08** | **134,45 ± 4,01** | **557,33 ± 6,18** |

##### So với fixed-time và rule-based (nhánh maianh)

| Metric | Fixed-time | Rule-based | DQN 100k | DQN giảm so với fixed-time | DQN giảm so với rule-based |
|---|---|---|---|---|---|
| mean_queue (xe) | 12,93 ± 0,39 | 9,48 ± 0,18 | 9,63 ± 0,21 | 25,5% | −1,6% (kém hơn) |
| max_queue (xe) | 35,67 ± 2,89 | 28,00 ± 1,00 | 29,33 ± 2,08 | 17,8% | −4,8% (kém hơn) |
| mean_total_waiting_time (s) | 238,83 ± 8,04 | 131,17 ± 2,95 | 134,45 ± 4,01 | 43,7% | −2,5% (kém hơn) |
| max_total_waiting_time (s) | 1037,87 ± 74,52 | 586,27 ± 63,43 | 557,33 ± 6,18 | 46,3% | 4,9% |

##### Nhận xét
- Đường cong huấn luyện: return tăng từ khoảng −220 lên đỉnh khoảng −191 ở episode 57 (khoảng 41.000 bước), sau đó giảm nhẹ và dao động quanh −195 đến −205. Mô hình lưu là bản cuối, kém hơn bản ở đỉnh.
- So với fixed-time: DQN tốt hơn rõ ở cả bốn thước đo (giảm 18 đến 46%).
- So với rule-based: DQN kém hơn nhẹ ở ba thước đo (1,6 đến 4,8%) và nhỉnh hơn ở `max_total_waiting_time` (4,9%). Chênh lệch nhỏ và nằm trong độ nhiễu của 3 seed, nên coi là ngang nhau, không phải DQN vượt rule-based.
- Chỉ có một lần train (seed DRL 0) và 3 seed test.

#### High

##### DQN 100.000 bước, từng seed

| Seed | mean_queue | max_queue | mean_total_waiting_time | max_total_waiting_time |
|---|---|---|---|---|
| 57 | 39,01 | 114,00 | 655,70 | 3269,10 |
| 367 | 42,50 | 89,00 | 708,00 | 2973,50 |
| 1024 | 49,71 | 114,00 | 849,75 | 4232,10 |
| **Trung bình ± SD** | **43,74 ± 5,46** | **105,67 ± 14,43** | **737,82 ± 100,40** | **3491,57 ± 658,13** |

##### So với fixed-time và rule-based (nhánh maianh)

| Metric | Fixed-time | Rule-based | DQN 100k | DQN giảm so với fixed-time | DQN giảm so với rule-based |
|---|---|---|---|---|---|
| mean_queue (xe) | 45,58 ± 2,86 | 42,07 ± 3,47 | 43,74 ± 5,46 | 4,0% | −4,0% (kém hơn) |
| max_queue (xe) | 93,33 ± 3,21 | 92,67 ± 2,08 | 105,67 ± 14,43 | −13,2% (kém hơn) | −14,0% (kém hơn) |
| mean_total_waiting_time (s) | 939,12 ± 75,53 | 693,94 ± 51,83 | 737,82 ± 100,40 | 21,4% | −6,3% (kém hơn) |
| max_total_waiting_time (s) | 3160,43 ± 357,15 | 2471,07 ± 219,77 | 3491,57 ± 658,13 | −10,5% (kém hơn) | −41,3% (kém hơn) |

##### Nhận xét
- Đường cong huấn luyện: return rất nhiễu (từ khoảng −560 đến −1100), trung bình trượt tăng từ khoảng −880 lên khoảng −780 trong 20 episode đầu, sau đó dao động quanh −750 đến −800 mà không tăng thêm. Chưa thấy hội tụ rõ.
- So với fixed-time: DQN chỉ tốt hơn ở hai thước đo trung bình (queue giảm 4,0%, thời gian chờ giảm 21,4%), và kém hơn ở hai thước đo cực đại.
- So với rule-based: DQN kém hơn ở cả bốn thước đo (4 đến 41%), kém nhiều nhất ở `max_total_waiting_time`.
- Độ lệch chuẩn giữa các seed lớn (queue từ 39,0 đến 49,7), nên chưa kết luận chắc chắn. Chỉ có một lần train (seed DRL 0) và 3 seed test.
- Kết quả này khác với lần đánh giá cũ trên seed 100–104 (khi đó DQN thấp nhất ở High), cho thấy kết quả ở High nhạy với bộ seed.

#### Imbalance

##### DQN 100.000 bước, từng seed

| Seed | mean_queue | max_queue | mean_total_waiting_time | max_total_waiting_time |
|---|---|---|---|---|
| 57 | 30,84 | 104,00 | 527,91 | 3391,60 |
| 367 | 34,43 | 105,00 | 621,44 | 4509,90 |
| 1024 | 31,70 | 90,00 | 531,90 | 2646,50 |
| **Trung bình ± SD** | **32,32 ± 1,88** | **99,67 ± 8,39** | **560,42 ± 52,89** | **3516,00 ± 937,91** |

##### So với fixed-time và rule-based (nhánh maianh)

| Metric | Fixed-time | Rule-based | DQN 100k | DQN giảm so với fixed-time | DQN giảm so với rule-based |
|---|---|---|---|---|---|
| mean_queue (xe) | 82,78 ± 6,97 | 38,56 ± 4,49 | 32,32 ± 1,88 | 61,0% | 16,2% |
| max_queue (xe) | 259,67 ± 34,12 | 119,67 ± 3,79 | 99,67 ± 8,39 | 61,6% | 16,7% |
| mean_total_waiting_time (s) | 1850,26 ± 111,75 | 692,27 ± 126,49 | 560,42 ± 52,89 | 69,7% | 19,0% |
| max_total_waiting_time (s) | 10014,07 ± 387,89 | 4879,00 ± 1033,06 | 3516,00 ± 937,91 | 64,9% | 27,9% |

##### Nhận xét
- Đường cong huấn luyện: return tăng rõ rệt. Từ khoảng −1450 xuống đáy khoảng −2000 quanh episode 22 (giai đoạn không ổn định), rồi tăng nhanh lên khoảng −600 ở episode 45 (khoảng 32.000 bước) và đi ngang quanh −600 đến −750 đến hết 138 episode. Đây là kịch bản hội tụ rõ nhất trong bốn kịch bản.
- So với fixed-time: DQN giảm 61 đến 70% ở cả bốn thước đo.
- So với rule-based: DQN tốt hơn ở cả bốn thước đo (16 đến 28%). Ở `mean_queue` và `mean_total_waiting_time`, chênh lệch lớn hơn độ lệch chuẩn của cả hai bên; ở `max_total_waiting_time` thì chênh lệch (1363 s) vẫn nằm trong độ lệch chuẩn của hai bên.
- Chỉ có một lần train (seed DRL 0) và 3 seed test, nên cần thêm seed DRL 1, 2 để xác nhận.

### 1.2 v1, seed DRL 1

Cùng cấu hình v1, chỉ đổi `--seed 1`.

Các seed DRL khác nhau cho biết mức dao động do huấn luyện. Mỗi bảng dưới đây là một lần train, đánh giá trên seed test 57, 367, 1024.

#### Low, seed DRL 1

Đường cong huấn luyện: return tăng từ khoảng −102 lên khoảng −90 trong 15 episode đầu, rồi tăng chậm lên khoảng −87 đến −88, ít dao động hơn seed 0, không có đỉnh rồi giảm rõ rệt.

| Seed test | mean_queue | max_queue | mean_total_waiting_time | max_total_waiting_time |
|---|---|---|---|---|
| 57 | 3,54 | 12,00 | 50,36 | 260,70 |
| 367 | 3,65 | 13,00 | 53,70 | 300,80 |
| 1024 | 3,71 | 14,00 | 52,71 | 280,90 |
| **Trung bình ± SD** | **3,63 ± 0,09** | **13,00 ± 1,00** | **52,25 ± 1,72** | **280,80 ± 20,05** |

#### Low, so sánh giữa các seed DRL

| Metric | Rule-based | DQN seed 0 | DQN seed 1 | Trung bình 2 seed DRL |
|---|---|---|---|---|
| mean_queue (xe) | 3,62 ± 0,11 | 3,35 ± 0,21 | 3,63 ± 0,09 | 3,49 |
| max_queue (xe) | 13,00 ± 1,00 | 14,33 ± 1,53 | 13,00 ± 1,00 | 13,67 |
| mean_total_waiting_time (s) | 51,50 ± 1,62 | 47,57 ± 3,79 | 52,25 ± 1,72 | 49,91 |
| max_total_waiting_time (s) | 281,50 ± 49,75 | 278,77 ± 43,97 | 280,80 ± 20,05 | 279,79 |

Nhận xét (Low):
- Seed 1 kém hơn seed 0 ở `mean_queue` (3,63 so với 3,35) và `mean_total_waiting_time` (52,25 so với 47,57). Seed 1 ngang rule-based, còn seed 0 nhỉnh hơn rule-based khoảng 7,5%. Chênh lệch giữa hai seed DRL xấp xỉ chênh lệch giữa DQN và rule-based, nên kết luận ở Low vẫn là DQN ngang rule-based.
- Trung bình 2 seed DRL: `mean_queue` thấp hơn rule-based khoảng 3,6%, thời gian chờ trung bình thấp hơn khoảng 3,1%, `max_queue` cao hơn khoảng 5,1%. Đây là chênh lệch nhỏ.

#### Medium, seed DRL 1

Đường cong huấn luyện: return tăng từ khoảng −228 lên khoảng −200 trong 25 episode đầu, rồi tiếp tục tăng chậm đến khoảng −196 ở cuối, không giảm lại như seed 0 (seed 0 đạt đỉnh ở episode 57 rồi giảm nhẹ).

| Seed test | mean_queue | max_queue | mean_total_waiting_time | max_total_waiting_time |
|---|---|---|---|---|
| 57 | 9,52 | 27,00 | 132,63 | 556,20 |
| 367 | 9,51 | 28,00 | 133,10 | 628,60 |
| 1024 | 9,81 | 29,00 | 138,08 | 678,00 |
| **Trung bình ± SD** | **9,61 ± 0,17** | **28,00 ± 1,00** | **134,60 ± 3,02** | **620,93 ± 61,26** |

#### Medium, so sánh giữa các seed DRL

| Metric | Rule-based | DQN seed 0 | DQN seed 1 | Trung bình 2 seed DRL |
|---|---|---|---|---|
| mean_queue (xe) | 9,48 ± 0,18 | 9,63 ± 0,21 | 9,61 ± 0,17 | 9,62 |
| max_queue (xe) | 28,00 ± 1,00 | 29,33 ± 2,08 | 28,00 ± 1,00 | 28,67 |
| mean_total_waiting_time (s) | 131,17 ± 2,95 | 134,45 ± 4,01 | 134,60 ± 3,02 | 134,53 |
| max_total_waiting_time (s) | 586,27 ± 63,43 | 557,33 ± 6,18 | 620,93 ± 61,26 | 589,13 |

Nhận xét (Medium):
- Hai seed DRL cho kết quả rất gần nhau ở hai thước đo trung bình (queue 9,63 và 9,61; thời gian chờ 134,45 và 134,60), nên kết quả ở Medium khá ổn định theo seed.
- Trung bình 2 seed DRL kém rule-based nhẹ ở cả bốn thước đo (queue 1,5%, `max_queue` 2,4%, thời gian chờ 2,6%, `max_total_waiting_time` 0,5%). Chênh lệch nhỏ, nằm trong độ lệch chuẩn, nên kết luận ở Medium là DQN ngang rule-based, hơi kém một chút.

#### High, seed DRL 1

Đường cong huấn luyện: return tăng từ khoảng −980 lên khoảng −780 trong 20 episode đầu, đạt đỉnh trung bình trượt khoảng −690 ở episode 42, sau đó dao động quanh −720 đến −800 (có một episode tụt xuống khoảng −1080 ở episode 114). Chưa hội tụ rõ, giống seed 0.

| Seed test | mean_queue | max_queue | mean_total_waiting_time | max_total_waiting_time |
|---|---|---|---|---|
| 57 | 39,01 | 114,00 | 655,70 | 3269,10 |
| 367 | 42,50 | 89,00 | 708,00 | 2973,50 |
| 1024 | 47,08 | 106,00 | 798,58 | 2851,70 |
| **Trung bình ± SD** | **42,86 ± 4,05** | **103,00 ± 12,77** | **720,76 ± 72,29** | **3031,43 ± 214,65** |

#### High, so sánh giữa các seed DRL

| Metric | Rule-based | DQN seed 0 | DQN seed 1 | Trung bình 2 seed DRL |
|---|---|---|---|---|
| mean_queue (xe) | 42,07 ± 3,47 | 43,74 ± 5,46 | 42,86 ± 4,05 | 43,30 |
| max_queue (xe) | 92,67 ± 2,08 | 105,67 ± 14,43 | 103,00 ± 12,77 | 104,34 |
| mean_total_waiting_time (s) | 693,94 ± 51,83 | 737,82 ± 100,40 | 720,76 ± 72,29 | 729,29 |
| max_total_waiting_time (s) | 2471,07 ± 219,77 | 3491,57 ± 658,13 | 3031,43 ± 214,65 | 3261,50 |

Nhận xét (High):
- Hai seed DRL cho kết quả gần nhau ở các thước đo trung bình. Trung bình 2 seed DRL kém rule-based ở cả bốn thước đo: queue 2,9%, `max_queue` 12,6%, thời gian chờ trung bình 5,1%, `max_total_waiting_time` 32,0%. Kết luận ở High giữ nguyên: DQN v1 chưa đạt rule-based.
- Ở seed test 57 và 367, hai mô hình (seed DRL 0 và 1) cho số liệu giống hệt nhau đến hai chữ số thập phân (ví dụ seed 57: queue 39,01, tổng thời gian chờ 655,70), chỉ khác ở seed test 1024. Nguyên nhân chưa kiểm chứng. Giả thuyết: ở High, nhiều đặc trưng trạng thái bị cắt về giá trị 1 (queue mỗi nhóm trên 20 xe, số xe trên 30, thời gian chờ trên 60 s), nên chính sách chủ yếu phụ thuộc vào thời gian xanh đã qua và hai mô hình học ra cùng một quy tắc. Cách kiểm tra: tính tỉ lệ các đặc trưng bị cắt khi đánh giá.

#### Imbalance, seed DRL 1

Đường cong huấn luyện: giống seed 0. Return tăng từ khoảng −1600, đáy khoảng −1700 quanh episode 25, rồi tăng nhanh lên khoảng −600 ở episode 40 (khoảng 29.000 bước) và đi ngang quanh −600 đến −750, có một đoạn tụt nhẹ quanh episode 120. Hội tụ rõ.

| Seed test | mean_queue | max_queue | mean_total_waiting_time | max_total_waiting_time |
|---|---|---|---|---|
| 57 | 30,72 | 102,00 | 561,38 | 3912,90 |
| 367 | 29,31 | 88,00 | 503,02 | 2614,90 |
| 1024 | 35,07 | 103,00 | 614,85 | 3936,20 |
| **Trung bình ± SD** | **31,70 ± 3,00** | **97,67 ± 8,39** | **559,75 ± 55,94** | **3488,00 ± 756,22** |

#### Imbalance, so sánh giữa các seed DRL

| Metric | Rule-based | DQN seed 0 | DQN seed 1 | Trung bình 2 seed DRL |
|---|---|---|---|---|
| mean_queue (xe) | 38,56 ± 4,49 | 32,32 ± 1,88 | 31,70 ± 3,00 | 32,01 |
| max_queue (xe) | 119,67 ± 3,79 | 99,67 ± 8,39 | 97,67 ± 8,39 | 98,67 |
| mean_total_waiting_time (s) | 692,27 ± 126,49 | 560,42 ± 52,89 | 559,75 ± 55,94 | 560,09 |
| max_total_waiting_time (s) | 4879,00 ± 1033,06 | 3516,00 ± 937,91 | 3488,00 ± 756,22 | 3502,00 |

Nhận xét (Imbalance):
- Hai seed DRL cho kết quả rất gần nhau ở mọi thước đo (queue 32,32 và 31,70; thời gian chờ 560,42 và 559,75), nên kết quả ở Imbalance ổn định theo seed.
- Trung bình 2 seed DRL tốt hơn rule-based ở cả bốn thước đo: queue 17,0%, `max_queue` 17,5%, thời gian chờ trung bình 19,1%, `max_total_waiting_time` 28,2%. Ở ba thước đo đầu, chênh lệch lớn hơn độ lệch chuẩn của cả hai bên. Imbalance là kịch bản duy nhất DQN v1 hơn rule-based.

### 1.3 v1, tổng hợp 2 seed DRL (0 và 1) so với rule-based

DQN giảm bao nhiêu so với rule-based (số dương: DQN tốt hơn). Low và Medium, High, Imbalance đều có đủ 2 seed DRL.

| Kịch bản | mean_queue | max_queue | mean_total_waiting_time | max_total_waiting_time |
|---|---|---|---|---|
| Low | 3,6% | −5,1% | 3,1% | 0,6% |
| Medium | −1,5% | −2,4% | −2,6% | −0,5% |
| High | −2,9% | −12,6% | −5,1% | −32,0% |
| Imbalance | 17,0% | 17,5% | 19,1% | 28,2% |

- Imbalance: DQN hơn rule-based rõ và ổn định giữa hai seed. Low và Medium: ngang. High: kém.
- Mới có 2 seed DRL và 3 seed test, nên chưa có độ tin cậy thống kê cao.
- Lưu ý: ở Low, Medium và High, kết quả DQN gần như trùng chính sách cố định "luôn SWITCH" (xem mục 2.4); chỉ ở Imbalance DQN thực sự vượt cả mốc này.

### 1.4 v1, seed DRL 2 (code v2 với `--reward avg_wait --eval-freq 0`, scale mặc định, `--tag v1`; bản cuối `_model`; 3 seed test)

| Kịch bản | mean_queue | max_queue | mean_total_waiting_time | max_total_waiting_time | đổi pha thật (seed 1024) |
|---|---|---|---|---|---|
| Low | 3,60 ± 0,07 | 14,00 ± 2,00 | 52,14 ± 2,08 | 269,87 ± 26,36 | 12,1% |
| Medium | 9,45 ± 0,30 | 26,00 ± 1,00 | 133,54 ± 4,70 | 561,77 ± 38,72 | 12,2% |
| High | 39,96 ± 7,44 | 91,33 ± 18,90 | 655,91 ± 149,88 | 2299,20 ± 603,96 | 12,5% |
| Imbalance | 37,59 ± 8,18 | 114,67 ± 13,65 | 675,45 ± 150,32 | 3944,33 ± 387,54 | 8,6% |

- Đặc trưng bị cắt (scale mặc định): High queue 40–42%, số xe 84–85%; Imbalance queue NS 63,1%, số xe NS 95,9%; Low và Medium gần như không bị cắt.
- High: số liệu seed test 1024 trùng chính sách luôn SWITCH (47,08 / 106 / 798,58 / 2851,70), nhưng trung bình 3 seed test khác (39,96 so với 42,86), nên ở hai seed test còn lại seed DRL 2 có hành vi khác mốc. Độ lệch chuẩn lớn (7,44).
- Imbalance: seed DRL 2 kém hơn hẳn seed 0 và 1 (37,59 so với 32,32 và 31,70) và gần rule-based, nên kết quả ở Imbalance không ổn định giữa các seed DRL như nhận xét trước (khi mới có 2 seed).
- Seed 2 chưa có đường cong huấn luyện trong file này.

### 1.5 v1, tổng hợp 3 seed DRL (0, 1, 2): trung bình ± độ lệch chuẩn giữa các seed DRL

Mỗi seed DRL được lấy trung bình trên 3 seed test trước; độ lệch chuẩn mẫu (n−1) tính giữa 3 giá trị đó.

| Kịch bản | mean_queue | max_queue | mean_total_waiting_time | max_total_waiting_time |
|---|---|---|---|---|
| Low | 3,53 ± 0,15 | 13,78 ± 0,69 | 50,65 ± 2,67 | 276,48 ± 5,81 |
| Medium | 9,56 ± 0,10 | 27,78 ± 1,68 | 134,20 ± 0,57 | 580,01 ± 35,51 |
| High | 42,19 ± 1,98 | 100,00 ± 7,63 | 704,83 ± 43,22 | 2940,73 ± 601,34 |
| Imbalance | 33,87 ± 3,24 | 104,00 ± 9,29 | 598,54 ± 66,61 | 3649,44 ± 255,76 |

DQN so với rule-based (số dương: DQN tốt hơn), trung bình 3 seed DRL:

| Kịch bản | mean_queue | max_queue | mean_total_waiting_time | max_total_waiting_time |
|---|---|---|---|---|
| Low | 2,6% | −6,0% | 1,6% | 1,8% |
| Medium | −0,9% | 0,8% | −2,3% | 1,1% |
| High | −0,3% | −7,9% | −1,6% | −19,0% |
| Imbalance | 12,2% | 13,1% | 13,5% | 25,2% |

DQN so với chính sách luôn SWITCH (mục 2.4), trung bình 3 seed DRL:

| Kịch bản | mean_queue | max_queue | mean_total_waiting_time | max_total_waiting_time |
|---|---|---|---|---|
| Low | 2,6% | −3,4% | 2,1% | 3,2% |
| Medium | 0,1% | 0,8% | −1,5% | 1,6% |
| High | 1,6% | 2,9% | 2,2% | 3,0% |
| Imbalance | 54,5% | 55,4% | 49,8% | 41,5% |

Kết luận v1 (3 seed DRL, 3 seed test):
- Low, Medium, High: DQN ngang rule-based và ngang chính sách luôn SWITCH (khác biệt vài phần trăm, nhỏ hơn độ lệch chuẩn). Không có bằng chứng DQN tốt hơn.
- Imbalance: DQN hơn rule-based khoảng 12–25% (hẹp hơn so với 17–28% khi mới có 2 seed, vì seed 2 kém hơn) và hơn chính sách luôn SWITCH khoảng 42–55%. Độ lệch chuẩn giữa các seed DRL khá lớn (queue 3,24; thời gian chờ 66,61), nên mức hơn rule-based có độ tin cậy vừa phải, chưa chắc chắn.

### 1.6 v1, Imbalance với 5 seed DRL (0 đến 4)

Seed 3 và 4 chạy bằng code v2 với `--reward avg_wait --eval-freq 0 --tag v1` (cấu hình tương đương v1), bản cuối `_model`, 3 seed test 57, 367, 1024.

| Seed DRL | mean_queue | max_queue | mean_total_waiting_time | max_total_waiting_time | yêu cầu SWITCH / đổi pha thật (seed 1024) |
|---|---|---|---|---|---|
| 0 | 32,32 ± 1,88 | 99,67 ± 8,39 | 560,42 ± 52,89 | 3516,00 ± 937,91 | 60,8% / 8,8% |
| 1 | 31,70 ± 3,00 | 97,67 ± 8,39 | 559,75 ± 55,94 | 3488,00 ± 756,22 | 40,1% / 8,6% |
| 2 | 37,59 ± 8,18 | 114,67 ± 13,65 | 675,45 ± 150,32 | 3944,33 ± 387,54 | 41,1% / 8,6% |
| 3 | 33,87 ± 1,76 | 104,33 ± 10,41 | 608,95 ± 29,44 | 3679,03 ± 502,45 | 56,4% / 8,3% |
| 4 | 34,61 ± 3,07 | 105,67 ± 18,45 | 677,98 ± 58,72 | 4744,70 ± 574,66 | 7,6% / 8,2% |
| Trung bình ± SD giữa 5 seed DRL | 34,02 ± 2,31 | 104,40 ± 6,61 | 616,51 ± 58,48 | 3874,41 ± 519,19 | |
| Rule-based (nhánh maianh) | 38,56 ± 4,49 | 119,67 ± 3,79 | 692,27 ± 126,49 | 4879,00 ± 1033,06 | |
| Luôn SWITCH | 74,41 ± 7,99 | 233,00 ± 23,52 | 1192,05 ± 119,00 | 6239,97 ± 431,32 | 100% / 12,5% |
| Luôn KEEP | 93,44 ± 11,93 | 257,00 ± 26,89 | 2912,17 ± 444,88 | 14723,93 ± 2789,57 | 0% / 6,1% |

- DQN (trung bình 5 seed DRL) hơn rule-based: mean_queue 11,8%, max_queue 12,8%, mean_total_waiting_time 10,9%, max_total_waiting_time 20,6%; hơn chính sách luôn SWITCH: 54,3%, 55,2%, 48,3%, 37,9%.
- Từng seed DRL đều có mean_queue thấp hơn rule-based (hơn từ 2,5% đến 17,8% tùy seed); seed 2 chỉ hơn khoảng 2,5% (nằm trong độ lệch chuẩn), các seed còn lại hơn 10–18%.
- Mọi seed có tỉ lệ đổi pha thật 8,2–8,8%, thấp hơn 12,5% của chính sách luôn SWITCH.
- Seed 4 chỉ yêu cầu SWITCH 7,6% số quyết định nhưng đèn đổi pha thật ở 8,2%. Để kiểm tra có phải chính sách "luôn KEEP" (chỉ đổi pha khi bị ép ở xanh tối đa 75 s) hay không, đã chạy `--constant keep` (3 seed test): mean_queue 93,44 ± 11,93, max_queue 257,00 ± 26,89, mean_total_waiting_time 2912,17 ± 444,88, max_total_waiting_time 14723,93 ± 2789,57, đổi pha thật 6,1%. Mốc này kém xa seed 4 (34,61; 677,98), nên seed 4 không phải "luôn KEEP": nó đổi pha có chủ động theo trạng thái (đổi pha thật 8,2% so với 6,1%), chỉ là kém hơn các seed 0, 1, 3.
- Kết luận: ở Imbalance, DQN hơn rule-based khoảng 11–21% trung bình 5 seed DRL, nhưng độ lớn khác nhau giữa các seed (2,5% đến 17,8%).

---

## PHẦN 2. KẾT QUẢ V2

### 2.1 Chẩn đoán và kế hoạch

Kế hoạch chạy v2:
1. Chẩn đoán trên các mô hình v1 đã có (không cần train lại): chạy `evaluate.py` v2 với mô hình v1 của High và Imbalance để xem tỉ lệ đặc trưng bị cắt và hằng số chuẩn hóa gợi ý. Kết quả chẩn đoán điền vào bảng dưới.
2. Nếu tỉ lệ bị cắt cao (ví dụ trên 30% số bước) ở High, train lại High (và Imbalance nếu cần) với `--q-scale`, `--v-scale`, `--w-scale` theo gợi ý.
3. Train v2 (reward mới, lưu mô hình tốt nhất) cho cả 4 kịch bản, rồi đánh giá bằng `evaluate.py` trên seed 57, 367, 1024 và ghi rõ dùng `_best_model` hay `_model`.

Kết quả chẩn đoán trên mô hình v1 (High và Imbalance đã chạy). Kết luận High: giả thuyết đúng. Với hằng số mặc định (20, 30, 60), hơn 40% số bước queue bị cắt về 1 và khoảng 85% số bước số xe bị cắt về 1, nên mô hình không phân biệt được mức tắc nghẽn từ trung bình đến nặng. Thời gian chờ không bị cắt:

| Mô hình v1 | queue bị cắt (tỉ lệ bước) | số xe bị cắt | thời gian chờ bị cắt | hằng số gợi ý (q, v, w) |
|---|---|---|---|---|
| High seed 0 | 43.4% (NS), 44.6% (EW) | 85.7% (NS), 87.1% (EW) | 0% | 56, 84, 19 |
| High seed 1 | 42.7% (NS), 45.4% (EW) | 84.7% (NS), 88.3% (EW) | 0% | 57, 81, 19 |
| Imbalance seed 0 | NS 54,7%, EW 0,1% | NS 98,4% (EW không bị cắt) | không ghi nhận | 70, 108, 27 |
| Imbalance seed 1 | NS 53,0%, EW 0% | NS 97,4% (EW không bị cắt) | không ghi nhận | 70, 106, 26 |

Kế hoạch train v2 cho High (seed DRL 0), tách từng thay đổi để biết cải thiện đến từ đâu (chưa có kết quả):

| Cấu hình | Reward | Scale (q, v, w) | Tag | Lệnh |
|---|---|---|---|---|
| v2a | `avg_wait` (như v1) | 60, 90, 30 | `v2a` | `python ../DRL/train_dqn.py --scenario high --seed 0 --q-scale 60 --v-scale 90 --w-scale 30 --reward avg_wait --tag v2a` |
| v2b | `total_wait` (mới) | 60, 90, 30 | `v2b` | `python ../DRL/train_dqn.py --scenario high --seed 0 --q-scale 60 --v-scale 90 --w-scale 30 --reward total_wait --tag v2b` |

Đánh giá bằng mô hình tốt nhất: `python ../DRL/evaluate.py --scenario high --model logs/dqn_high_seed0_v2b_best_model` (v2a tương tự). So v2a với v1 cho thấy tác dụng của scale; so v2b với v2a cho thấy tác dụng của reward.

Nhận định Imbalance: hướng NS bị bão hòa nặng với hằng số v1 (queue NS bị cắt 53–55% số bước, số xe NS bị cắt 97–98%; hướng EW gần như không bị cắt), nên scale v1 cũng quá nhỏ cho Imbalance. DQN v1 vẫn hơn rule-based khoảng 17–28% nên đây là cơ hội cải thiện thêm, không phải lỗi. Quyết định: thử Imbalance với scale mới sau khi có kết quả High (gợi ý `--q-scale 70 --v-scale 110 --w-scale 30`); mỗi lần train khoảng 1 giờ. Low và Medium giữ kết quả v1 (chưa chẩn đoán).

Ghi chú:
- `TOTAL_WAIT_SCALE` = 1000 là giá trị chọn ban đầu, chưa thử nghiệm.
- Return của v2 dùng reward khác v1 nên không so trực tiếp được với đường cong v1.
- Thay đổi quan sát chỉ áp dụng khi truyền các cờ `--q-scale`... lúc train; mô hình v1 vẫn đánh giá đúng với `evaluate.py` v2 (dùng hằng số mặc định).
- Khi có kết quả v2, thêm bảng riêng cho v2 (từng seed, so với fixed-time, rule-based và v1).

### 2.2 Kết quả train v2 (High, seed DRL 0, bản `_best_model`)

High, đánh giá trên seed test 57, 367, 1024 bằng `_best_model`. Số liệu fixed-time và rule-based lấy từ nhánh maianh.

| Mô hình | mean_queue | max_queue | mean_total_waiting_time | max_total_waiting_time |
|---|---|---|---|---|
| Fixed-time | 45,58 ± 2,86 | 93,33 ± 3,21 | 939,12 ± 75,53 | 3160,43 ± 357,15 |
| Rule-based | 42,07 ± 3,47 | 92,67 ± 2,08 | 693,94 ± 51,83 | 2471,07 ± 219,77 |
| DQN v1, seed DRL 0 | 43,74 ± 5,46 | 105,67 ± 14,43 | 737,82 ± 100,40 | 3491,57 ± 658,13 |
| DQN v1, seed DRL 1 | 42,86 ± 4,05 | 103,00 ± 12,77 | 720,76 ± 72,29 | 3031,43 ± 214,65 |
| DQN v1, trung bình 2 seed DRL | 43,30 | 104,33 | 729,29 | 3261,50 |
| DQN v2a_best (chỉ đổi scale), seed DRL 0 | 43,67 ± 2,39 | 97,00 ± 1,73 | 745,99 ± 46,27 | 2846,27 ± 210,72 |
| DQN v2b_best (scale và reward mới), seed DRL 0 | 43,34 ± 3,32 | 96,67 ± 8,62 | 720,19 ± 72,92 | 2957,73 ± 99,10 |

Đặc trưng bị cắt về 1 sau khi đổi scale (60, 90, 30): v2a: queue NS 0,1%, queue EW 5,9%, số xe EW 3,3%, thời gian chờ EW 0%; v2b: queue NS 1,0%, queue EW 3,2%, số xe NS 0,3%, số xe EW 1,1%, thời gian chờ EW 0%. Ở v1 các đặc trưng này bị cắt 43–88% số bước.

Nhận xét v2 (High):
- Scale mới hết bão hòa quan sát, nhưng hai chỉ số trung bình (`mean_queue`, `mean_total_waiting_time`) ngang v1 (khác biệt nhỏ hơn độ lệch chuẩn).
- Hai chỉ số cực đại cải thiện: `max_queue` khoảng 97 (v1 khoảng 104), `max_total_waiting_time` 2846 (v2a) và 2958 (v2b) so với khoảng 3260 của v1.
- So với rule-based, DQN v2 vẫn kém ở High (so với rule-based, số âm là DQN kém hơn): v2a: queue −3,8%, `max_queue` −4,7%, thời gian chờ −7,5%, `max_total_waiting_time` −15,2%; v2b: −3,0%, −4,3%, −3,8%, −19,7%. DQN v2 vẫn tốt hơn fixed-time ở các chỉ số trung bình.
- v2a và v2b khác nhau trong phạm vi độ lệch chuẩn, và mới có một seed DRL, nên chưa kết luận reward mới tốt hơn hay kém hơn.
- Chưa đánh giá bản cuối `_model` và chưa train seed DRL 1 cho v2.

### 2.3 Phát hiện: bản cuối ở High suy biến thành chính sách "đổi pha ngay khi được phép"

Đánh giá bản cuối (`_model`) của v2a và v2b ở High cho cùng một kết quả, và kết quả đó trùng khớp từng chữ số với v1 seed 1 (kể cả từng seed test, ví dụ seed 1024: 47,08 / 106 / 798,58 / 2851,70):

| Mô hình (High, bản cuối) | mean_queue | max_queue | mean_wait | max_wait |
|---|---|---|---|---|
| v1 seed 1 | 42,86 ± 4,05 | 103,00 ± 12,77 | 720,76 ± 72,29 | 3031,43 ± 214,65 |
| v2a_model | 42,86 ± 4,05 | 103,00 ± 12,77 | 720,76 ± 72,29 | 3031,43 ± 214,65 |
| v2b_model | 42,86 ± 4,05 | 103,00 ± 12,77 | 720,76 ± 72,29 | 3031,43 ± 214,65 |

Ba mạng huấn luyện độc lập (khác scale quan sát và khác reward) cho quỹ đạo giống hệt nhau, nên chính sách không phụ thuộc trạng thái. Kiểm tra bằng `DRL/check_policy.py` (20.000 quan sát ngẫu nhiên trong [0, 1]^11) và `evaluate.py` (tỉ lệ SWITCH khi chạy thật):

| Mô hình (High) | tỉ lệ chọn SWITCH trên quan sát ngẫu nhiên | Q(SWITCH) − Q(KEEP) trung bình |
|---|---|---|
| v1 seed 1 (cuối) | 99,1% | +1,319 |
| v2a (cuối) | 98,5% | +1,167 |
| v2b (cuối) | 89,8% | +1,756 |
| v2a_best | 66,9% | +0,115 |
| v2b_best | 80,6% | +2,053 |

Khi chạy thật, v2b (cuối) yêu cầu SWITCH ở 88,3% số quyết định nhưng đèn chỉ đổi pha thật ở 12,5% số quyết định, vì yêu cầu trước khi hết thời gian đèn xanh tối thiểu (30 s) bị bỏ qua.

Kiểm chứng bằng chính sách cố định (`python ../DRL/evaluate.py --scenario high --constant switch`, luôn yêu cầu SWITCH; đèn chỉ đổi khi hết 30 s xanh tối thiểu, thực tế đổi ở 12,5% số quyết định): kết quả **trùng từng chữ số** với v1 seed 1, v2a_model và v2b_model:

| Mô hình (High) | mean_queue | max_queue | mean_wait | max_wait |
|---|---|---|---|---|
| Luôn SWITCH (chính sách cố định) | 42,86 ± 4,05 | 103,00 ± 12,77 | 720,76 ± 72,29 | 3031,43 ± 214,65 |

Kết luận: ở High, DQN bản cuối (v1 seed 1, v2a, v2b) chỉ học được "đổi pha ngay khi được phép" (chu kỳ ngắn cố định), không dùng trạng thái giao thông. Hai bản `_best_model` ít cực đoan hơn (66,9% và 80,6% quan sát ngẫu nhiên chọn SWITCH) nên có số liệu khác, nhưng khác biệt nhỏ và mới có một seed DRL. Hệ quả cho báo cáo: ở High không kết luận DQN học được điều khiển thích nghi; mốc "luôn SWITCH" cần có trong bảng so sánh.

### 2.4 Mốc "luôn SWITCH" ở cả 4 kịch bản (3 seed test 57, 367, 1024; mean ± SD)

Chính sách cố định: luôn yêu cầu SWITCH, đèn đổi pha ngay khi hết 30 s xanh tối thiểu (thực tế đổi pha ở 12,5% số quyết định). Chạy bằng `python ../DRL/evaluate.py --scenario <kịch bản> --constant switch`.

| Kịch bản | mean_queue | max_queue | mean_total_waiting_time | max_total_waiting_time |
|---|---|---|---|---|
| Low | 3,62 ± 0,10 | 13,33 ± 1,15 | 51,74 ± 1,68 | 285,57 ± 52,38 |
| Medium | 9,57 ± 0,17 | 28,00 ± 1,00 | 132,25 ± 2,58 | 589,63 ± 61,16 |
| High | 42,86 ± 4,05 | 103,00 ± 12,77 | 720,76 ± 72,29 | 3031,43 ± 214,65 |
| Imbalance | 74,41 ± 7,99 | 233,00 ± 23,52 | 1192,05 ± 119,00 | 6239,97 ± 431,32 |

So sánh với rule-based và DQN v1 (trung bình 2 seed DRL):
- Low: mốc luôn SWITCH gần như trùng rule-based (3,62 so với 3,62; 51,74 so với 51,50). DQN v1 ngang cả hai; seed 0 tốt hơn nhẹ ở thời gian chờ (47,57), seed 1 không (52,25).
- Medium: mốc luôn SWITCH (9,57; 132,25) ngang rule-based (9,48; 131,17) và DQN v1 (9,62; 134,5).
- High: DQN bản cuối trùng hoàn toàn với mốc luôn SWITCH; rule-based nhỉnh hơn (xem 2.3).
- Imbalance: mốc luôn SWITCH (74,41; 1192,05) tốt hơn fixed-time (82,78; 1850,26) nhưng kém xa rule-based (38,56; 692,27). DQN v1 (32,01; 560,09) giảm khoảng 57% queue, 53% thời gian chờ và 44% `max_total_waiting_time` so với mốc này, nên ở Imbalance DQN thực sự học được chính sách phụ thuộc trạng thái (cấp xanh theo hướng đông xe). Đây là kết quả có ý nghĩa của DRL trong nghiên cứu này.

Hệ quả cho báo cáo: ở Low, Medium và High, rule-based và DQN không khác chính sách chu kỳ ngắn cố định một cách đáng kể, nên không kết luận DQN thắng; chỉ ở Imbalance DQN vượt cả rule-based và mốc cố định.

Bằng chứng DQN ở Imbalance phụ thuộc trạng thái:
- `check_policy.py` (quan sát ngẫu nhiên, chỉ phát hiện chính sách một hành động; không đo được tính thích nghi): chọn SWITCH ở Low seed 0/1: 73,9%/47,9%; Medium: 38,3%/78,1%; Imbalance: 87,7%/53,1%.
- Tỉ lệ đổi pha khi chạy thật (seed test 1024, từ `evaluate.py` mới): Imbalance seed 0 yêu cầu SWITCH 60,8% và đèn đổi pha thật ở 8,8% số quyết định; seed 1 yêu cầu 40,1%, đổi pha thật 8,6%; chính sách luôn SWITCH yêu cầu 100% và đổi pha thật 12,5%. DQN giữ xanh lâu hơn chu kỳ ngắn cố định khoảng 30%.
- Kết hợp với mean_queue giảm khoảng 57% so với mốc luôn SWITCH, đây là bằng chứng ở Imbalance DQN dùng trạng thái giao thông để quyết định (chưa đo từng seed 57 và 367; mới ghi seed 1024).

### 2.5 Imbalance v2a (chỉ đổi scale, seed DRL 0, `--q-scale 70 --v-scale 110 --w-scale 30 --reward avg_wait`)

| Mô hình (Imbalance) | mean_queue | max_queue | mean_total_waiting_time | max_total_waiting_time |
|---|---|---|---|---|
| Rule-based | 38,56 ± 4,49 | 119,67 ± 3,79 | 692,27 ± 126,49 | 4879,00 ± 1033,06 |
| DQN v1, seed DRL 0 | 32,32 ± 1,88 | 99,67 ± 8,39 | 560,42 ± 52,89 | 3516,00 ± 937,91 |
| DQN v1, seed DRL 1 | 31,70 ± 3,00 | 97,67 ± 8,39 | 559,75 ± 55,94 | 3488,00 ± 756,22 |
| DQN v2a_best, seed DRL 0 | 32,76 ± 0,83 | 100,67 ± 15,31 | 583,09 ± 24,72 | 3532,30 ± 583,95 |
| DQN v2a_model (bản cuối), seed DRL 0 | 32,83 ± 0,92 | 100,67 ± 15,31 | 585,06 ± 27,97 | 3532,30 ± 583,95 |

- Đặc trưng bị cắt sau khi đổi scale: queue NS 4,6–4,7%, số xe NS 3,2–3,3%, thời gian chờ EW 4,7%, thời gian chờ NS 0,1% (v1: queue NS 53–55%, số xe NS 97–98%).
- Tỉ lệ đổi pha khi chạy thật (seed 1024): yêu cầu SWITCH 33,6–35,0%, đổi pha thật 8,3% (v1: 8,6–8,8%).
- Kết luận: đổi scale không cải thiện Imbalance; v2a ngang hoặc kém v1 nhẹ (khác biệt trong phạm vi độ lệch chuẩn), vẫn hơn rule-based khoảng 15–28%. Kết quả chính của Imbalance giữ là v1. `_best_model` và `_model` gần như trùng nhau.
