# Tổng quan kiến trúc hệ thống Fall Detection

> Tài liệu tổng hợp cấu trúc, luồng dữ liệu và các module quan trọng của toàn bộ dự án. Dùng để tham chiếu nhanh khi làm việc với code.

---

## 1. Kiến trúc tổng thể

```
[ESP32S3 + MPU6050 @100Hz]
    ↓ 4G LTE (A7680C qua giao thức PPPoS)
[MQTT Broker: mqtt.toolhub.app:8883 (mqtts/TLS)]
    ├──→ [FastAPI Backend]
    │         ├── PostgreSQL (Supabase, ap-southeast-2): metadata, alerts
    │         └── InfluxDB (influx.tdcq.me): time-series telemetry, raw IMU
    │         ↕ REST API /api/v1/...
    └──→ [Next.js Frontend]
              └── WebSocket WSS :8084 MQTT trực tiếp (real-time alerts)
```

**Phase 1 (hiện tại):** Data Collection — firmware gửi raw IMU về backend lưu InfluxDB, dùng train TinyML.  
**Phase 2:** Edge Inference — model TinyML chạy trên ESP32S3, gửi kết quả HAR + fall detection về dashboard.

---

## 2. Frontend

**Đường dẫn:** `fall-detection/fall-detection/`  
**Chạy:** `npm run dev` (port 3000)  
**Backend URL:** `NEXT_PUBLIC_BACKEND_URL` = `https://vitalsguard-backend.onrender.com` (hoặc `http://localhost:8000`)  
**MQTT Broker URL:** `NEXT_PUBLIC_MQTT_BROKER_URL` = `wss://mqtt.toolhub.app:8084/mqtt`

### Tech Stack
- Next.js 16 App Router, React 19, TypeScript
- TanStack Query v5 (server state / polling)
- Zustand 5 (transient UI state)
- Tailwind CSS 4 + Shadcn UI
- MQTT.js 5 (WebSocket)
- Recharts 3

### Màn hình & Routes

| Route | File | Chức năng |
|-------|------|-----------|
| `/login` | `app/login/page.tsx` | Đăng nhập, lưu JWT vào httpOnly cookie `auth_token` |
| `/` | `app/page.tsx` | Dashboard: grid thiết bị, fall alert overlay, activity trends |
| `/wearers` | `app/wearers/page.tsx` | CRUD hồ sơ người già (`height_cm` quan trọng cho tính bước chân) |
| `/devices` | `app/devices/page.tsx` | Đăng ký thiết bị, assign/unassign cho wearer |
| `/device/[id]` | `app/device/[id]/page.tsx` | Chi tiết thiết bị, lịch sử alert, config |
| `/alerts` | `app/alerts/page.tsx` | Lịch sử té ngã + biểu đồ steps/distance (Recharts) |
| `/data-collection` | `app/data-collection/page.tsx` | Ghi IMU 100Hz real-time, export CSV (Phase 1) |
| `/settings` | `app/settings/page.tsx` | Cấu hình MQTT broker (URL, user, pass) |

### Luồng dữ liệu

**MQTT (real-time, < 1s):**
```
lib/mqtt-client.ts (singleton)
    ↓ subscribe topics
hooks/useMqtt.ts
    ├── eldercare/{id}/imu/raw → data-collection & device-detail charts
    ├── eldercare/{id}/alert/fall → store/useAlertStore.ts → FallDetectionOverlay
    └── eldercare/{id}/telemetry → (subscribed nhưng chưa xử lý payload)
```

**REST API (polling):**
```
hooks/useDeviceData.ts (TanStack Query)
    → services/api.ts (facade)
        → lib/apiClient.ts (inject Bearer JWT từ cookie)
            → FastAPI Backend
```
- `useDevices()` → poll 60s
- `useAlerts()` → poll 30s
- `useWearers()` → static
- `useStepsHistory(days)` → cache 5min

### State Management

| Store | File | Nội dung |
|-------|------|----------|
| `useAlertStore` | `store/useAlertStore.ts` | Real-time alerts (MQTT), device online/offline status |
| `useSettingsStore` | `store/useSettingsStore.ts` | MQTT broker config (persisted localStorage) |

### File quan trọng

