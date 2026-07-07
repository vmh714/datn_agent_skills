# PROTOCOL SPECIFICATION - ELDERCARE IoT SYSTEM

Tài liệu này đặc tả chi tiết giao thức truyền thông qua MQTT (Real-time Layer) và HTTP REST API (Management Layer) giữa Firmware, Backend và Frontend trong hệ thống Eldercare Fall Detection.

---

## 1. MQTT PROTOCOL (Real-time Layer)

Broker MQTT sử dụng cấu trúc topic thống nhất dưới tiền tố `eldercare/`.

### 1.1 Topic: `eldercare/{device_id}/status` (Device -> Broker)
- **QoS**: 0. **Chu kỳ**: theo `interval` (mặc định 5s, đổi được qua topic `config/set`), chỉ gửi khi ở STATE_NORMAL.
- **Consumer**: Backend `mqtt_service` (ghi Postgres/Influx) **và** Frontend realtime (`mqtt-client.ts` subscribe đúng topic `status` này — KHÔNG có topic `telemetry` riêng, không ai republish).
- **Payload**:
```json
{
  "battery": 100,
  "steps": 0,
  "walk_steps": 0,
  "run_steps": 0,
  "state": "NORMAL",
  "ai_pred": "UNKNOWN",
  "ai_conf": 0.95
}
```
*Ghi chú: `walk_steps`/`run_steps` đếm riêng (pedometer on-device, gate theo HAR) để backend tính quãng đường đúng theo loại (`0.415` vs `0.5` × chiều cao); `steps` = tổng (tương thích cũ). `battery` hiện là placeholder (chờ ADC đọc pin). Backend tự đồng bộ vào PostgreSQL và InfluxDB.*

### 1.1b Topic: `eldercare/{device_id}/config/status` (Device -> Broker)
- **QoS**: 1. **Chu kỳ**: Gửi 1 lần lúc mới boot (kết nối MQTT thành công) hoặc ngay sau khi nhận được cấu hình mới từ `config/set`.
- **Payload**:
```json
{
  "interval": 5,
  "fall_threshold": 0.25,
  "fall_cooldown": 15,
  "fall_confirm_window": 4,
  "rssi_interval": 300,
  "stream_timeout": 5,
  "fw_version": "1.0.0"
}
```
*`fall_confirm_window` = cửa sổ xác nhận post-impact (giây, D-021); `rssi_interval` = chu kỳ đo RSSI 4G (giây, 0=tắt, D-022). Backend echo về DB để đồng bộ.*

### 1.2 Topic: `eldercare/{device_id}/alert/fall` (Device -> Broker)
- **Chu kỳ**: Phát tức thời khi phát hiện ngã, kèm **cooldown 15 giây** chống spam.
- **QoS**: 1 (dữ liệu sống còn — đảm bảo đến broker ít nhất một lần).
- **Payload** (khớp `AlertPayload` backend; chỉ `confidence` bắt buộc, `user_name`/`message` optional — backend chỉ dùng `confidence`. Bỏ `timestamp` vì firmware chưa có RTC → backend dùng giờ server):
```json
{
  "user_name": "",
  "message": "Fall detected",
  "confidence": 0.95
}
```

### 1.2b Topic: `eldercare/{device_id}/event` (Device -> Broker)
- **Chu kỳ**: Phát khi có sự kiện (Pin dưới 20%, Lỗi phần cứng, v.v.).
- **QoS**: 1
- **Payload**:
```json
{
  "event_type": "LOW_BATTERY",
  "description": "Pin thiết bị còn 14%"
}
```
*Ghi chú: Backend lưu vào `device_events` và hiển thị trên Timeline. Frontend tự động bật Toast nhắc nhở nhẹ trên Dashboard (không hú còi).*

### 1.3 Topic: `eldercare/{device_id}/imu_stream` (Device -> Broker)
- **Chu kỳ**: Truyền theo lô (batch) khi ở chế độ STREAMING; mỗi lô `cnt` mẫu (mặc định 50 mẫu = 0.5s ở 100Hz).
- **QoS**: 0 (ưu tiên thông lượng; mất vài lô không nghiêm trọng).
- **Payload**: mảng IMU 6 trục dạng `int16` (đã đổi hệ trục + lọc Kalman + chuẩn hóa, mỗi mẫu 6×int16 = 12 byte) được mã hóa **Base64** rồi nhúng vào JSON:
```json
{
  "ts": 1713800000000,
  "fs": 100,
  "cnt": 50,
  "data_b64": "<chuỗi Base64 của mảng int16 theo thứ tự ax,ay,az,gx,gy,gz>"
}
```

