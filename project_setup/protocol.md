# PROTOCOL SPECIFICATION - ELDERCARE IoT SYSTEM

Tài liệu này đặc tả các gói tin (payload) và giao thức truyền thông giữa Firmware, Backend và Frontend.

---

## 1. MQTT PROTOCOL (Real-time Layer)
Tất cả các topic từ thiết bị gửi lên đều tuân thủ nguyên tắc bảo mật và sử dụng tiền tố: `eldercare/{device_id}/` (Ví dụ: `eldercare/1A:2B:3C:4D/telemetry`).

### 1.1 Topic: `eldercare/{device_id}/status` (Device -> Cloud)
- **Chu kỳ**: 1 phút/lần.
- **Consumer**: Backend (Lưu trạng thái vào Postgres, lưu số bước vào InfluxDB).
- **Payload**:
```json
{
  "device_id": "dev_01",
  "status": "online",
  "battery_pct": 85,
  "rssi": -70,
  "walk_steps": 120,
  "run_steps": 0,
  "timestamp": 1713800000
}
```
*Ghi chú: Backend sẽ tự động tính quãng đường dựa trên `walk_steps`, `run_steps` và chiều cao người đeo lưu trong PostgreSQL, sau đó ghi cụm data vào InfluxDB.*

### 1.2 Topic: `eldercare/{device_id}/alert/fall` (Device -> Cloud/Web)
- **Chu kỳ**: Tức thời khi có sự kiện.
- **Consumer**: Frontend (WebSockets trực tiếp để hiển thị Real-time) và Backend (Lưu vào Postgres).
- **Payload**:
```json
{
  "device_id": "dev_01",
  "user_name": "Nguyen Van A",
  "timestamp": 1713800000,
  "confidence": 0.95,
  "message": "Nguyen Van A fall detected!"
}
```
*Ghi chú: `user_name` được Firmware lưu cục bộ sau khi nhận từ lệnh cấu hình.*

### 1.3 Topic: `eldercare/{device_id}/event` (Device -> Cloud)
- **Chu kỳ**: Chỉ gửi khi có sự thay đổi trạng thái (State Transition).
- **Consumer**: Backend (Lưu vào bảng `device_events` trong Postgres).
- **Payload**:
```json
{
  "timestamp": 1713800000,
  "device_id": "dev_01",
  "event_type": "ACTIVITY_WALKING", 
  "description": "Patient started walking"
}
```
*Ghi chú: Các `event_type` có thể là: `DEVICE_STARTED`, `ACTIVITY_WALKING`, `ACTIVITY_STATIONARY`...*

### 1.4 Topic: `eldercare/{device_id}/telemetry/imu` (Device -> Cloud)
- **Chu kỳ**: Phụ thuộc vào Data Collection Mode (Phase 1). Không gửi trong Production.
- **Consumer**: Backend (Ghi thẳng dạng Batch vào InfluxDB).
- **Payload**:
```json
{
  "timestamp": 1713800000000,
  "fs": 100,
  "columns": ["ax", "ay", "az", "gx", "gy", "gz"],
  "samples": [
    [0.10, -0.98, 0.20, 0.01, 0.05, -0.02],
    [0.11, -0.97, 0.21, 0.02, 0.04, -0.01]
  ]
}
```

### 1.5 Topic: `eldercare/{device_id}/cmd` (Backend -> Device)
- **Mục đích**: Điều khiển và cấu hình.
- **Payload**:
```json
{
  "command": "SET_CONFIG",
  "params": {
    "user_name": "Mr. Hung",
    "sensitivity": 0.8
  }
}
```
*Ghi chú: Backend gửi tên người đeo xuống để Firmware hiển thị hoặc nhúng vào Alert.*

---

## 2. HTTP REST API (Management Layer)

### 2.1 Quản lý Người bệnh (Patient / Wearer)
- **GET `/api/v1/wearers`**: Lấy danh sách bệnh nhân.
- **POST `/api/v1/wearers`**: Thêm mới bệnh nhân (Payload cần: `full_name`, `height_cm`).
- **PUT `/api/v1/wearers/{id}`**: Cập nhật thông tin bệnh nhân.

### 2.2 Quản lý Thiết bị (Wear Device)
- **GET `/api/v1/devices`**: Lấy danh sách thiết bị và trạng thái.
- **POST `/api/v1/devices`**: Đăng ký thiết bị phần cứng mới.
- **POST `/api/v1/devices/{device_id}/assign`**: Gán thiết bị cho một `wearer_id`.
- **POST `/api/v1/devices/{device_id}/unassign`**: Gỡ thiết bị.

### 2.3 Dashboard & Lịch sử (Alert History & Telemetry)
- **GET `/api/v1/dashboard/telemetry`**: Lấy trạng thái thiết bị và số bước chân hiện tại (Frontend polling 1 phút/lần).
- **GET `/api/v1/history/alerts`**: Truy vấn lịch sử các vụ té ngã (từ PostgreSQL).
- **GET `/api/v1/history/telemetry`**: Lấy dữ liệu vẽ biểu đồ vận động theo ngày/tuần (số bước chân, quãng đường từ InfluxDB).
- **GET `/api/v1/devices/{device_id}/timeline`**: Lấy nhật ký hoạt động Timeline (Recent Activity Log). API này gộp dữ liệu từ 2 bảng `alerts` và `device_events` trong PostgreSQL, sắp xếp theo thời gian giảm dần để trả về cho Frontend hiển thị.