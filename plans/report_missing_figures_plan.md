# Danh sách hình minh họa CÒN THIẾU trong luận văn

> Mục tiêu: liệt kê các phần đang trình bày **bằng chữ** nhưng **chưa có hình** — để bổ sung cho đẹp & dễ hiểu.
> Phân loại theo cách tạo: 🖐️ **Vẽ tay / sơ đồ** (TikZ, draw.io, vẽ tay) · 📊 **Sinh từ dữ liệu** (matplotlib — phối hợp agent AI) · 📷 **Chụp màn hình / ảnh thật**.
> Các hình ĐÃ CÓ và ổn (không cần làm lại): `sync.png` (5235×3720), `pppos_stack.png` (1743×1355, 160dpi), `mqtt_architechture.png` (2840×1052, 160dpi), `erd.png` (1081×943, tạm ổn) + ảnh phần cứng/sản phẩm thương mại.
> ⚠️ Hình CÓ SẴN nhưng **quá nhỏ, cần làm lại**: `arch.png` (738×781px) · `fsm.png` (704×486px) — xem mục D.

---

## A. 🖐️ Sơ đồ khái niệm cần vẽ (ưu tiên — đây là phần "vẽ tay cho đẹp")

| # | Mục trong luận văn | Hình cần vẽ — nội dung | Ưu tiên |
|---|---|---|---|
| ~~A1~~ | ~~**§3.3.1** Depthwise Separable 1D CNN~~ | ~~**Phân rã tích chập tách kênh**: so sánh Standard Conv vs (Depthwise theo từng kênh) + (Pointwise 1×1 trộn kênh). Minh họa vì sao giảm phép tính. Khái niệm cốt lõi, hiện chỉ có chữ.~~ | ✅ Xong (đã vẽ TikZ) |
| ~~A2~~ | ~~**§3.3.1 / §4.2.5 / §5.2** Kiến trúc v30_optimize~~ | ~~**Sơ đồ khối kiến trúc** Input(200×6) → Stem(Conv1D s2) → Block1/2/3(SepConv+MaxPool) → Head **GAP∥GMP∥Flatten** → Concat → Dense(5). Hiện mới chỉ có **bảng** `tab:v30opt_architecture`; cần hình khối trực quan (đây là đóng góp trung tâm).~~ | ✅ Xong (đã vẽ TikZ) |
| ~~A3~~ | ~~**§4.2.3 / §5.1** Chiến lược cắt cửa sổ theo sự kiện~~ | ~~**Minh họa 3 cách windowing**: Fall căn theo đỉnh SVM gia tốc; Trans căn theo sự kiện RMS-gyro (>20 dps); Walk/Run sliding window. Đóng góp quan trọng, hiện chỉ mô tả chữ.~~ | ✅ Xong (`har_windows.png`) |
| A4 | **§3.4.3** Stack suy luận nhúng | **Sơ đồ chồng 3 lớp**: `.tflite`/LiteRT (FlatBuffer) → TFLM (tensor arena tĩnh + MicroMutableOpResolver) → ESP-NN kernels (SIMD Xtensa). Có bảng ops nhưng thiếu sơ đồ stack. | ⭐⭐ |
| A5 | **§3.4.2** Pipeline TinyML đầu–cuối | **Sơ đồ luồng**: raw `.txt` → tiền xử lý → windowing → cache `.npy` → train (TF/Keras) → quantize INT8 (TFLite) → `model_data.cc` → firmware. Hiện là itemize. | ⭐⭐ |
| A6 | **§4.1.2** Kiến trúc phần mềm firmware | **Sơ đồ phân lớp/gói (package)**: App (`app_main`, `sys_manager`) / Service (`svc_imu`, `svc_ai`, `svc_network`, `svc_cloud`) / Driver (`drv_*`, `lib_*`), kèm chiều phụ thuộc. Template yêu cầu package diagram; mới chỉ có FSM. | ⭐⭐ |
| A7 | **§5.3** Lấy mẫu PCNT vs vTaskDelay | **Giản đồ thời gian (timing)**: chuỗi mẫu bị jitter khi dùng `vTaskDelay` (lệch vài ms khi bận) so với PCNT ngắt phần cứng đều tăm tắp (<1µs). Minh họa lập luận chính của đóng góp 3. | ⭐⭐ |
| A8 | **§5.2 / §4.2.4** Hành trình tối ưu kiến trúc | **Cây/timeline tiến hóa**: v1(CNN-LSTM) → v8–22(TCN) → v25(ResNet+SE) → v30(CNN) → **v30_optimize**, đánh dấu nhánh bị loại (TCN >2s, SE/sigmoid…). Trực quan hóa bảng `tab:model_evolution`. | ⭐ |
| A9 | **§3.3.2** Lượng tử hóa INT8 | Minh họa ánh xạ **Float32 → INT8** (dải giá trị, scale & zero-point), kèm ý "giảm 4× bộ nhớ". | ⭐ |
| ~~A10~~ | ~~**§3.1.1–3.1.2** HAR & phát hiện ngã~~ | ~~Khái niệm **cửa sổ trượt trên dòng IMU** + đỉnh va chạm khi ngã (có thể gộp/đặt trước A3).~~ | ✅ Xong (`fall_phases.png`) |
| ~~A11~~ | ~~**§4.1 (use case mới) / §4.2** Tự động đăng ký thiết bị~~ | ~~**Sơ đồ tuần tự (sequence) Auto-provisioning theo MAC (D-020)**: Device boot → đọc MAC eFuse → kết nối MQTT(4G) → publish `config/status` (mac + fw_version) → Backend `mqtt_service` gặp MAC lạ → `_get_or_create_device_by_mac` sinh `esp32_eldercare_NN` + lưu mac → thiết bị tự hiện trên Dashboard → Nhân viên y tế chỉ gán wearer. Đây là pipeline "zero-touch" hiện CHƯA có hình/use case.~~ | ✅ Xong (đã vẽ TikZ) |
| ~~A12~~ | ~~**§3.x / §4.2** Phát hiện ngã 2 pha (D-021)~~ | ~~**Sơ đồ FSM phụ `svc_ai`**: NORMAL →(ML Fall)→ CONFIRMING →(đa số Idle+lying trong N giây)→ CONFIRMED→alert; ABORT nếu hồi phục. (Thay/bổ sung cho `fsm.png` mục D2.)~~ | ✅ Xong (đã vẽ TikZ) |