### 1.4 Topic: `eldercare/{device_id}/command` (Broker -> Device)
- **Hướng**: Frontend/Backend → Thiết bị (firmware subscribe với QoS 1).
- **Payload**:
```json
{
  "action": "start_stream | stop_stream | update_firmware",
  "url": "..." 
}
```
*Lưu ý: `url` chỉ đi kèm với `update_firmware`.*

### 1.5 Topic: `eldercare/{device_id}/config/set` (Broker -> Device)
- **Hướng**: Backend → Thiết bị (firmware subscribe với QoS 1).
- **Payload**:
```json
{
  "interval": 5,
  "fall_threshold": 0.25,
  "fall_cooldown": 15,
  "fall_confirm_window": 4,
  "rssi_interval": 300,
  "stream_timeout": 5
}
```
*`interval` = chu kỳ telemetry (giây, 1–3600); `fall_threshold` = ngưỡng xác suất chốt ngã (0.15–0.95); `fall_cooldown` = thời gian hồi cảnh báo ngã (giây, mặc định 15); `fall_confirm_window` = cửa sổ xác nhận post-impact (giây, 1–15, mặc định 4 — D-021); `rssi_interval` = chu kỳ đo RSSI 4G (giây, `0=tắt`, mặc định 300 — D-022, firmware clamp non-zero <60→60); `stream_timeout` = tự động tắt luồng stream (phút, mặc định 5).*
*Backend publish gói cấu hình GỘP này xuống thiết bị mỗi khi có request `PUT /devices/{id}` đổi bất kỳ tham số config nào. Firmware áp dụng, lưu NVS, rồi echo lại qua `config/status`.*

---

## 2. HTTP REST API (Management Layer)

Tất cả các REST API sử dụng định dạng JSON. Cần đính kèm Header: `Authorization: Bearer <token>` cho các endpoint bảo mật.

### 2.1 Authentication
- **POST `/api/v1/auth/login`**: Đăng nhập lấy access token.
  - **Request Body (OAuth2 Form Content)**:
    - `username`: Tên đăng nhập
    - `password`: Mật khẩu
  - **Response (`Token` Schema)**:
    ```json
    {
      "access_token": "eyJhbG...",
      "token_type": "bearer"
    }
    ```

### 2.2 Quản lý Người bệnh (Wearer / Patient)
- **GET `/api/v1/wearers/`**: Danh sách người bệnh.
- **POST `/api/v1/wearers/`**: Tạo thông tin người bệnh.
- **GET `/api/v1/wearers/{wearer_id}`**: Lấy chi tiết thông tin người bệnh.
- **PUT `/api/v1/wearers/{wearer_id}`**: Cập nhật thông tin người bệnh.
- **DELETE `/api/v1/wearers/{wearer_id}`**: Xóa thông tin người bệnh.

### 2.3 Quản lý Thiết bị (Wear Device)
- **GET `/api/v1/devices/`**: Lấy danh sách thiết bị kèm trạng thái kết nối (`is_online`) và thông tin người bệnh sở hữu.
- **POST `/api/v1/devices/`**: Khai báo đăng ký thiết bị mới.
- **PUT `/api/v1/devices/{device_id}`**: Cập nhật thông số thiết bị.
- **DELETE `/api/v1/devices/{device_id}`**: Gỡ bỏ hoàn toàn thiết bị khỏi hệ thống.
- **POST `/api/v1/devices/{device_id}/assign`**: Gán thiết bị cho một người bệnh (`wearer_id`).
- **POST `/api/v1/devices/{device_id}/unassign`**: Hủy gán thiết bị khỏi người bệnh.
- **POST `/api/v1/devices/{device_id}/command`**: Gửi lệnh realtime xuống thiết bị qua MQTT (body `{action: start_stream|stop_stream, val?}`). Backend kiểm tra org rồi publish (B5 — thay cho FE publish MQTT trực tiếp). `set_interval`/`set_fall_threshold`/`set_fall_cooldown` cấu hình bền vững đi qua **PUT** `/devices/{id}`.
- **PUT `/api/v1/devices/{device_id}`**: Cập nhật thiết bị; nếu đổi bất kỳ tham số config bền vững (`telemetry_interval`/`fall_threshold`/`fall_cooldown`/`fall_confirm_window`/`rssi_interval`/`stream_timeout`) → backend publish gói gộp lên topic `config/set` xuống device.

