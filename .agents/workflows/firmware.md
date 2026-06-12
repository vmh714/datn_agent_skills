---
description: "Workflow cho vai trò Firmware: Lập trình C nhúng với FSM, ESP-IDF và giao tiếp không dây/có dây."
---

# Firmware Workflow

Sử dụng workflow này khi thực hiện các tác vụ liên quan đến vi điều khiển, phần mềm nhúng (Firmware), đặc biệt là dòng ESP32 sử dụng **ESP-IDF**.

## Kỹ năng cốt lõi (Skills)

1. **Finite State Machine (FSM) trong C**:
   - Luôn ưu tiên sử dụng kiến trúc State Machine (Máy trạng thái hữu hạn) để quản lý luồng thực thi trong hệ thống nhúng.
   - Định nghĩa rõ các trạng thái (States), sự kiện (Events) và hàm chuyển trạng thái (State Transition Functions).
   - Tránh việc sử dụng quá nhiều cờ (flags) lồng nhau (nested if-else) làm rối luồng xử lý.

2. **Hiểu và ứng dụng API của ESP-IDF**:
   - Sử dụng chuẩn FreeRTOS (Task, Queue, Semaphore, Mutex, Timer) do ESP-IDF cung cấp để xử lý đa nhiệm (multitasking).
   - Quản lý bộ nhớ cẩn thận, tránh memory leak khi cấp phát động (`malloc`, `free`) trong các task.
   - Sử dụng NVS (Non-Volatile Storage) để lưu trữ cấu hình.
   - Ưu tiên sử dụng ESP_LOGI, ESP_LOGE, ESP_LOGW cho việc logging thay vì `printf`.
   - **Tách biệt Logic và Log (Quy tắc Service vs Driver)**: Việc in Log (`ESP_LOG`) và các xử lý nghiệp vụ (Business Logic như tính toán tư thế, xử lý sự kiện) CHỈ được đặt ở các lớp `svc_` (Services). Các lớp `drv_` (Drivers) hoặc `lib_` (Libraries) chỉ làm nhiệm vụ lấy dữ liệu, xử lý thuật toán và **trả về giá trị (Return values) hoặc ném vào Queue**, tuyệt đối không in log kết quả nghiệp vụ làm rác màn hình.

3. **Giao tiếp có dây & không dây**:
   - **Không dây (Wireless)**:
     - **Wi-Fi**: Sử dụng sự kiện hệ thống của ESP-IDF (`esp_event_loop_create_default`) để xử lý quá trình kết nối Wi-Fi (SmartConfig, kết nối lại khi mất mạng).
     - **Bluetooth/BLE**: Cấu hình GATT server/client chuẩn xác. Chú ý tối ưu năng lượng khi dùng BLE.
   - **Có dây (Wired)**:
     - Nắm vững cấu hình và giao tiếp qua I2C (đọc cảm biến MPU, v.v.), SPI (màn hình, thẻ nhớ), UART (kết nối module ngoài).

## Hướng dẫn thực thi

1. **Xác định Yêu Cầu**: Xác định các cảm biến, giao thức giao tiếp và logic cần xử lý.
2. **Thiết kế FSM**: Phác thảo máy trạng thái trước khi code.
3. **Môi trường**: Luôn làm việc chủ yếu trong thư mục `d:\datn\firmware`.
4. **Viết Code**: Tuân thủ naming convention của C (rõ ràng, dùng prefix cho tên module).
5. **Kiểm tra**: Xem lại các cấu hình `sdkconfig` nếu có thay đổi về module ngoại vi.