## B. 📊 Hình sinh từ dữ liệu (KHÔNG vẽ tay — chạy script, phối hợp agent AI)

| # | Mục | Hình | Ghi chú |
|---|---|---|---|
| ~~B1~~ | ~~§4.3.1~~ | ~~**Confusion matrix** của v30_optimize trên tập test~~ | ~~✅ Xong (đã có ma trận nhầm lẫn 2x2)~~ |
| ~~B2~~ | ~~§4.3.2~~ | ~~**Biểu đồ cột** latency & kích thước INT8 các họ kiến trúc~~ | ~~✅ Xong (đã có biểu đồ so sánh)~~ |
| B3 | §4.2.1 | **Tín hiệu Kalman trước/sau** (Roll/Pitch) | Minh họa khử nhiễu, hiện thuần chữ |
| B4 | §5.1 | **Ví dụ tín hiệu Idle vs Trans** (SVM gia tốc + RMS gyro) | Minh họa peak-detection gán nhãn |

## C. 📷 Ảnh chụp / ảnh thật (KHÔNG vẽ tay — chụp)

| # | Mục | Ảnh | Ghi chú |
|---|---|---|---|
| ~~C1~~ | ~~§4.1.2 hoặc §4.3~~ | ~~**Thiết bị thật** (mạch lắp ráp + đeo lên người/thắt lưng)~~ | ✅ Xong (Chèn trong Chương 5) |
| C2 | §4.2 (Frontend) | **Screenshot Dashboard** giám sát đa thiết bị | "Minh họa chức năng chính" — hiện chưa có ảnh giao diện nào |
| C3 | §4.2 (Frontend) | **Screenshot Overlay cảnh báo ngã** toàn màn hình | Minh họa `FallDetectionOverlay` |
| C4 | §4.2 (Frontend) | **Screenshot trang cấu hình** (slider ngưỡng ngã) + **trang thu thập IMU** (biểu đồ Accel/Gyro) | |
| C5 | §3.6 (tùy chọn) | Screenshot Swagger API (đã có placeholder comment trong §3.6) | Thấp |