| File | Vai trò |
|------|---------|
| `services/api.ts` | Facade tất cả REST calls, map BackendDevice → Device type |
| `lib/apiClient.ts` | HTTP client, inject `Authorization: Bearer {token}` |
| `lib/mqtt-client.ts` | Singleton MQTT, real/mock mode switch, subscriber registry |
| `hooks/useMqtt.ts` | React hook quản lý kết nối MQTT và batch parsing |
| `hooks/useDeviceData.ts` | Tất cả React Query hooks (devices, alerts, wearers, mutations) |
| `store/useAlertStore.ts` | Zustand: addAlert, acknowledgeAlert, setDeviceOnline/Offline |
| `components/shared/GlobalMqttInit.tsx` | Provider khởi tạo MQTT khi app load |
| `lib/imu-parser.ts` | Parse payload format `{ ts, fs, d: [[ax,ay,az,gx,gy,gz],...] }` |
| `lib/alarm.ts` | Web Audio API — phát âm thanh khi fall alert |
| `src/types/index.d.ts` | TypeScript types: Device, Alert, Wearer, IMUSample, v.v. |

### Authentication Flow
1. POST `/api/v1/auth/login` → nhận `{ access_token }`
2. Lưu vào httpOnly cookie `auth_token` (24h, qua Server Action)
3. `apiClient.ts` đọc cookie client-side, inject vào mọi request
4. Logout: xóa cookie → redirect `/login`

---

## 3. Backend

**Đường dẫn:** `HAR_and_Fall-detection-backend/`  
**Chạy:** `uvicorn app.main:app --reload` (port 8000)  
**Prefix:** tất cả endpoints tại `/api/v1/`

### Tech Stack
- FastAPI + Pydantic v2
- SQLAlchemy 2 async + asyncpg (PostgreSQL)
- InfluxDB client + Flux queries
- aiomqtt (async MQTT listener)
- python-jose (JWT), passlib/bcrypt
- Alembic migrations

### PostgreSQL Models (`app/models/domain.py`)

| Model | Bảng | Trường đáng chú ý |
|-------|------|-------------------|
| `Organization` | `organizations` | `name`, `address` — multi-tenant root |
| `User` | `users` | `username`, `password_hash`, `role` (ADMIN/MANAGER), `org_id` |
| `Wearer` | `wearers` | `full_name`, **`height_cm`** (dùng tính stride length), `org_id` |
| `Device` | `devices` | `device_id` (PK = MQTT Client ID), `current_wearer_id` (unique), `battery_pct`, `last_online`, `is_active`, `org_id` |
| `Alert` | `alerts` | `device_id`, `wearer_id`, `alert_type`, `confidence`, `is_resolved` |
| `DeviceEvent` | `device_events` | `event_type` (ACTIVITY_WALKING, DEVICE_STARTED…), `device_id`, `wearer_id` |

### InfluxDB (`app/db/influx_client.py`)

| Bucket | Measurement | Tags | Fields |
|--------|-------------|------|--------|
| `imu_raw` | `imu_raw` | `device_id`, `label` | `ax, ay, az, gx, gy, gz` |
| `telemetry` | `telemetry` | `device_id` | `battery_pct`, `walk_steps`, `run_steps`, `distance_m` |

### API Endpoints

**Auth:**
| Method | Path | Mô tả |
|--------|------|-------|
| POST | `/auth/login` | Login → JWT access_token |

**Wearers:**
| Method | Path | Mô tả |
|--------|------|-------|
| GET | `/wearers/` | Danh sách (org-scoped) |
| POST | `/wearers/` | Tạo mới |
| GET | `/wearers/{id}` | Chi tiết |
| PUT | `/wearers/{id}` | Cập nhật (full_name, height_cm) |
| DELETE | `/wearers/{id}` | Xóa |

**Devices:**
| Method | Path | Mô tả |
|--------|------|-------|
| GET | `/devices/` | Danh sách kèm thông tin wearer (selectinload) |
| POST | `/devices/` | Đăng ký thiết bị mới |
| PUT | `/devices/{id}` | Cập nhật (firmware_version, is_active) |
| DELETE | `/devices/{id}` | Xóa |
| POST | `/devices/{id}/assign` | Gán cho wearer `{ wearer_id }` |
| POST | `/devices/{id}/unassign` | Gỡ khỏi wearer |

**History & Analytics:**
| Method | Path | Mô tả |
|--------|------|-------|
| GET | `/history/alerts` | Lịch sử té ngã (params: `device_id`, `limit=20`) |
| PATCH | `/history/alerts/{id}/resolve` | Đánh dấu đã xử lý |
| GET | `/history/{device_id}/timeline` | UNION alerts + device_events (limit=20) |
| GET | `/history/steps` | Aggregated steps/distance từ InfluxDB (param: `days=7`) |

**Dashboard:**
| Method | Path | Mô tả |
|--------|------|-------|
| GET | `/dashboard/telemetry` | Trạng thái real-time tất cả thiết bị (battery, online, last_online) |

