# Ngã Tư Thăng Long

Mô phỏng giao thông mặt đất tại nút Trần Duy Hưng – Đại lộ Thăng Long – Phạm Hùng – Khuất Duy Tiến. Thư mục này chỉ chứa bộ map đã tạo sẵn để chạy bằng SUMO.

## Chạy

Cài Eclipse SUMO và thêm `sumo-gui` vào PATH. Phiên bản đã kiểm tra: 1.27.1.

Nhấp đúp launcher trong `scenarios/Low`, `Medium`, `High` hoặc `Imbalance`, hoặc chạy tại thư mục này:

```powershell
.\run.bat Low
.\run.bat Medium
.\run.bat High
.\run.bat Imbalance
```

Không truyền tên kịch bản thì mặc định chạy Low. Launcher tự tạo thư mục output khi chạy.

| Kịch bản | Nhu cầu | Khoảng sinh xe |
|---|---:|---|
| Low | 1.200 xe/giờ | 0–3.600 giây |
| Medium | 3.000 xe/giờ | 0–3.600 giây |
| High | 5.400 xe/giờ | 0–3.600 giây |
| Imbalance | 6.300 xe/giờ, hướng đông xe thay đổi | 0–10.800 giây |

## File cần giữ

- `network/thang_long.net.xml`: mạng đường và đèn.
- `config/osm.view.xml`: cấu hình hiển thị.
- `scenarios/<kịch bản>/simulation.sumocfg`: cấu hình mô phỏng.
- `scenarios/<kịch bản>/traffic.rou.xml`: loại xe, tuyến và lưu lượng.
- Các launcher `.bat`: mở mô phỏng và tạo thư mục kết quả.

Hiển thị mặc định ẩn vạch sublane và đường nối chẩn đoán, bật mặt phủ nút và giữ vạch làn đường thông thường. Mở lại mô phỏng để nạp cấu hình mới; `Ctrl+J` bật/tắt mặt phủ nút.

Kết quả được ghi vào `output/<kịch bản>/seed42/` và được Git bỏ qua. Chạy lại cùng kịch bản sẽ ghi đè kết quả cũ.

## Tổ chức làn và rẽ phải

| Hướng vào | Làn đi thẳng | Làn rẽ trái | Làn rẽ phải riêng |
|---|---:|---:|---:|
| Bắc (N) | 3 | 2 | 2 |
| Đông (E) | 3 | 2 | 2 |
| Nam (S) | 4 | 3 | 2 |
| Tây (W) | 2 | 2 | 2 |

Bốn đường `N_right_bypass`, `E_right_bypass`, `S_right_bypass`, `W_right_bypass` đều có hai làn, tách khỏi dòng chính và không chịu điều khiển đèn ở cả hai đầu. Làn 0 của mỗi đường chính `*_main_in` tiếp tục đi thẳng vào nút.

Đoạn mở rộng trước chỗ tách có 7 làn ở Bắc/Đông, 9 làn ở Nam và 6 làn ở Tây. Tại chỗ tách, hai làn ngoài 0–1 chỉ nối vào hai làn bypass tương ứng; các làn còn lại chỉ nối vào đường chính. Trên đường chính, Bắc/Đông dùng làn 0–2 đi thẳng và 3–4 rẽ trái; Nam dùng 0–3 và 4–6; Tây dùng 0–1 và 2–3.

Các đoạn đón xe sau rẽ được mở rộng để xe có thể đổi làn hợp lệ và dàn sang các làn trống. Mỗi làn nguồn chỉ có một đường nối vào đoạn mở rộng theo đúng thứ tự làn; xe dàn làn sau khi vào đoạn đón, tránh nhiều đường nối chồng chéo xuất phát từ cùng một làn. Các vùng nhập dòng dùng nút zipper và chiều dài mô hình 30 m.

Đường dẫn mỗi hướng dùng trục thẳng và bề rộng đều trước điểm tách. Đường ra phía Bắc/Đông giữ 6 làn đến mép mô phỏng, bỏ các đoạn thu làn liên tiếp trong vùng nút. Đường ra phía Nam/Tây giữ 5 làn. Bề rộng ở mép mô phỏng là giả định để xe thoát mạng, chưa đối chiếu với số làn thực địa.

## Giới hạn

Cơ cấu xe: 80% xe máy, 17% ô tô, 3% xe buýt. Bước mô phỏng 0,1 giây, sublane 0,325 m. Mức chủ động vượt `lcSpeedGain` của xe máy, ô tô và xe buýt lần lượt là 2,0 / 1,0 / 0,5. Cấu hình dùng mức chấp nhận khe tiêu chuẩn thay cho mức quyết tâm tối đa.

Kiểm tra chẩn đoán thưa dùng đúng bước 0,1 giây và sublane 0,325 m của cấu hình chạy thực tế, với ba loại xe, đủ 12 tuyến và cả hai làn của từng bypass: 60/60 xe đến đích, không ghi nhận va chạm, teleport hoặc cảnh báo phanh khẩn cấp. Khi ép cả bốn đèn chính đỏ liên tục, kiểm tra chỉ rẽ phải có 36/36 xe đến đích, không va chạm hoặc teleport; bốn cảnh báo thiếu pha xanh là do cố ý giữ đèn đỏ. Các kiểm tra thưa này không thay thế kiểm tra tải đông.

Đèn chính chạy chu kỳ 64 giây, gồm hai lượt 23 giây xanh, 4 giây vàng, 5 giây đỏ toàn bộ. Pha xả xe giữa các nút lệch nhau 9 giây theo chiều lưu thông.

Medium, seed 42, kiểm tra đến 4.300 giây: 2.873/2.873 xe đến đích, không còn xe chạy/chờ, 0 va chạm, 0 teleport, 4 lần phanh gấp. Thời gian chờ trung bình 16,13 giây. Trong các đoạn nối nội bộ, xe giữ làn; trên đường dẫn và đoạn nhận xe vẫn được đổi làn. Teleport tắt.

Imbalance, seed 42, kiểm tra đến 7.300 giây: 12.747 xe đến đích, 113 xe còn trong mạng, 0 xe chờ nhập mạng, 0 teleport. Ghi nhận 8 va chạm và 33 lần phanh gấp. Lượt kiểm tra kết thúc khi kịch bản vẫn đang sinh xe.

Map chạy độc lập bằng SUMO; chưa tích hợp với controller TraCI/DRL của dự án. Bộ này không kèm dữ liệu nguồn hoặc script tái tạo mạng và lưu lượng.

Nguồn dữ liệu: © [OpenStreetMap contributors](https://www.openstreetmap.org/copyright), theo ODbL.