---

## C. 📷 Ảnh chụp / ảnh thật — bổ sung từ Ch.3 (commented-out)

| # | File cần tạo | Mục | Nội dung | Ưu tiên |
|---|---|---|---|---|
| C5 | `dual_database.png` | §3.6 Ch.3 | Sơ đồ kiến trúc **Cơ sở dữ liệu kép**: InfluxDB (time-series) + PostgreSQL (metadata) — mối quan hệ, luồng write/query | ⭐⭐⭐ |
| ~~C6~~ | ~~`fastapi_swagger.png`~~ | ~~§3.6 Ch.3~~ | ~~**Screenshot** giao diện Swagger UI tự sinh từ FastAPI (chạy backend, vào `/docs`, chụp)~~ | ✅ Xong |
| C7 | `nextjs_architecture.png` | §3.6 Ch.3 | Sơ đồ cơ chế **Server-Side Rendering (SSR)** trong Next.js (Request → Server → HTML → Hydrate) | ⭐ |

> 3 hình trên hiện đang **commented-out** trong `3_Cong_nghe.tex` dòng 227–262, chờ file ảnh.

---

## D. 🔄 Hình có sẵn cần làm lại (chất lượng thấp) -> ✅ ĐÃ HOÀN THÀNH

| # | File hiện có | Kích thước | Vấn đề | Cách xử lý |
|---|---|---|---|---|
| ~~D1~~ | ~~`arch.png`~~ | ~~Mới vẽ lại~~ | ~~Đã giải quyết~~ | ✅ **Xong** (đã có `arch.png` nét căng) |
| ~~D2~~ | ~~`fsm.png`~~ | ~~Mới vẽ lại~~ | ~~Đã giải quyết~~ | ✅ **Xong** (đã có `fsm.png` nét căng) |

> Đã có file nét lưu đè lên tên cũ (file mờ được đổi tên thành `*-old.png`). Hạng mục này đã xong hoàn toàn.

---

## E. 📷 Screenshot Frontend (FE đã chạy ngon → chụp ngay)

> Thay thế & mở rộng C2–C4 ở trên (đó là bản liệt kê sơ khai). Đây là checklist chuẩn theo các trang FE thực có.
> **Mẹo chụp:** light mode, full-HD, ẩn/giả tên bệnh nhân (PII). Tạo dữ liệu sống bằng `tools/fake_device.py` (1-2 thiết bị online + 1 cảnh báo) để E1/E2/E8 có nội dung.

| # | Trang (route) | Ảnh chụp & điểm cần lộ ra | Minh họa cho | Ưu tiên |
|---|---|---|---|---|
| ~~E1~~ | ~~`/` Dashboard~~ | ~~Lưới giám sát đa thiết bị: card pin/online, bước chân realtime, banner cảnh báo~~ | ~~§4.2/§5.6 — chức năng chính, giám sát realtime~~ | ✅ Xong |
| ~~E2~~ | ~~`/` (overlay)~~ | ~~**Overlay cảnh báo ngã** toàn màn hình: tên, thời gian, **confidence**, nút "Đã xử lý"~~ | ~~§4.1 (activity ngã), §5.6 — Hybrid Alert Sync~~ | ✅ Xong |
| E3 | `/device/{id}/settings` | **Trang cấu hình** — chụp đủ các card: chu kỳ telemetry, slider `fall_threshold`, `fall_cooldown`, **`fall_confirm_window` (D-021)**, **`rssi_interval` có "Tắt" (D-022)** | §5.6 + §2.4 cấu hình từ xa + 2 feature mới | ⭐⭐⭐ |
| ~~E4~~ | ~~`/devices`~~ | ~~**Bảng thiết bị auto-provisioned**: `esp32_eldercare_NN` + MAC + firmware (read-only), KHÔNG có nút "Đăng ký tay"~~ | ~~**D-020 auto-provision** (ghép với sơ đồ A11)~~ | ✅ Xong |
| ~~E5~~ | ~~`/device/{id}/history`~~ | ~~Biểu đồ **bậc thang trạng thái** + marker ngã đỏ + timeline log sự kiện~~ | ~~§5.6 — phân loại HAR + nhật ký~~ | ✅ Xong |
| ~~E6~~ | ~~`/device/{id}/vitals`~~ | ~~Biểu đồ **Pin + RSSI 4G** theo thời gian~~ | ~~**D-022 RSSI** + theo dõi sức khỏe thiết bị~~ | ✅ Xong |
| ~~E7~~ | ~~`/data-collection`~~ | ~~Biểu đồ Accel/Gyro realtime + chọn người đeo + mã activity SisFall~~ | ~~§5.x — thu data verify (D-017)~~ | ✅ Xong |
| ~~E8~~ | ~~`/alerts`~~ | ~~Bảng lịch sử cảnh báo + lọc theo wearer + nút Resolve~~ | ~~§5.6 — quản lý/giải quyết cảnh báo (D-016)~~ | ✅ Xong |
| E9 | `/device/{id}/telemetry` | Bảng log telemetry thô (pin, bước, AI pred/conf) | §5.6 — minh họa dữ liệu thô | ⭐ |
| ~~E10~~| ~~`/wearers`~~ | ~~CRUD hồ sơ bệnh nhân (full_name, height_cm)~~ | ~~§5.6 — quản lý bệnh nhân~~ | ✅ Xong |

