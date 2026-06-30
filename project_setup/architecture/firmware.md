# ⚙️ Firmware Architecture
> **Cập nhật lần cuối:** 2026-06-30

> **Định danh & broker (D-020):** `device_id` dùng làm **khóa topic MQTT = MAC chip**, lấy từ eFuse
> (`esp_read_mac` trong `app_main.c`, format `%02x...` 12 hex) → ổn định qua erase-flash/OTA, mỗi board tự
> duy nhất, không cần provision. Backend nhận MAC rồi tự sinh `device_id` ngữ nghĩa (`esp32_eldercare_NN`)
> phía server. Broker URI = `#define CONFIG_MQTT_BROKER_URI` (default = broker org); có thể override bằng
> NVS key `config/mqtt_uri` (+`mqtt_user`/`mqtt_pass`) khi 1 build dùng nhiều org. `svc_cloud` publish
> `fw_version` (`esp_app_get_description()->version`) kèm `config/status` lúc connect/reconnect →
> backend auto-cập nhật `Device.firmware_version`. `CONFIG_DEVICE_ID` cũ đã deprecated.

## Tổng Quan Hệ Thống (System Overview)
Hệ thống firmware được xây dựng trên module **Seeed Studio XIAO ESP32-S3** (8MB PSRAM + 8MB Flash) nhằm mục tiêu giám sát vận động, đếm bước chân (HAR) và phát hiện té ngã (Post-Impact Fall Detection).
*   **Framework**: ESP-IDF v5.x native API.
*   **Ngôn ngữ**: C11 thuần (ngoại trừ TFLite Wrapper dùng C++).
*   **Vị trí đeo**: Thắt lưng phía trước. MPU6050 sử dụng tọa độ Body Frame (FLU).

## Cấu Trúc Thành Phần (Components)
Hệ thống áp dụng mô hình phân tách Service - Driver, quản lý các task độc lập qua FreeRTOS.
- `sys_manager`: Quản lý máy trạng thái hữu hạn (FSM) trung tâm (`STATE_INIT`, `STATE_CONNECTING`, `STATE_NORMAL`, `STATE_STREAMING`, `STATE_OTA`, `STATE_ERROR`) và phân phối sự kiện. Giữ thêm **cờ comms-critical** (`sys_manager_bump_comms_critical(ms)` / `sys_manager_is_comms_critical()`, monotonic expiry) để `svc_network` biết "đang trong cửa sổ confirm/alert, đừng rớt link" — xem [DECISIONS.md](DECISIONS.md) D-022. Khi bắt được `SYS_EVT_HARDWARE_ERROR`, hệ thống chuyển vào `STATE_ERROR` và kích hoạt hẹn giờ tự động reboot sau 10 giây để tự phục hồi.
- `svc_network`: Dịch vụ mạng vật lý — WiFi STA (dev) hoặc **4G LTE qua PPPoS** (production, dùng `esp_modem` + A7680C). **Auto-detect runtime bằng sniff bus UART** (không macro): nghe `UART_BREAK`/`UART_DATA` ~10s với pull-up RX + ngưỡng ≥5 event (chống false-positive); có hoạt động → có module → cellular, im → fallback WiFi (~11s). Đường 4G khóa **LTE-only (`AT+CNMP=38`)** với cờ NVS `lte_lock` để skip chu trình CFUN+10s ở các lần boot sau (**Boot Fast-path**). UART modem prio 9 + buffers (RX:16K, TX:2K) tránh **overrun**. Cả hai đường phát cùng event nên `svc_cloud` chạy MQTT độc lập. Đo RSSI 4G theo `rssi_interval` bằng cách thoát PPP (chỉ ở `STATE_NORMAL`, không trong cooldown). Lệnh `+++` thoát DATA mode **chỉ gửi khi sniff thấy byte PPP** (`saw_data` — nghi kẹt DATA sau warm-reboot); **không** `+++` khi bus im (tránh chờ ACK vô ích ~25s). Xem [DECISIONS.md](DECISIONS.md) D-026.
- `svc_cloud`: Dịch vụ đám mây, quản lý vòng đời MQTT Client, xử lý lệnh từ xa và định tuyến bản tin về backend. Có **MQTT Watchdog tự phục hồi 2 bậc**: nếu đứt MQTT lâu nhưng IP vẫn còn, tự động `stop/start` MQTT sau 60s và bắn `SYS_EVT_HARDWARE_ERROR` (để FSM flush NVS cache rồi tự reboot) sau 150s. Sau khi publish `alert/fall` → `sys_manager_bump_comms_critical(fall_cooldown)` (giữ link suốt cooldown).
- `svc_imu`: Dịch vụ chuyên trách đọc dữ liệu từ FIFO (MPU6050), áp dụng bộ lọc Kalman, gom batch 100Hz và RingBuffer Sliding Window. Tích hợp **pedometer** (`lib_pedometer`) đếm bước, và **impact detector** per-sample. Theo dõi lỗi I2C: nếu lỗi đọc FIFO liên tiếp quá 10 lần, bắn sự kiện `SYS_EVT_HARDWARE_ERROR`. Dịch vụ này đã được tối ưu CPU qua cơ chế **FSM Gating**: các tác vụ phân tích AI, đếm bước và va chạm chỉ chạy ở `STATE_NORMAL`. Ở `STATE_STREAMING`, nó bỏ qua inference và chỉ thu thập/scale batch raw lên MQTT.
- `svc_ai` / `tflite_wrapper`: Xử lý trượt cửa sổ dữ liệu, chạy inference mô hình TinyML INT8 ra phán đoán Fall. Hệ thống sử dụng 2 lớp Gating để lọc nhiễu: (1) **Pre-Impact Posture Gating**: Chặn ngay từ đầu nếu thiết bị nằm hoàn toàn nằm ngang (Roll < 45 độ) trong suốt 3 giây trước cú ngã (nhằm loại trừ Off-body False Alarm do vứt máy trên bàn rồi lỡ tay đập vào); (2) **Post-Impact Confirmation FSM** (`FALL_FSM_NORMAL`/`CONFIRMING`): Sau khi nhận ML Fall hợp lệ → CONFIRMING quan sát post-impact (`Idle`+ROLL=lying) đa số window trong `fall_confirm_window` giây (NVS `fall_cf`, default 4s) → CONFIRMED mới post `AI_EVT_FALL_DETECTED`; ABORT nếu hồi phục. Khi vào CONFIRMING → `sys_manager_bump_comms_critical()`. Xem [DECISIONS.md](DECISIONS.md) D-021.
- `drv_mpu6050`: Driver I2C (400kHz) điều khiển cảm biến MPU6050, thiết lập ngắt 100Hz tại chân GPIO 7.
- `drv_a7680c`: Driver điều khiển **nguồn** module 4G LTE A7680C qua chân PWRKEY (GPIO thuần, không ôm UART). UART/AT/PPP do `esp_modem` ở `svc_network` quản lý.
- `drv_battery`: Driver đọc % pin qua ADC oneshot + hệ số cầu phân áp (chân ở `hardware_config.h`). Sử dụng Median filter + EMA để chống nhiễu sụt áp, bảng tra (LUT) nội suy tuyến tính (3.0V - 4.2V), và thuật toán monotonic (chỉ giảm, không tăng đột biến khi dập tải).
- `lib_kalman`: Thư viện tính toán bộ lọc Kalman 1D để khử nhiễu góc Roll/Pitch.
- `lib_pedometer`: Thư viện thuần đếm bước (band-pass 0.5–3.5Hz + peak-detect ngưỡng động + trơ), platform-independent.

