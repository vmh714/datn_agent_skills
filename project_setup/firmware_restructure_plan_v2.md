# KẾ HOẠCH TÁI CẤU TRÚC FIRMWARE (V2) - EVENT-DRIVEN & FSM

Tài liệu này là bản kế hoạch từng bước (Step-by-step roadmap) để chuyển đổi cấu trúc Firmware cũ sang kiến trúc hướng sự kiện (Event-driven) sử dụng Máy trạng thái (FSM) trung tâm. Lộ trình này bao phủ toàn bộ vòng đời thiết bị, từ lúc thu thập Data (Phase 1) đến lúc chạy Edge AI (Phase 2).

## I. NGUYÊN TẮC BẤT DI BẤT DỊCH (CORE RULES)
1. **One-time Init:** Tất cả các Tasks (`svc_imu`, `svc_network`, `svc_cloud`, `svc_ai`) chỉ được gọi `xTaskCreate()` đúng một lần tại `app_main()`.
2. **State-aware Logic:** Trong vòng lặp `while(1)` của mỗi Task, bắt buộc phải check `sys_manager_get_state()` trước khi xử lý logic nặng.
3. **Fire & Forget:** Các component giao tiếp 100% thông qua `esp_event` hoặc FreeRTOS Queue. Không component nào được gọi hàm trực tiếp của component khác (trừ thư viện toán học/driver).
4. **Static Allocation:** Tuyệt đối không dùng `malloc/free` bên trong các ngắt (ISR) hoặc vòng lặp vô tận. Data buffer (Sliding Window, Batch) phải được cấp phát tĩnh.

---

## II. LỘ TRÌNH TRIỂN KHAI (IMPLEMENTATION PHASES)

### Phase 1: Xây dựng Bộ não trung tâm (FSM Skeleton)
**Mục tiêu:** Tạo ra `sys_manager` quản lý State và Event Loop. Không chạy logic nghiệp vụ.
- **Task 1.1:** Cập nhật `sys_manager.h`: Định nghĩa các State (`STATE_INIT`, `STATE_CONNECTING`, `STATE_NORMAL`, `STATE_STREAMING`, `STATE_OTA`, `STATE_ERROR`).
- **Task 1.2:** Định nghĩa các Event Base: `SYS_EVENT`, `NET_EVENT`, `CLOUD_EVENT`, `IMU_EVENT`, `AI_EVENT`.
- **Task 1.3:** Dọn dẹp `app_main.c`: Chỉ khởi tạo NVS, Netif, gọi `sys_manager_init()` và gọi lệnh khởi tạo (Init) cho các Service. Xóa bỏ mọi hàm `vTaskDelay` block luồng main.

### Phase 2: Phân tách Hạ tầng Mạng & MQTT (Connectivity)
**Mục tiêu:** Tách `wifi_mqtt_service` cũ thành 2 service độc lập `svc_network` và `svc_cloud`.
- **Task 2.1 - `svc_network`:** Chịu trách nhiệm kết nối Mạng (Tạm thời test bằng WiFi). Trạng thái hiện tại là `STATE_CONNECTING`. Khi kết nối thành công -> post sự kiện `NET_EVT_WIFI_CONNECTED`.
- **Task 2.2 - `svc_cloud`:** Task này chỉ thức dậy thực hiện kết nối MQTT Broker khi bắt được sự kiện `NET_EVT_WIFI_CONNECTED`.
- **Task 2.3:** Subscribe MQTT vào Topic `v1/devices/{device_id}/cmd`. Viết hàm parse JSON lệnh điều khiển đổi State.
- **Task 2.4:** Khi MQTT kết nối thành công, `svc_cloud` post sự kiện báo FSM chuyển sang `STATE_NORMAL`.

### Phase 3: Luồng thu thập dữ liệu IMU (Data Collection)
**Mục tiêu:** Thu thập dữ liệu IMU thô (Raw Data 100Hz) chuyển về Backend để train TinyML.
- **Task 3.1 - `drv_mpu6050`:** Đảm bảo hàm cấu hình MPU6050 sử dụng FIFO và Interrupt pin (GPIO 11) kích hoạt đúng 100Hz.
- **Task 3.2 - `svc_imu`:** Khởi tạo Static Array (Batch Buffer) cỡ 50 mẫu. Trong Task IMU (được wake up bởi ngắt), nhét data vào Buffer.
- **Task 3.3:** Nếu hệ thống đang ở `STATE_STREAMING` và Buffer đầy (50 mẫu), post sự kiện `IMU_EVT_BATCH_READY` kèm con trỏ tới Buffer.
- **Task 3.4 - `svc_cloud`:** Bắt sự kiện `BATCH_READY`, mã hóa buffer này bằng mbedtls Base64, bọc vào JSON và Publish lên topic `v1/devices/{device_id}/imu_stream`.

### Phase 4: Tích hợp Edge AI & Alert (Production Mode)
**Mục tiêu:** Thiết bị tự nhận diện hành vi (HAR) và ngã bằng mô hình 1D-CNN + LSTM/GRU mà không cần gửi Raw Data.
- **Task 4.1 - Sliding Window:** Nâng cấp `svc_imu` để duy trì một RingBuffer tĩnh lớn (400-500 mẫu = 4-5 giây). Mỗi 0.5s trượt dữ liệu 1 lần và post sự kiện `IMU_EVT_WINDOW_READY`.
- **Task 4.2 - `svc_ai`:** Nhận Window, truyền qua hàm inference của `lib_tinyml`.
- **Task 4.3 - Fall Alert:** Nếu AI phát hiện Fall, post `AI_EVT_FALL_DETECTED`. `svc_cloud` nhận được sẽ lập tức gửi JSON Alert qua MQTT (QoS 1). Áp dụng Cooldown 10-15 giây để chống spam cảnh báo.
- **Task 4.4 - Pedometer & Telemetry:** Ở chế độ `STATE_NORMAL`, `svc_imu` đếm bước chân ngầm. `svc_cloud` hẹn giờ tự động thu thập trạng thái (Pin, Steps) gửi về Topic `status` mỗi 1 phút/lần.

### Phase 5: Triển khai phần cứng thực tế (LTE Module & OTA)
**Mục tiêu:** Cắt đứt hoàn toàn với mạng WiFi, chạy độc lập ngoài trời qua mạng 4G.
- **Task 5.1:** Tích hợp `drv_a7680c` vào `svc_network`. Cấu hình PPPoS stack của LwIP để biến A7680C thành Network Interface mặc định.
- **Task 5.2:** Bổ sung logic `STATE_OTA` (Tạm để trống ở các Phase trước). Chờ lệnh từ Backend để tải bản cập nhật `.bin` qua giao thức HTTPS trên nền mạng 4G.
