# Danh sách hình minh họa CÒN THIẾU trong luận văn

> Mục tiêu: liệt kê các phần đang trình bày **bằng chữ** nhưng **chưa có hình** — để bổ sung cho đẹp & dễ hiểu.
> Phân loại theo cách tạo: 🖐️ **Vẽ tay / sơ đồ** (TikZ, draw.io, vẽ tay) · 📊 **Sinh từ dữ liệu** (matplotlib — phối hợp agent AI) · 📷 **Chụp màn hình / ảnh thật**.
> Các hình ĐÃ CÓ và ổn (không cần làm lại): `sync.png` (5235×3720), `pppos_stack.png` (1743×1355, 160dpi), `mqtt_architechture.png` (2840×1052, 160dpi), `erd.png` (1081×943, tạm ổn) + ảnh phần cứng/sản phẩm thương mại.
> ⚠️ Hình CÓ SẴN nhưng **quá nhỏ, cần làm lại**: `arch.png` (738×781px) · `fsm.png` (704×486px) — xem mục D.

---

## A. 🖐️ Sơ đồ khái niệm cần vẽ (ưu tiên — đây là phần "vẽ tay cho đẹp")

| # | Mục trong luận văn | Hình cần vẽ — nội dung | Ưu tiên |
|---|---|---|---|
| A1 | **§3.3.1** Depthwise Separable 1D CNN | **Phân rã tích chập tách kênh**: so sánh Standard Conv vs (Depthwise theo từng kênh) + (Pointwise 1×1 trộn kênh). Minh họa vì sao giảm phép tính. Khái niệm cốt lõi, hiện chỉ có chữ. | ⭐⭐⭐ |
| A2 | **§3.3.1 / §4.2.5 / §5.2** Kiến trúc v30_optimize | **Sơ đồ khối kiến trúc** Input(200×6) → Stem(Conv1D s2) → Block1/2/3(SepConv+MaxPool) → Head **GAP∥GMP∥Flatten** → Concat → Dense(5). Hiện mới chỉ có **bảng** `tab:v30opt_architecture`; cần hình khối trực quan (đây là đóng góp trung tâm). | ⭐⭐⭐ |
| A3 | **§4.2.3 / §5.1** Chiến lược cắt cửa sổ theo sự kiện | **Minh họa 3 cách windowing**: Fall căn theo đỉnh SVM gia tốc; Trans căn theo sự kiện RMS-gyro (>20 dps); Walk/Run sliding window. Đóng góp quan trọng, hiện chỉ mô tả chữ. | ⭐⭐⭐ |
| A4 | **§3.4.3** Stack suy luận nhúng | **Sơ đồ chồng 3 lớp**: `.tflite`/LiteRT (FlatBuffer) → TFLM (tensor arena tĩnh + MicroMutableOpResolver) → ESP-NN kernels (SIMD Xtensa). Có bảng ops nhưng thiếu sơ đồ stack. | ⭐⭐ |
| A5 | **§3.4.2** Pipeline TinyML đầu–cuối | **Sơ đồ luồng**: raw `.txt` → tiền xử lý → windowing → cache `.npy` → train (TF/Keras) → quantize INT8 (TFLite) → `model_data.cc` → firmware. Hiện là itemize. | ⭐⭐ |
| A6 | **§4.1.2** Kiến trúc phần mềm firmware | **Sơ đồ phân lớp/gói (package)**: App (`app_main`, `sys_manager`) / Service (`svc_imu`, `svc_ai`, `svc_network`, `svc_cloud`) / Driver (`drv_*`, `lib_*`), kèm chiều phụ thuộc. Template yêu cầu package diagram; mới chỉ có FSM. | ⭐⭐ |
| A7 | **§5.3** Lấy mẫu PCNT vs vTaskDelay | **Giản đồ thời gian (timing)**: chuỗi mẫu bị jitter khi dùng `vTaskDelay` (lệch vài ms khi bận) so với PCNT ngắt phần cứng đều tăm tắp (<1µs). Minh họa lập luận chính của đóng góp 3. | ⭐⭐ |
| A8 | **§5.2 / §4.2.4** Hành trình tối ưu kiến trúc | **Cây/timeline tiến hóa**: v1(CNN-LSTM) → v8–22(TCN) → v25(ResNet+SE) → v30(CNN) → **v30_optimize**, đánh dấu nhánh bị loại (TCN >2s, SE/sigmoid…). Trực quan hóa bảng `tab:model_evolution`. | ⭐ |
| A9 | **§3.3.2** Lượng tử hóa INT8 | Minh họa ánh xạ **Float32 → INT8** (dải giá trị, scale & zero-point), kèm ý "giảm 4× bộ nhớ". | ⭐ |
| A10 | **§3.1.1–3.1.2** HAR & phát hiện ngã | Khái niệm **cửa sổ trượt trên dòng IMU** + đỉnh va chạm khi ngã (có thể gộp/đặt trước A3). | ⭐ |