## Cơ Chế Giao Tiếp (Inter-Component Communication)
1. **System Event Loop (`esp_event`)**: 
   - Truyền tải tín hiệu điều khiển và trạng thái FSM giữa các modules (VD: `SYS_EVENT`, `NET_EVENT`, `CLOUD_EVENT`, `IMU_EVENT`, `AI_EVENT`). 
   - Tuyệt đối cấm gửi raw data mảng lớn qua Event Loop.
2. **FreeRTOS Message Queue / Callbacks (`xQueue`)**: 
   - Chuyên dùng để gửi mảng dữ liệu (Batch 50 mẫu, Sliding Window 400 mẫu) từ `svc_imu` sang `svc_cloud` (chế độ thu thập) hoặc `svc_ai` (chế độ inference) nhằm tiết kiệm PSRAM và CPU cycles.

## Tài Nguyên Cấp Phát (Memory Allocation)
- **PSRAM (`MALLOC_CAP_SPIRAM`)**: Phải được sử dụng cho TFLite Tensor Arena (100KB) và Sliding Window Buffer lớn để tránh cạn kiệt Internal SRAM.
- **Tối ưu ISR**: Hàm ngắt (ISR) luôn giữ cực ngắn, chỉ gọi `xQueueSendFromISR` hoặc `vTaskNotifyGiveFromISR`, mọi logic tính toán chuyển vào Task xử lý.

## Bảo mật MQTT (Security Status)

| Hạng mục | Trạng thái |
|---|---|
| Transport | **MQTTS** (`mqtts://`, port 8883) — TLS 1.2/1.3 qua mbedtls |
| Broker URI | `mqtts://mqtt.toolhub.app:8883` (khai báo tại `main/hardware_config.h`) |
| CA Cert | Let's Encrypt **E8 intermediate CA** — nhúng thẳng dưới dạng C string constant `CONFIG_MQTT_CA_CERT` trong `hardware_config.h` (hết hạn 2027-03-12) |
| Xác thực | Username/password truyền trong TLS tunnel (encrypted) |
| mbedtls | Dùng cho cả **TLS transport** (`broker.verification.certificate`) lẫn **base64 encode** payload |

**Luồng verify:** Device gửi TLS ClientHello → broker trả server cert (mqtt.toolhub.app) + E8 trong handshake → mbedtls verify chain: `server cert ← E8 (trusted anchor)` → kết nối thành công.
