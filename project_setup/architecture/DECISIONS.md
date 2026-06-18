# DECISIONS — Nhật ký quyết định thiết kế (ADR rút gọn)

> **Cập nhật lần cuối:** 2026-06-17
> Ghi "TẠI SAO" của các quyết định không hiển nhiên — để agent/người đọc khỏi tái suy luận (rất tốn). Mỗi mục: bối cảnh → quyết định → lý do. Mới nhất ở trên.

---

### D-012 · `set_fall_threshold` mirror `set_interval`; control command (start/stop) đi qua backend (B5)
- **Quyết định:** (1) Thêm chỉnh **ngưỡng phát hiện ngã** từ xa: cột `devices.fall_threshold` (float 0.6) + command `set_fall_threshold` (val 0.15–0.95), publish khi PUT `/devices/{id}` — **giống hệt pipeline `set_interval`**; device echo `fall_threshold` trong status để đồng bộ. (2) `start_stream`/`stop_stream` chuyển từ FE-publish-MQTT-thẳng sang `POST /devices/{id}/command` (backend authz org rồi publish).
- **Lý do:** Nhất quán một khuôn cấu hình (cột DB + command + echo status) cho mọi tham số áp xuống device. Đưa control command về backend → có authz/audit + bớt một đường client tự publish (bước đệm tiến tới M3, dù creds subscribe vẫn ở client nên chưa bịt hẳn). Range 0.15–0.95: dưới 0.15 quá nhạy (spam báo nhầm), trên 0.95 gần như không bao giờ kích.
- **UX:** FE dùng React Query `isPending` cho nút start/stop ("Đang gửi lệnh…") và chỉ vào trạng thái recording sau khi backend xác nhận — tránh "bấm xong không thấy gì".

### D-011 · FE realtime telemetry subscribe thẳng `status` (không tạo topic `telemetry`)
- **Bối cảnh:** FE từng subscribe `eldercare/+/telemetry` nhưng không hệ nào publish topic đó (firmware publish `status`, backend chỉ sub→ghi DB, không republish) → `useTelemetryStore` chết với thiết bị thật, chỉ "sống" ở mock.
- **Quyết định:** FE subscribe thẳng `eldercare/+/status` (topic firmware publish thật), map `battery`→`battery_pct`. KHÔNG thêm backend republish `status`→`telemetry`.
- **Lý do:** Ít tầng nhất (sửa 1 file FE, 0 đụng backend), đúng tinh thần "firmware/status là canonical". Đánh đổi: FE coupling nhẹ với schema status firmware (đã xử lý bằng fallback `battery_pct ?? battery`). Cùng lúc backend nhận thêm `walk_steps`/`run_steps` trong `StatusPayload` để tính distance đúng (0.415 vs 0.5 × height) thay vì dùng tổng `steps × 0.415` (sai cho người chạy).

### D-010 · Pedometer đặt ở svc_imu, gate theo HAR, đếm walk/run riêng
- **Quyết định:** `lib_pedometer` (band-pass 0.5–3.5Hz + peak-detect ngưỡng động + trơ); gọi per-sample trong `svc_imu`; chỉ đếm khi HAR=Walk/Run; tách `walk_steps`/`run_steps`; lưu NVS định kỳ.
- **Lý do:** HAR classifier đã có sẵn → gate loại gần hết false-positive mà pedometer truyền thống phải vật lộn. Đếm riêng walk/run để khớp công thức distance của backend (0.415 vs 0.5 × height). Per-sample cho độ phân giải đỉnh tốt; gán nhãn bằng `svc_ai_get_latest_prediction()` (trễ ≤0.5s, đủ vì gait đổi chậm). Band-pass ăn accel **thô** (không phải data Kalman làm mượt vốn làm cùn đỉnh).

### D-009 · 4G LTE qua PPPoS bằng esp_modem; drv_a7680c chỉ lo nguồn
- **Quyết định:** Dùng component `esp_modem` (UART+AT+PPP+netif); `drv_a7680c` chỉ điều khiển PWRKEY (Ton~50ms, Toff 2.5s). Switch WiFi(dev)/Cellular(prod) bằng macro.
- **Lý do:** esp_modem là component chính chủ Espressif, xử lý sẵn state machine PPP/LCP/IPCP → ít bug hơn tự viết. Tách lớp: driver thuần GPIO, service lo giao thức. MQTT/svc_cloud chạy trên 4G mà không cần sửa (PPP cấp IP routable).

### D-008 · Khóa LTE-only sớm (AT+CNMP=38) để chống sụt dòng
- **Quyết định:** Gửi `AT+CNMP=38` (LTE only) ngay sau AT sync, trước khi attach; kèm `CFUN=0→CNMP→CFUN=1`.
- **Lý do:** Phần cứng A7680C: quét GSM/2G gây xung dòng tức thời (dù đã có 3 tụ tantalum). `CNMP=38` là **AUTO_SAVE** (lưu NVRAM) → từ boot thứ 2 module vào thẳng LTE, không quét 2G. Đây là yêu cầu phần cứng cụ thể của dự án.