**Data Collection (Phase 1):**
| Method | Path | Mô tả |
|--------|------|-------|
| POST | `/data-collection/sessions` | Lưu batch IMU raw vào InfluxDB (không cần auth) |

### MQTT Bridge (`app/services/mqtt_service.py`)

Subscribe 3 topic patterns:

| Topic | Handler | Action |
|-------|---------|--------|
| `eldercare/+/status` | `process_status()` | Update `battery_pct` + `last_online` Postgres; tính distance → ghi InfluxDB `telemetry` |
| `eldercare/+/alert/fall` | `process_alert()` | Tạo `Alert` record Postgres |
| `eldercare/+/event` | `process_event()` | Tạo `DeviceEvent` record Postgres |

**Distance formula:**
```
distance_m = (walk_steps × 0.415 × height_m) + (run_steps × 0.5 × height_m)
```
`height_m` lấy từ `Wearer.height_cm / 100` (lookup Postgres theo device → wearer).

**Auto-reconnect:** backoff 5s khi mất kết nối.

### File quan trọng

| File | Vai trò |
|------|---------|
| `app/main.py` | FastAPI app, lifespan (khởi/dừng MQTT service), CORS config |
| `app/api/api_v1/api.py` | Aggregate tất cả routers |
| `app/api/api_v1/endpoints/` | Tất cả endpoint handlers |
| `app/api/deps.py` | Auth dependency: JWT → User → org_id |
| `app/models/domain.py` | Tất cả SQLAlchemy models |
| `app/schemas/` | Pydantic request/response schemas |
| `app/services/mqtt_service.py` | MQTT bridge + data processing logic |
| `app/db/session.py` | AsyncSessionLocal, PostgreSQL connection |
| `app/db/influx_client.py` | InfluxDB write + Flux query helpers |
| `app/core/config.py` | Settings từ `.env` (DB URLs, MQTT config, JWT secret) |
| `app/core/security.py` | JWT create/verify, bcrypt hash/verify |

### Multi-tenancy
Mọi query tự động filter `org_id` từ JWT của user đang đăng nhập. Thiết bị assignment có unique constraint: 1 device ↔ 1 wearer tại một thời điểm.

---

## 4. MQTT Topics & Payload (tổng hợp)

| Topic | Chiều | Payload mẫu |
|-------|-------|-------------|
| `eldercare/{id}/status` | Device → Broker | `{ battery_pct, walk_steps, run_steps }` |
| `eldercare/{id}/alert/fall` | Device → Broker | `{ message?, confidence? }` |
| `eldercare/{id}/event` | Device → Broker | `{ event_type, description? }` |
| `eldercare/{id}/imu/raw` | Device → Broker | `{ ts, fs, mode?, d: [[ax,ay,az,gx,gy,gz], ...] }` |
| `eldercare/{id}/telemetry` | Device → Broker | `{ battery_pct, ... }` (FE subscribe, chưa xử lý) |

---

## 5. Gaps & Known Issues

| # | Vị trí | Vấn đề | Mức độ |
|---|--------|--------|--------|
| 1 | FE | Đã xử lý (Fixed): Đã tích hợp proxy.ts làm middleware kiểm tra JWT | Resolved |
| 2 | FE | `eldercare/+/telemetry` subscribe nhưng payload bị bỏ qua | Low |
| 3 | FE | Không có user feedback khi MQTT disconnect | Low |
| 4 | BE | Thiếu CRUD User endpoints (chỉ có `/auth/login`) | Medium |
| 5 | BE | `history/steps` và `history/timeline` không filter `org_id` | High (security) |
| 6 | BE | InfluxDB query failure silent — trả về `[]` không báo lỗi | Low |
| 7 | BE | Không có rate limiting | Low |

---

## 6. Environment Variables

### Frontend (`.env`)
```
NEXT_PUBLIC_BACKEND_URL=https://vitalsguard-backend.onrender.com
NEXT_PUBLIC_MQTT_BROKER_URL=wss://mqtt.toolhub.app:8084/mqtt
NEXT_PUBLIC_MOCK_MQTT=false
```

### Backend (`.env`)
```
DATABASE_URL=postgresql+asyncpg://...  (Supabase)
INFLUXDB_URL=https://influx.tdcq.me
MQTT_BROKER_HOST=mqtt.toolhub.app
MQTT_BROKER_PORT=8883
JWT_SECRET_KEY=...
ACCESS_TOKEN_EXPIRE_MINUTES=1440
DEVICE_ONLINE_TIMEOUT_SECONDS=60
```
