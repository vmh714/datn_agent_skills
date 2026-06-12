# Kiến trúc hệ thống IoT Eldercare (Fall Detection)

> **Cập nhật lần cuối:** 2026-06-12
> Đọc file này trước khi làm bất kỳ task nào trong dự án để tránh grep/scan lại codebase.

## Mục tiêu hệ thống
Giám sát người cao tuổi 24/7 qua thiết bị wearable ESP32 — phát hiện ngã (Fall Detection) và nhận dạng hoạt động (HAR: đi bộ, đứng, chạy, ngã). Cảnh báo real-time đến dashboard y tá/bác sĩ.

## Monorepo layout
```
datn/
├── backend/HAR_and_Fall-detection-backend/   # FastAPI REST API + MQTT bridge
├── frontend/Fall-Detection-dashboard/        # Next.js 16 dashboard (web)
├── firmware/                                 # ESP32 C/ESP-IDF (wearable)
└── REPORT/                                   # Báo cáo luận văn LaTeX
```

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
| `eldercare/{deviceId}/status` | ESP32 | Backend | battery_pct, walk_steps, run_steps, rssi |
| `eldercare/{deviceId}/alert/fall` | ESP32 | Backend + Frontend | confidence, message |
| `eldercare/{deviceId}/event` | ESP32 | Backend | event_type, description |
| `eldercare/{deviceId}/imu_stream` | ESP32 | Frontend (lazy) | Base64 int16_t binary, 50 samples/batch |
| `eldercare/{deviceId}/telemetry` | Backend? | Frontend | battery_pct, walk_steps, run_steps |
| `eldercare/{deviceId}/command` | Frontend | ESP32 | start_stream, stop_stream, ota_update |

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
