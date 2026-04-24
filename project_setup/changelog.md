# Project History & Documentation Changelog

Tài liệu này lưu trữ lịch sử thay đổi của các file đặc tả hệ thống (`instruction.md`, `protocol.md`) để đảm bảo các Agent luôn nắm bắt được ngữ cảnh mới nhất.

---

## 2026-04-24: Khởi tạo & Chuẩn hóa Master Spec

### [Updated] `instruction.md` (v2.0)
- **Nội dung:** Cập nhật toàn bộ kiến trúc từ Prototype lên Production.
- **Thay đổi chính:**
    - Chốt vị trí đeo: Thắt lưng phía trước.
    - Chia 2 giai đoạn: Phase 1 (Data collection) và Phase 2 (TinyML deployment).
    - Quy định thuật toán té ngã Post-impact (< 1s).
    - Tích hợp đếm bước chân và quãng đường dựa trên chiều cao.
    - Chốt kết nối 4G LTE (A7680C).

### [Initial] `project_configs/.env`
- Thiết lập biến `${WORKSPACE_ROOT}` để đảm bảo tính di động của Project.

---

## 2026-04-24: Thiết kế UI/UX & Protocol v1.0

### [New] `protocol.md` (v1.0)
- **MQTT**: Đặc tả 4 topic chính (`telemetry`, `alert/fall`, `raw_imu`, `cmd`).
- **REST API**: Đặc tả các endpoint quản lý cấu hình (chiều cao, tên) và lịch sử vận động.
- **Data Collection**: Quy chuẩn gửi mảng 50 mẫu (Batch mode) với tần số 2Hz.

### [UI/UX Decisions]
- **Màn 1 (Dashboard)**: Giám sát Real-time, ưu tiên hiển thị trạng thái người đeo và cảnh báo té ngã khẩn cấp (Modal + Sound).
- **Màn 2 (Config/History)**: Quản lý Metadata và xem lịch sử bước chân/quãng đường theo ngày.
- **Màn 3 (Monitor)**: Chuyên dụng cho Phase 1, hiển thị Raw IMU 100Hz và công cụ thu thập mẫu train AI.

### [System Optimization]
- **Offloading Calculation**: Di chuyển logic tính toán quãng đường từ Firmware lên Backend (dựa trên metadata chiều cao).
- **Telemetry Refinement**: Tách chi tiết các loại bước chân (`walk_steps`, `run_steps`).
- **Context-aware Alerts**: Firmware nhận `user_name` từ Cloud để nhúng vào tin nhắn cảnh báo té ngã.
