# Kế Hoạch Triển Khai `STATE_ERROR`

Dưới đây là kế hoạch chi tiết để xử lý triệt để trạng thái `STATE_ERROR` cho hệ thống theo sơ đồ FSM:

## 1. Định nghĩa sự kiện phần cứng
*   **Mở rộng `sys_manager.h`**: Bổ sung event `SYS_EVT_HARDWARE_ERROR` vào enum `sys_event_id_t`.
*   **Mở rộng `sys_manager.c`**: Thêm nhánh bắt event cho `event_base == SYS_EVENT` và `event_id == SYS_EVT_HARDWARE_ERROR`. Khi xảy ra, gọi `sys_manager_set_state(STATE_ERROR)`.

## 2. Cơ chế tự khởi động lại (Auto-Reset)
*   Trong `sys_manager_init`, tạo một timer mới `auto_reboot_timer` trỏ tới hàm callback gọi `esp_restart()`.
*   Bên trong `sys_manager_set_state()`, nếu `new_state == STATE_ERROR`, tiến hành:
    1.  Khởi động `auto_reboot_timer` (ví dụ sau 10 giây).
    2.  Hệ thống sẽ tạm thời không làm gì để các component có thời gian dọn dẹp hoặc tắt đèn LED, in log lỗi... trước khi tự động reboot.

## 3. Quản lý lỗi I2C & MPU6050 (trong `svc_imu` hoặc `drv_mpu6050`)
*   Thêm biến toàn cục `i2c_consecutive_errors` để đếm số lần hàm đọc MPU6050 (vd: `mpu6050_read_fifo`) trả về lỗi.
*   Nếu đọc thành công, đặt lại biến này về 0.
*   Nếu biến này vượt qua một ngưỡng cho phép (ví dụ: 10 lần đọc hỏng liên tiếp do dây lỏng, cảm biến treo), gọi hàm:
    `esp_event_post(SYS_EVENT, SYS_EVT_HARDWARE_ERROR, NULL, 0, portMAX_DELAY);`

## 4. Quản lý lỗi Mạng / Cloud Timeout
*   Hiện tại, `svc_cloud` đã có MQTT Watchdog: tự động restart mạng sau 60s và `esp_restart()` sau 150s nếu mất kết nối. 
*   **Cải tiến (Tùy chọn)**: Thay vì gọi `esp_restart()` trực tiếp trong `svc_cloud.c`, ta đổi thành `esp_event_post(SYS_EVENT, SYS_EVT_HARDWARE_ERROR, ...)` để quy trình reset về chung một đầu mối duy nhất là `sys_manager`.
