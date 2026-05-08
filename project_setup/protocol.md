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

Tất cả các API mặc định trả về JSON. Các endpoint yêu cầu Authentication sẽ sử dụng Header: `Authorization: Bearer <token>`.

### 2.1 Authentication
- **POST `/api/v1/auth/login`**: Đăng nhập hệ thống.
  - **Request (Form Data)**:
    ```json
    {
      "username": "admin",
      "password": "password123"
    }
    ```
  - **Response**:
    ```json
    {
      "access_token": "eyJhbG...",
      "token_type": "bearer"
    }
    ```

### 2.2 Quản lý Người bệnh (Patient / Wearer)
- **GET `/api/v1/wearers`**: Lấy danh sách bệnh nhân.
  - **Response**: `Array<WearerResponse>`

- **POST `/api/v1/wearers`**: Thêm mới bệnh nhân.
  - **Request Payload**:
    ```json
    {
      "full_name": "Nguyen Van A",
      "height_cm": 170.5,
      "org_id": "uuid-string"
    }
    ```
  - **Response**: `WearerResponse`

- **PUT `/api/v1/wearers/{id}`**: Cập nhật thông tin bệnh nhân.
  - **Request Payload**: (Tất cả fields là optional)
    ```json
    {
      "full_name": "Nguyen Van B",
      "height_cm": 172.0
    }
    ```

- **WearerResponse Object**:
  ```json
  {
    "id": "uuid-string",
    "full_name": "Nguyen Van A",
    "height_cm": 170.5,
    "org_id": "uuid-string",
    "created_at": "2024-04-23T10:00:00Z",
    "updated_at": "2024-04-23T10:00:00Z"
  }
  ```

### 2.3 Quản lý Thiết bị (Wear Device)
- **GET `/api/v1/devices`**: Lấy danh sách thiết bị.
  - **Response**: `Array<DeviceResponse>` (Kèm thông tin người đeo nếu đã gán).

- **POST `/api/v1/devices`**: Đăng ký thiết bị phần cứng mới.
  - **Request Payload**:
    ```json
    {
      "device_id": "MAC_ADDRESS_OR_ID",
      "firmware_version": "1.0.0",
      "is_active": true,
      "org_id": "uuid-string"
    }
    ```

- **PUT `/api/v1/devices/{device_id}`**: Cập nhật thông tin thiết bị.
  - **Request Payload**: (Optional fields)
    ```json
    {
      "firmware_version": "1.1.0",
      "is_active": false
    }
    ```

- **DELETE `/api/v1/devices/{device_id}`**: Xóa hoàn toàn thiết bị khỏi hệ thống.

- **POST `/api/v1/devices/{device_id}/assign`**: Gán thiết bị cho một `wearer_id`.
  - **Request Payload**:
    ```json
    {
      "wearer_id": "uuid-string"
    }
    ```

- **POST `/api/v1/devices/{device_id}/unassign`**: Gỡ thiết bị.
  - **Response**: `DeviceResponse` với `current_wearer_id: null`.

- **DeviceResponse Object**:
  ```json
  {
    "device_id": "dev_01",
    "firmware_version": "1.0.0",
    "is_active": true,
    "current_wearer_id": "uuid-string",
    "wearer": { ...WearerResponse... },
    "created_at": "...",
    "updated_at": "..."
  }
  ```

### 2.4 Dashboard & Monitoring
- **GET `/api/v1/dashboard/telemetry`**: Trạng thái thời gian thực của toàn bộ thiết bị.
  - **Response**:
    ```json
    [
      {
        "device_id": "dev_01",
        "battery_pct": 85,
        "last_online": "2024-04-23T10:05:00Z",
        "is_active": true,
        "wearer_id": "uuid-string"
      }
    ]
    ```

### 2.5 Lịch sử & Timeline
- **GET `/api/v1/history/alerts`**: Truy vấn lịch sử té ngã.
  - **Query Params**: `device_id` (optional).
  - **Response**: `Array<AlertHistory>`
    ```json
    {
      "id": "uuid",
      "device_id": "dev_01",
      "alert_type": "FALL_DETECTED",
      "confidence": 0.98,
      "is_resolved": false,
      "created_at": "..."
    }
    ```

- **GET `/api/v1/history/{device_id}/timeline`**: Nhật ký hoạt động chi tiết.
  - **Response**: `Array<TimelineEntry>`
    ```json
    {
      "id": "uuid",
      "type": "ALERT | EVENT",
      "title": "FALL_DETECTED | ACTIVITY_WALKING",
      "description": "Optional details",
      "created_at": "..."
    }
    ```

### 2.6 Data Collection (TinyML Research)
- **POST `/api/v1/data-collection/sessions`**: Lưu dữ liệu IMU thô để huấn luyện.
  - **Request Payload**:
    ```json
    {
      "device_id": "dev_01",
      "label": "FALLING",
      "start_timestamp": 1713800000000,
      "end_timestamp": 1713800005000,
      "sample_count": 500,
      "samples": [
        {"timestamp": 1713800000000, "ax": 0.1, "ay": -0.9, "az": 0.1, "gx": 0, "gy": 0, "gz": 0},
        ...
      ]
    }
    ```