> Login (`/login`) thường KHÔNG cần đưa vào báo cáo. Swagger backend = C6 (mục riêng).

## F. 📌 Cập nhật USE CASE (không phải hình — nhưng liên quan, làm cùng lúc)

Sau D-020, **đăng ký thiết bị đã thành tự động (zero-touch)** nhưng chương use case (`4_1_Phan_tich_yeu_cau.tex`) chưa phản ánh:
- **uc2 "Quản lý thiết bị"** trong sơ đồ tổng quát (`fig:use_case_tongquat`) chỉ nối *Nhân viên y tế* → cần thêm liên kết tới actor **Thiết bị giám sát** (thiết bị TỰ đăng ký), vì khâu tạo `device_id` là do device+backend, không phải người nhập tay.
- Thêm **1 use case phân rã "Tự động đăng ký thiết bị (Auto-provisioning)"** (mục mới sau `subsection:2.2.x`) + dùng **sơ đồ A11** (sequence). Nhấn: nhân viên KHÔNG nhập `device_id`/firmware; chỉ cắm nguồn là thiết bị tự lên dashboard, người dùng chỉ gán wearer.
- Cân nhắc thêm **1 bảng Đặc tả Use case** cho auto-provision ở §2.3 (actor = Thiết bị; tiền điều kiện = có org/broker; hậu điều kiện = device_id ngữ nghĩa sinh ra + firmware_version tự báo).
- ⚠️ Rà nhẹ: §2.2.4 "Gán thiết bị" ghi *"nhập chiều cao bệnh nhân"* tại bước gán — thực tế chiều cao thuộc hồ sơ wearer (CRUD riêng, D-016). Sửa cho khớp (chiều cao lấy từ hồ sơ wearer, không nhập lúc gán).
- ✅ §2.4 NFR đã thêm "Độ tin cậy cảnh báo" + "Khả năng cấu hình từ xa" (model rẻ đã làm) — khớp D-021/D-022.

## Ghi chú thực hiện
- Nhóm **A**: dùng Lucidchart/draw.io → xuất **PDF** (vector), hoặc báo để dựng bằng **TikZ** trong LaTeX.
- Nhóm **C5** (`dual_database`): sơ đồ khái niệm → dùng Lucidchart/TikZ; **C6** (`fastapi_swagger`): chụp màn hình app đang chạy.
- Nhóm **D**: ưu tiên làm lại — hiện đang gây mờ ảnh trong PDF.
- Sau khi có file ảnh, đặt vào `REPORT/Do_an_tot_nghiep_Vu_Manh_Hung/Hinhve/` và chèn `\begin{figure}...\includegraphics...\caption...\label` vào đúng mục — phần khung này có thể nhờ tôi chèn sẵn.
- Nhóm **B** cần số liệu thật → phối hợp agent AI (vùng TinyML).
