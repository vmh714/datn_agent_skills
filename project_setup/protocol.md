# PROTOCOL SPECIFICATION - ELDERCARE IoT SYSTEM

Tài liệu này đặc tả các gói tin (payload) và giao thức truyền thông giữa Firmware, Backend và Frontend.

---

## 1. MQTT PROTOCOL (Real-time Layer)
Tất cả các topic đều sử dụng tiền tố `eldercare/dev_{id}/`.

### 1.1 Topic: `telemetry` (Device -> Cloud/Web)
- **Chu kỳ**: 1 giây/lần.
- **Payload**:
```json
{
  "device_id": "dev_01",
  "status": "online",
  "battery": 85,
  "rssi": -70,
  "activity_state": "walking",
  "walk_steps": 1200,
  "run_steps": 50,
  "timestamp": 1713800000
}
```
*Ghi chú: Backend sẽ tự động tính quãng đường dựa trên `walk_steps`, `run_steps` và chiều cao người đeo lưu trong database.*

### 1.2 Topic: `alert/fall` (Device -> Cloud/Web)
- **Chu kỳ**: Tức thời khi có sự kiện.
- **Payload**:
```json
{
  "device_id": "dev_01",
  "user_name": "Mr. Hung",
  "timestamp": 1713800000,
  "confidence": 0.98,
  "message": "Mr. Hung fall detected!"
}
```
*Ghi chú: `user_name` được Firmware lưu cục bộ sau khi nhận từ lệnh cấu hình.*

### 1.3 Topic: `raw_imu` (Device -> Web Monitor)
- **Chu kỳ**: 2Hz (Gửi theo lô 50 mẫu).
- **Payload**:
```json
{
  "ts": 1713800000000,
  "fs": 100,
  "data": [
    [ax, ay, az, gx, gy, gz],
    ... (50 samples)
  ]
}
```

### 1.4 Topic: `cmd` (Backend -> Device)
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

### 2.1 Quản lý thiết bị
- **GET `/api/v1/devices`**: Lấy danh sách thiết bị.
    - Response: `{ "status": "success", "data": [{ "id": "dev_01", "name": "Cụ A", "is_online": true }] }`
- **POST `/api/v1/devices/{id}/config`**: Đổi tên người đeo, set chiều cao.
    - Request: `{ "name": "Cụ B", "user_height": 165 }`

### 2.2 Lịch sử & Dữ liệu
- **GET `/api/v1/devices/{id}/history?date=YYYY-MM-DD`**: Lấy dữ liệu vận động trong ngày.
    - Response: `{ "steps_total": 5000, "distance_total": 3500, "chart_data": [...] }`
- **POST `/api/v1/devices/{id}/data-collection`**: Lưu file CSV cho AI.
    - Request: `{ "label": "fall", "samples": [...] }`

---

## 3. UI/UX DESIGN FLOWS

### Screen 1: Real-time Dashboard
- **MQTT Sub**: `eldercare/+/telemetry`, `eldercare/+/alert/fall`.
- **UX**: Hiển thị Card các thiết bị. Khi có `alert/fall`, hiện Modal đỏ chiếm toàn màn hình + Âm báo.

### Screen 2: Config & History
- **API**: `/api/v1/devices/{id}/config`, `/api/v1/devices/{id}/history`.
- **UX**: Cho phép người quản lý đổi tên cụ, cập nhật chiều cao và xem biểu đồ bước chân theo ngày.

### Screen 3: Monitor Data (Phase 1)
- **MQTT Sub**: `eldercare/{id}/raw_imu`.
- **UX**: Vẽ biểu đồ Recharts mượt mà từ lô 50 mẫu. Có nút "Record" để gửi dữ liệu về Backend lưu CSV.
