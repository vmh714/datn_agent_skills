# ⚙️ Firmware Architecture
> **Cập nhật lần cuối:** 2026-06-22

## Tổng Quan Hệ Thống (System Overview)
Hệ thống firmware được xây dựng trên module **Seeed Studio XIAO ESP32-S3** (8MB PSRAM + 8MB Flash) nhằm mục tiêu giám sát vận động, đếm bước chân (HAR) và phát hiện té ngã (Post-Impact Fall Detection).
*   **Framework**: ESP-IDF v5.x native API.
*   **Ngôn ngữ**: C11 thuần (ngoại trừ TFLite Wrapper dùng C++).
*   **Vị trí đeo**: Thắt lưng phía trước. MPU6050 sử dụng tọa độ Body Frame (FLU).

## Cấu Trúc Thành Phần (Components)
Hệ thống áp dụng mô hình phân tách Service - Driver, quản lý các task độc lập qua FreeRTOS.
- `sys_manager`: Quản lý máy trạng thái hữu hạn (FSM) trung tâm (`STATE_INIT`, `STATE_CONNECTING`, `STATE_NORMAL`, `STATE_STREAMING`, `STATE_OTA`, v.v.) và phân phối sự kiện.
- `svc_network`: Dịch vụ mạng vật lý — WiFi STA (dev) hoặc **4G LTE qua PPPoS** (production, dùng `esp_modem` + A7680C). Chọn đường mạng bằng macro `NETWORK_USE_CELLULAR` trong `hardware_config.h`. Đường 4G khóa **LTE-only (`AT+CNMP=38`)** để tránh quét 2G gây sụt dòng. Cả hai đường phát cùng event (`NET_EVT_WIFI_CONNECTED`/`NET_EVT_CELLULAR_CONNECTED`) nên `svc_cloud` chạy MQTT trên 4G mà không cần sửa.
- `svc_cloud`: Dịch vụ đám mây, quản lý vòng đời MQTT Client, xử lý lệnh từ xa và định tuyến bản tin về backend.
- `svc_imu`: Dịch vụ chuyên trách đọc dữ liệu từ FIFO (MPU6050), áp dụng bộ lọc Kalman, gom batch 100Hz và RingBuffer Sliding Window. Tích hợp **pedometer** (`lib_pedometer`) đếm bước per-sample, gate theo HAR (Walk/Run) và lưu NVS.
- `svc_ai` / `tflite_wrapper`: Xử lý trượt cửa sổ dữ liệu, chạy inference mô hình học máy lượng tử hóa (Edge AI / TinyML) để đưa ra phán đoán Fall.
- `drv_mpu6050`: Driver I2C (400kHz) điều khiển cảm biến MPU6050, thiết lập ngắt 100Hz tại chân GPIO 7.
- `drv_a7680c`: Driver điều khiển **nguồn** module 4G LTE A7680C qua chân PWRKEY (GPIO thuần, không ôm UART). UART/AT/PPP do `esp_modem` ở `svc_network` quản lý.
- `drv_battery`: Driver đọc % pin qua ADC oneshot + hệ số cầu phân áp (chân ở `hardware_config.h`).
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
