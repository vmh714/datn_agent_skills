# Kiến trúc hệ thống IoT Eldercare (Fall Detection)

> **Cập nhật lần cuối:** 2026-06-29
> Đọc file này trước khi làm bất kỳ task nào trong dự án để tránh grep/scan lại codebase.

## Mục tiêu hệ thống
Giám sát người cao tuổi 24/7 qua thiết bị wearable ESP32 — phát hiện ngã (Fall Detection) và nhận dạng hoạt động (HAR: đi bộ, đứng, chạy, ngã). Cảnh báo real-time đến dashboard y tá/bác sĩ.

## Monorepo layout
```
datn/
├── backend/      # FastAPI REST API + MQTT bridge
├── frontend/     # Next.js 16 dashboard (web)
├── firmware/     # ESP32 C/ESP-IDF (wearable)
└── REPORT/       # Báo cáo luận văn LaTeX
```
> **Quy ước đường dẫn:** mỗi `backend/`, `frontend/`, `firmware/` chứa code **trực tiếp** (máy gốc). Khi clone repo về, một số máy có thể tạo thêm thư mục con trùng tên repo (vd `firmware/HAR-and-Fall-detection-firmware/`). Vì vậy mọi `file:line` trong các doc đều tính **TƯƠNG ĐỐI VỚI GỐC REPO tương ứng** (vd firmware: `components/...`; backend: `app/...`) — không nhúng tên repo con.

## Stack công nghệ

| Layer | Tech |
|-------|------|
| **Backend** | FastAPI + Uvicorn async, PostgreSQL (SQLAlchemy 2.x + asyncpg), InfluxDB, aiomqtt, JWT HS256, Alembic, Pydantic v2, deploy Render |
| **Frontend** | Next.js 16 App Router + React 19 + TypeScript, Zustand v5, TanStack React Query v5, mqtt v5 (WebSocket), Recharts v3, shadcn/Radix + Tailwind v4 |
| **Firmware** | ESP-IDF C, FSM, MPU-6050 IMU (±8g / ±2000dps), A7680C 4G LTE, MQTT over TLS (mqtts port 8883) |
| **Database** | PostgreSQL (relational: users/devices/wearers/alerts) + InfluxDB (time-series: telemetry, imu_raw) |
| **Message broker** | MQTT (TLS cho firmware, WebSocket cho frontend) |

## Luồng dữ liệu tổng thể
```
ESP32 (firmware, 100Hz IMU)
  ├── MQTT TLS publish → Backend mqtt_service.py
  │     ├── telemetry → InfluxDB measurement "telemetry"
  │     ├── fall alert → PostgreSQL alerts table
  │     └── device event → PostgreSQL device_events table
  └── HTTP POST (fallback) → /api/v1/data-collection/sessions → InfluxDB "imu_raw"

Frontend Dashboard (Next.js)
  ├── REST API (JWT Bearer) → FastAPI endpoints → PostgreSQL / InfluxDB
  └── MQTT WebSocket → mqtt-client.ts singleton → Zustand stores → React UI
```

## MQTT Topics
> **Khóa topic `{mac}` = MAC chip** (vân tay phần cứng, firmware lấy từ eFuse), KHÔNG phải `device_id`
> ngữ nghĩa. Backend khớp MQTT theo `mac`, tự sinh `device_id` (`esp32_eldercare_NN`) khi auto-provision,
> publish lệnh/config/OTA tới `eldercare/<device.mac>/...`. Per-org broker (1 org/deployment). Xem
> [DECISIONS.md](DECISIONS.md) D-020.

| Topic | Publisher | Subscriber | Nội dung |
|-------|-----------|------------|----------|
| `eldercare/{mac}/status` | ESP32 | Backend | battery, steps, walk_steps, run_steps, state, ai_pred, ai_conf (QoS 0) |
| `eldercare/{mac}/config/status` | ESP32 | Backend | interval, fall_threshold, fall_cooldown, fall_confirm_window, rssi_interval, stream_timeout, **fw_version** (QoS 1; fire lúc connect/reconnect → auto-provision + cập nhật firmware_version) |
| `eldercare/{mac}/config/set` | Backend | ESP32 | Cấu hình muốn cập nhật: interval, fall_threshold, fall_cooldown, fall_confirm_window, rssi_interval, stream_timeout (QoS 1) |
| `eldercare/{mac}/alert/fall` | ESP32 | Backend + Frontend | `{user_name, message, confidence}` (QoS 1) |
| `eldercare/{mac}/event` | ESP32 | Backend | event_type, description (firmware CHƯA publish — kế hoạch) |
| `eldercare/{mac}/imu_stream` | ESP32 | Frontend (lazy) | `{ts,fs,cnt,data_b64}` int16 base64 (QoS 0) |
| `eldercare/{mac}/telemetry` | Backend | Frontend | battery_pct, walk_steps, run_steps |
| `eldercare/{mac}/command` | Frontend | ESP32 | start_stream, stop_stream, ota_update (QoS 1) |

> Firmware, backend, frontend và `tools/fake_device.py` đều dùng `alert/fall`. Lệch còn lại: firmware **chưa** publish `event` (backend có handler). Chi tiết payload: `protocol.md`.

## JWT Structure
```json
{"sub": "user_id", "username": "...", "role": "MANAGER|ADMIN", "exp": timestamp}
```
Algorithm: HS256 | Expire: 1440 min (24h) | Stored: HTTP-only cookie

## Multi-tenancy
Mọi entity (User, Wearer, Device, Alert) đều có `org_id`. Mọi query lọc theo `current_user.org_id` từ JWT.

## Chi tiết từng layer
- Backend chi tiết → xem `backend.md`
- Frontend chi tiết → xem `frontend.md`