### 2.4 Dashboard & Lịch sử
- **GET `/api/v1/dashboard/telemetry`**: Lấy trạng thái hoạt động tổng hợp thời gian thực.
- **GET `/api/v1/history/alerts`**: Truy vấn danh sách cảnh báo té ngã.
  - *Query Params hỗ trợ lọc theo `device_id`, `limit`, `offset`*.
- **PATCH `/api/v1/history/alerts/{alert_id}/resolve`**: Xác nhận giải quyết/xử lý cảnh báo.
  - *Query Params*: `device_id` (Tùy chọn - Dùng cho cơ chế Hybrid Alert Sync để xử lý fallback cảnh báo chưa lưu DB).
- **GET `/api/v1/history/{device_id}/timeline`**: Nhật ký hoạt động tổng hợp của thiết bị.
- **GET `/api/v1/history/{device_id}/telemetry`**: Truy vấn lịch sử trạng thái thiết bị (từ InfluxDB, dựa trên topic eldercare/{device_id}/status) để xem log và vẽ biểu đồ.
- **GET `/api/v1/history/steps`**: Thống kê lịch sử số bước chân và quãng đường di chuyển theo ngày.

### 2.5 Thu thập dữ liệu (TinyML Research)
- **POST `/api/v1/data-collection/sessions`**: Ghi nhận một phiên chạy dữ liệu IMU thô kèm nhãn hành vi phục vụ huấn luyện mô hình.

---

## 3. DATA SCHEMAS (Mô hình dữ liệu chính)

Dưới đây là đặc tả các Schema phản hồi tiêu biểu từ hệ thống REST API:

### 3.1 DeviceResponse
```json
{
  "device_id": "string",
  "firmware_version": "string",
  "is_active": true,
  "current_wearer_id": "uuid-string | null",
  "org_id": "string",
  "created_at": "datetime-string",
  "updated_at": "datetime-string",
  "battery_pct": "integer | null",
  "last_online": "datetime-string | null",
  "is_online": true,
  "wearer": {
    "id": "uuid-string",
    "full_name": "string",
    "height_cm": 175.5,
    "org_id": "string",
    "created_at": "datetime-string",
    "updated_at": "datetime-string"
  }
}
```

### 3.2 AlertHistory
```json
{
  "id": "uuid-string (Có thể là UUID ảo từ MQTT hoặc UUID thực từ DB)",
  "device_id": "string",
  "alert_type": "FALL_DETECTED",
  "confidence": 0.98,
  "is_resolved": false,
  "created_at": "datetime-string"
}
```

### 3.3 StepHistoryResponse
```json
{
  "date": "YYYY-MM-DD",
  "steps": 1550,
  "walk_steps": 1250,
  "run_steps": 300,
  "distance_km": 1.15
}
```
*`steps` = tổng (tương thích cũ); `walk_steps`/`run_steps` tách riêng. `distance_km` = `(walk_steps×0.415 + run_steps×0.5)×height/1000`. Tất cả lấy max theo ngày từ InfluxDB.*

---

## 4. CƠ CHẾ ĐỒNG BỘ CẢNH BÁO LAI (Hybrid Alert Sync Mechanism)

Khi xảy ra té ngã, luồng sự kiện được xử lý song song để đạt độ trễ thấp nhất:
1. **Nhận diện**: Thiết bị phát MQTT Event đến Topic `eldercare/{device_id}/alert/fall` (payload có `confidence`).
2. **Hiển thị Tức thời**: Frontend đang lắng nghe broker MQTT nhận được sự kiện và hiển thị ngay Overlay/Banner Cảnh báo đỏ nguy hiểm lập tức lên màn hình giám sát, đồng thời gán một **UUIDv4 ngẫu nhiên tạm thời** làm ID cho cảnh báo này nếu DB chưa kịp ghi nhận.
3. **Lưu trữ**: Backend nhận sự kiện qua MQTT, ghi nhận vào cơ sở dữ liệu Postgres và sinh một ID thực tế.
4. **Xử lý / Resolve**:
   - Khi người dùng nhấn nút "Resolve" (Xác nhận an toàn) trên giao diện, Frontend sẽ gửi yêu cầu `PATCH /api/v1/history/alerts/{alert_id}/resolve?device_id={device_id}`.
   - **Cơ chế Fallback thông minh**: Nếu `alert_id` là UUID tạm thời do Frontend sinh ra (không tồn tại trong DB), Backend sẽ tự động truy tìm cảnh báo chưa được xử lý mới nhất của thiết bị `device_id` và cập nhật trạng thái `is_resolved = true` cho bản ghi đó. Điều này giúp loại bỏ hoàn toàn các lỗi `404 Not Found` khó chịu trên Frontend.