### D-007 · MQTT alert: firmware theo contract chung `alert/fall` (đã ĐẢO quyết định ban đầu)
- **Quyết định:** Firmware publish cảnh báo lên `eldercare/{id}/alert/fall`, payload khớp `AlertPayload` backend (`user_name`, `message`, `confidence`). Các topic status/imu_stream/command vốn đã khớp.
- **Lý do:** Ban đầu định lấy firmware làm canonical (`/alert`), nhưng phát hiện `tools/fake_device.py` + backend + frontend (3 hệ đã test với nhau) đều dùng `alert/fall`. Sửa 1 file firmware rẻ hơn sửa 3 hệ. Firmware thêm `confidence` (từ `svc_ai_get_latest_confidence()`) vì FE cần hiển thị.
- **Đã dọn (2026-06-17):** `AlertPayload` cho `user_name`/`message` optional; `fake_device.py` gửi đúng `{user_name,message,confidence}` (+ walk/run/rssi/interval ở status, xử lý `set_interval`); `handle_message` log `[MQTT][DROP]` thay vì nuốt.
- **Còn nợ:** firmware chưa publish `event` (backend có handler); firmware chưa gửi `rssi` (AT+CSQ) — backend đã sẵn đường ghi Influx khi payload có; cô lập đa tenant tầng MQTT (M3 — chờ quyết định hạ tầng).

### D-006 · Cooldown chống spam alert nằm ở svc_cloud (KHÔNG ở svc_ai)
- **Quyết định:** `FALL_COOLDOWN_US = 15s` cố định trong `svc_cloud.c`. `svc_ai` phát event mỗi lần phát hiện, không cooldown.
- **Lý do:** Tách trách nhiệm: svc_ai chỉ suy luận; chính sách phát/giới hạn alert thuộc tầng cloud. (Lưu ý: tài liệu cũ từng ghi nhầm cooldown ở svc_ai 10–20s — đã sửa.)

### D-005 · Streaming gửi data ĐÃ tiền xử lý (không phải raw)
- **Quyết định:** Ở STATE_STREAMING, batch gửi lên MQTT là data đã đổi hệ trục + Kalman + chuẩn hóa (scale int16), KHÔNG phải raw.
- **Lý do:** Tránh lệch phân phối train/serve — dataset thu thập phải đi qua đúng pipeline tiền xử lý như lúc inference thì model mới hoạt động đúng khi chạy thật.

### D-004 · Giao tiếp giữa service: event loop cho tín hiệu, queue/callback cho data lớn
- **Quyết định:** `svc_*` giao tiếp qua `esp_event` (loose coupling); mảng dữ liệu lớn (window/batch) đi qua FreeRTOS queue hoặc callback, KHÔNG qua event loop.
- **Lý do:** Tránh phụ thuộc vòng tròn khi build (CMake) và không nghẽn event loop bằng payload lớn; tiết kiệm PSRAM/CPU.

### D-003 · Tiền xử lý IMU: Kalman 1D 6 trục + chuẩn hóa [-1,1]; pitch riêng bằng Kalman 2-state
- **Quyết định:** Lọc Kalman 1D từng trục → chuẩn hóa [-1,1] làm input TinyML INT8. Pitch tính riêng bằng Kalman 2-state (góc+bias) để xác định tư thế.
- **Lý do:** Input model cần đồng nhất định dạng đã train (INT8 quantize). Pitch cần fusion accel+gyro chống trôi để phân biệt nằm/đứng/ngồi.

### D-002 · Sliding window 200 mẫu, trượt 50 — cố định
- **Quyết định:** `IMU_WINDOW_SIZE=200` (2s@100Hz), trượt `IMU_BATCH_SIZE=50` (0.5s).
- **Lý do:** Là kích thước input cố định model đã train — **không đổi mà không retrain**.

### D-001 · PCNT đếm xung INT để gom batch IMU (chống sụt dòng + tiết kiệm điện)
- **Quyết định:** Nối chân INT MPU6050 vào ngoại vi PCNT; chỉ ngắt CPU mỗi 50 xung (0.5s).
- **Lý do:** MPU6050 **không có** ngắt theo ngưỡng FIFO (chỉ data-ready từng mẫu / FIFO-full), và I2C của ESP32-S3 **không có DMA** → nếu không gom, CPU phải thức 100 lần/giây. PCNT "tự chế" ra ngắt gom-lô bằng phần cứng → CPU thức 2 lần/giây. Đây là sáng kiến cốt lõi của firmware.
