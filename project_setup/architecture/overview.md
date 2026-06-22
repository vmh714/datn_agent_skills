# Kiến trúc hệ thống IoT Eldercare (Fall Detection)

> **Cập nhật lần cuối:** 2026-06-21
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
| Topic | Publisher | Subscriber | Nội dung |
|-------|-----------|------------|----------|
| `eldercare/{deviceId}/status` | ESP32 | Backend | battery, steps, walk_steps, run_steps, state, ai_pred, ai_conf, interval (QoS 0) |
| `eldercare/{deviceId}/alert/fall` | ESP32 | Backend + Frontend | `{user_name, message, confidence}` (QoS 1) |
| `eldercare/{deviceId}/event` | ESP32 | Backend | event_type, description (firmware CHƯA publish — kế hoạch) |
| `eldercare/{deviceId}/imu_stream` | ESP32 | Frontend (lazy) | `{ts,fs,cnt,data_b64}` int16 base64 (QoS 0) |
| `eldercare/{deviceId}/telemetry` | Backend | Frontend | battery_pct, walk_steps, run_steps |
| `eldercare/{deviceId}/command` | Frontend | ESP32 | start_stream, stop_stream, set_interval, set_fall_threshold, set_fall_cooldown, ota_update (QoS 1) |

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
