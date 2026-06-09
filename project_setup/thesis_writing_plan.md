# Kế Hoạch Viết Đồ Án Tốt Nghiệp (Tích hợp Kiến trúc Dự án)

Kế hoạch này được cập nhật dựa trên nguyên tắc **Viết từ Dễ (lý thuyết/thiết kế đã có sẵn) đến Khó (chờ hoàn thiện thực tế)**, đồng thời **ánh xạ trực tiếp** tới các file tài liệu và mã nguồn hiện có trong dự án. Điều này giúp tối ưu hóa việc sử dụng lệnh `/write_chapter` bằng cách chỉ ra chính xác Data/Input cần nạp cho Agent.

---

## Giai Đoạn 1: Viết ngay lập tức (Lý thuyết & Thiết kế Tổng quan)
*Phần này không phụ thuộc vào tiến độ code. Dữ liệu đã có sẵn đầy đủ trong thư mục `datn-agent-skills/project_setup/`.*

### 1. Chương 3: Nền tảng lý thuyết và công nghệ sử dụng
- **Tình trạng:** Viết dở (9.5KB).
- **Dữ liệu đầu vào (Input cho Agent):**
  - **Kiến trúc tổng thể:** Đọc file `architecture_overview.md`.
  - **Lý thuyết Backend:** FastAPI, PostgreSQL, InfluxDB (Agent tự tổng hợp kiến thức nền).
  - **Lý thuyết Firmware/Hardware:** Cảm biến MPU6050, Module 4G A7680C, ESP32, hệ điều hành FreeRTOS (ESP-IDF).
- **Lệnh mẫu:** `/write_chapter Dựa vào file @[c:\...\architecture_overview.md], hãy viết mục 3.2 về các công nghệ được lựa chọn trong dự án.`

### 2. Chương 4 (Phần 1): Phân tích & Thiết kế Kiến trúc Hệ thống
- **Dữ liệu đầu vào (Input cho Agent):**
  - **Thiết kế Cơ sở dữ liệu:** File `schema.md` (giải thích ERD, tại sao dùng InfluxDB cho time-series và Postgres cho metadata).
  - **Thiết kế Giao thức truyền thông:** File `protocol.md` (giải thích cấu trúc gói tin MQTT, HTTP API).
  - **Thiết kế Firmware:** File `firmware_architecture_design.md` (giải thích các tầng Hardware Abstraction, Services, App).
- **Lệnh mẫu:** `/write_chapter Dựa vào file @[c:\...\schema.md] và @[c:\...\protocol.md], hãy viết mục 4.1 về thiết kế cơ sở dữ liệu và giao thức truyền thông.`

### 3. Chương 1: Giới thiệu đề tài
- **Dữ liệu đầu vào:** Thông tin cơ bản về đề tài, lý do thực hiện.
- **Lệnh mẫu:** `/write_chapter Hãy viết phần giới thiệu đề tài tập trung vào hệ thống nhận diện hành động và phát hiện ngã cho người già sử dụng IoT.`

---

## Giai Đoạn 2: Trung Bình - Viết chi tiết việc Triển khai (Dựa trên Code đang có)
*Tận dụng các file `README.md` trong từng component của Firmware và tài liệu Frontend.*

### 4. Chương 4 (Phần 2): Triển khai Firmware (Thiết bị IoT)
- **Tình trạng:** Firmware đang được phát triển theo hướng module hóa (Component-based).
- **Dữ liệu đầu vào (Input cho Agent):**
  - **Tầng Driver:** `components/drv_mpu6050/README.md` và `components/drv_a7680c/README.md` (Cách đọc dữ liệu thô, giao tiếp I2C/UART).
  - **Tầng Xử lý tín hiệu:** `components/lib_kalman/README.md` và `components/svc_imu/README.md` (Cách áp dụng bộ lọc Kalman và nhận diện hành động/ngã).
  - **Tầng Mạng & Quản lý:** `components/svc_cloud/README.md`, `components/svc_network/README.md`, `components/sys_manager/README.md`.
- **Lệnh mẫu:** `/write_chapter Dựa vào file README @[...\components\svc_imu\README.md], hãy viết mục 4.2.1 về thuật toán xử lý tín hiệu IMU và nhận diện ngã trên thiết bị.`

### 5. Chương 4 (Phần 3): Triển khai Frontend & Backend
- **Dữ liệu đầu vào (Input cho Agent):**
  - **Frontend:** Tham chiếu file `fe_implementation.md` (Kiến trúc React/Next.js, quản lý state, giao diện theo dõi sức khỏe).
  - **Backend:** Cung cấp link các file router của FastAPI để Agent phân tích logic lưu luồng dữ liệu xuống DB.

---

## Giai Đoạn 3: Khó - Chờ hệ thống chạy thực tế (Kết quả & Đóng góp)
*Chỉ viết khi các module đã ghép nối thành công.*

### 6. Chương 4 (Phần 4): Kết quả Thực nghiệm & Đánh giá
- **Dữ liệu đầu vào (Tương lai):** 
  - Ảnh chụp màn hình ứng dụng web.
  - Log console trên ESP32 chứng minh nhận diện đúng.
  - Biểu đồ thời gian trễ (latency), tiêu thụ năng lượng.
- **Cách nạp Data:** Bạn gạch đầu dòng các chỉ số kỹ thuật (VD: "Độ trễ trung bình 150ms, độ chính xác phát hiện ngã 95%") để Agent diễn giải thành đoạn văn phân tích.

### 7. Chương 5: Các giải pháp và đóng góp nổi bật
- **Dữ liệu đầu vào:** 4 Khía cạnh kỹ thuật đã được thống nhất:
  1. **Thiết kế luồng xử lý đa nhiệm thời gian thực với FreeRTOS:** Khắc phục nút thắt cổ chai (bottleneck) của Super Loop, chạy song song lấy mẫu IMU 100Hz và AI Inference.
  2. **Dung hợp dữ liệu (Sensor Fusion) bằng Bộ lọc Kalman:** Khử nhiễu gia tốc kế và trôi gyroscope để AI không bị báo động giả.
  3. **Kiến trúc cơ sở dữ liệu kép (Dual-Database):** Dùng InfluxDB hứng tải ghi (write) viễn trắc liên tục, Postgres quản lý metadata.
  4. **Cơ chế Đồng bộ cảnh báo lai (Hybrid Alert Sync):** Kết hợp MQTT (cảnh báo popup real-time <1s) và REST API/Postgres (lưu lịch sử) để hệ thống Web luôn đồng bộ.
- **Cách nạp Data:** Dựa vào dàn ý này, Agent tự động triển khai thành các tiểu mục (5.1 -> 5.4), phân tích rõ Bài toán (Problem) $\rightarrow$ Giải pháp (Solution) $\rightarrow$ Kết quả đạt được theo chuẩn mẫu tham khảo.

### 8. Chương 6: Kết luận và Hướng phát triển
- Đánh giá tổng quan xem dự án đã đạt được các mục tiêu ở Chương 1 chưa. 
- Chuẩn hóa các file tham chiếu (`Danh_sach_tai_lieu_tham_khao.bib`, `Tu_viet_tat.tex`).