## B. 📊 Hình sinh từ dữ liệu (KHÔNG vẽ tay — chạy script, phối hợp agent AI)

| # | Mục | Hình | Ghi chú |
|---|---|---|---|
| B1 | §4.3.1 | **Confusion matrix** của v30_optimize trên tập test | Có sẵn `confusion_matrix_*.png` trong repo train |
| B2 | §4.3.2 | **Biểu đồ cột** latency & kích thước INT8 các họ kiến trúc | Trực quan hóa bảng `tab:mcu_arch_compare` |
| B3 | §4.2.1 | **Tín hiệu Kalman trước/sau** (Roll/Pitch) | Minh họa khử nhiễu, hiện thuần chữ |
| B4 | §5.1 | **Ví dụ tín hiệu Idle vs Trans** (SVM gia tốc + RMS gyro) | Minh họa peak-detection gán nhãn |

## C. 📷 Ảnh chụp / ảnh thật (KHÔNG vẽ tay — chụp)

| # | Mục | Ảnh | Ghi chú |
|---|---|---|---|
| C1 | §4.1.2 hoặc §4.3 | **Thiết bị thật** (mạch lắp ráp + đeo lên người/thắt lưng) | Bắt buộc nên có với đồ án phần cứng |
| C2 | §4.2 (Frontend) | **Screenshot Dashboard** giám sát đa thiết bị | "Minh họa chức năng chính" — hiện chưa có ảnh giao diện nào |
| C3 | §4.2 (Frontend) | **Screenshot Overlay cảnh báo ngã** toàn màn hình | Minh họa `FallDetectionOverlay` |
| C4 | §4.2 (Frontend) | **Screenshot trang cấu hình** (slider ngưỡng ngã) + **trang thu thập IMU** (biểu đồ Accel/Gyro) | |
| C5 | §3.6 (tùy chọn) | Screenshot Swagger API (đã có placeholder comment trong §3.6) | Thấp |

---

## C. 📷 Ảnh chụp / ảnh thật — bổ sung từ Ch.3 (commented-out)

| # | File cần tạo | Mục | Nội dung | Ưu tiên |
|---|---|---|---|---|
| C5 | `dual_database.png` | §3.6 Ch.3 | Sơ đồ kiến trúc **Cơ sở dữ liệu kép**: InfluxDB (time-series) + PostgreSQL (metadata) — mối quan hệ, luồng write/query | ⭐⭐⭐ |
| C6 | `fastapi_swagger.png` | §3.6 Ch.3 | **Screenshot** giao diện Swagger UI tự sinh từ FastAPI (chạy backend, vào `/docs`, chụp) | ⭐⭐ |
| C7 | `nextjs_architecture.png` | §3.6 Ch.3 | Sơ đồ cơ chế **Server-Side Rendering (SSR)** trong Next.js (Request → Server → HTML → Hydrate) | ⭐ |

> 3 hình trên hiện đang **commented-out** trong `3_Cong_nghe.tex` dòng 227–262, chờ file ảnh.

---

## D. 🔄 Hình có sẵn cần làm lại (chất lượng thấp)

| # | File hiện có | Kích thước | Vấn đề | Cách xử lý |
|---|---|---|---|---|
| D1 | `arch.png` | 738×781 px | Quá nhỏ — mờ khi xem PDF zoom | Vẽ lại bằng **TikZ** hoặc re-export từ file gốc (PDF vector) |
| D2 | `fsm.png` | 704×486 px | Quá nhỏ — mờ khi xem PDF zoom | Vẽ lại bằng **TikZ** hoặc re-export từ file gốc (PDF vector) |

> Nếu còn file gốc (draw.io, Lucidchart…) → re-export PDF là nhanh nhất. Nếu không còn → TikZ.

---

## Ghi chú thực hiện
- Nhóm **A**: dùng Lucidchart/draw.io → xuất **PDF** (vector), hoặc báo để dựng bằng **TikZ** trong LaTeX.
- Nhóm **C5** (`dual_database`): sơ đồ khái niệm → dùng Lucidchart/TikZ; **C6** (`fastapi_swagger`): chụp màn hình app đang chạy.
- Nhóm **D**: ưu tiên làm lại — hiện đang gây mờ ảnh trong PDF.
- Sau khi có file ảnh, đặt vào `REPORT/Do_an_tot_nghiep_Vu_Manh_Hung/Hinhve/` và chèn `\begin{figure}...\includegraphics...\caption...\label` vào đúng mục — phần khung này có thể nhờ tôi chèn sẵn.
- Nhóm **B** cần số liệu thật → phối hợp agent AI (vùng TinyML).
