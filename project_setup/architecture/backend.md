# Backend — HAR & Fall Detection API

> **Path:** `backend/` (code trực tiếp; đường dẫn dưới đây tương đối gốc repo backend, vd `app/...`)
> **Cập nhật lần cuối:** 2026-06-17

## Tech Stack
FastAPI + Uvicorn async, PostgreSQL (SQLAlchemy 2.x + asyncpg), InfluxDB (influxdb-client[ciso]), Alembic, JWT (python-jose + passlib/bcrypt), aiomqtt 2.x, Pydantic v2, **numpy + scipy** (windowing IMU ở data_collection), pytest (37 test, harness SQLite in-memory + mock Influx — `tests/conftest.py`), deploy Render (Python 3.12.2).
> ⚠️ `requirements.txt` trước đây THIẾU `numpy`/`scipy` (data_collection import) → đã bổ sung (+ test deps pytest/pytest-asyncio/httpx/aiosqlite). Local test chạy trên venv `.venv` (Python 3.13) — xem mục "Chạy local".

## Cấu trúc thư mục
```
app/
├── main.py                   # FastAPI app, CORS (localhost:3000), MQTT lifespan
├── patch_loop.py             # Windows WindowsSelectorEventLoopPolicy
├── api/
│   ├── deps.py               # get_db (AsyncSession), get_current_user (OAuth2+JWT)
│   └── api_v1/
│       ├── api.py            # Router tổng hợp tất cả sub-routers
│       └── endpoints/
│           ├── auth.py           # POST /login → JWT access_token (expire 1440 min)
│           ├── devices.py        # CRUD devices + POST /assign, /unassign
│           ├── wearers.py        # CRUD wearers (full_name, height_cm)
│           ├── dashboard.py      # GET /telemetry (battery, last_online, is_active per device)
│           ├── data_collection.py# POST /sessions (raw IMU → windowing ML → InfluxDB imu_windowed)
│           └── history.py        # GET /alerts, PATCH resolve, GET /steps (Flux), GET /timeline
├── core/
│   ├── config.py             # Pydantic BaseSettings (DATABASE_URL, INFLUX_*, MQTT_*, SECRET_KEY)
│   └── security.py           # create_access_token, verify_password, get_password_hash (bcrypt)
├── db/
│   ├── session.py            # AsyncSessionLocal (asyncpg engine)
│   └── influx_client.py      # InfluxDB singleton: write_api (ASYNC) + query_api
├── models/
│   ├── base.py               # DeclarativeBase + created_at/updated_at mixins + Organization model
│   └── domain.py             # User, Wearer, Device, Alert, DeviceEvent (SQLAlchemy 2.x)
├── schemas/
│   ├── domain.py             # Pydantic Device/Wearer/Alert Create/Update/Response
│   ├── mqtt.py               # StatusPayload (alias: battery, steps), AlertPayload, EventPayload
│   ├── user.py               # Token, TokenData, UserCreate, UserResponse
│   ├── data_collection.py    # IMUSampleSchema, DataCollectionSessionCreate
│   └── history.py            # TimelineEntry, AlertHistory, StepHistoryResponse
└── services/
    └── mqtt_service.py       # MQTT bridge (286 lines) — core pipeline
```

## PostgreSQL Schema (sau 5 Alembic migrations)
```
organizations: id(UUID PK), name, address, created_at, updated_at
users:         id(UUID PK), username[unique+idx], password_hash, role(ADMIN|MANAGER), org_id FK
wearers:       id(UUID PK), full_name, height_cm(float), org_id FK
devices:       device_id(str PK), firmware_version, current_wearer_id[unique FK], is_active, telemetry_interval(int),
               fall_threshold(float, default 0.6), org_id FK, battery_pct(int), last_online(datetime), created_at, updated_at
alerts:        id(UUID PK), device_id FK, wearer_id FK(optional), alert_type,
               confidence(float 0-1), is_resolved(bool)
device_events: id(UUID PK), device_id FK, wearer_id FK(optional), event_type, description
```

**Migrations (Alembic):**
1. `4c400002ec88` — initial schema (organizations, users, wearers, devices)
2. `4686844feabb` — add timestamp mixins (created_at, updated_at with timezone)
3. `56ec4e5d8c21` — add alerts + device_events tables; thêm battery_pct, last_online vào devices
4. `f1eda2d1e58f` — add org_id vào devices (backfill + NOT NULL)
5. `cade8bab7f74` — add telemetry_interval to devices (5s default)
6. `a7b3f9c1d2e4` — add fall_threshold to devices (0.6 default)

## InfluxDB Measurements
| Measurement | Tags | Fields |
|-------------|------|--------|
| `telemetry` | device_id, wearer_id, state, ai_pred | battery_pct, steps, walk_steps, run_steps, ai_conf, distance_m |
| `imu_windowed` | device_id, label, session_id, window_id | ax, ay, az, gx, gy, gz |

## API Endpoints
| Method | Path | Mô tả |
|--------|------|-------|
| POST | `/api/v1/auth/login` | Login OAuth2 → access_token (JWT) |
| GET/POST/PUT/DELETE | `/api/v1/wearers/` | CRUD bệnh nhân |
| GET/POST/PUT/DELETE | `/api/v1/devices/` | CRUD thiết bị ESP32 |
| POST | `/api/v1/devices/{id}/assign` | Gán thiết bị cho wearer (unique) |
| POST | `/api/v1/devices/{id}/unassign` | Gỡ gán |
| POST | `/api/v1/devices/{id}/command` | Gửi lệnh realtime (start/stop_stream) → backend publish MQTT (B5). PUT `/devices/{id}` đổi `telemetry_interval`/`fall_threshold` → publish `set_interval`/`set_fall_threshold` |
| GET | `/api/v1/dashboard/telemetry` | Trạng thái realtime tất cả devices |
| GET | `/api/v1/history/alerts` | Lịch sử alert ngã (từ Postgres, giới hạn 20) |
| PATCH | `/api/v1/history/alerts/{id}/resolve` | Đánh dấu alert đã xử lý |
| GET | `/api/v1/history/steps` | Bước chân theo ngày (InfluxDB Flux, daily max aggregate) |
| GET | `/api/v1/history/{device_id}/timeline` | Timeline UNION ALL alerts + events |
| GET | `/api/v1/history/{device_id}/telemetry` | Lịch sử telemetry từ InfluxDB (dựa trên eldercare/{device_id}/status) |
| POST | `/api/v1/data-collection/sessions` | Lưu session IMU, tiền xử lý và cắt windowing (Scipy) → `imu_windowed` |

## MQTT Service (mqtt_service.py) — Core Pipeline
Subscribe 3 topics với wildcard `+`:
- **`eldercare/+/status`** → `process_status()`: cập nhật Device.battery_pct, last_online, telemetry_interval, tính distance_m, ghi InfluxDB
- **`eldercare/+/alert/fall`** → `process_alert()`: tạo Alert record Postgres (is_resolved=False)
- **`eldercare/+/event`** → `process_event()`: tạo DeviceEvent record Postgres

> ℹ️ Firmware publish cảnh báo lên `eldercare/{id}/alert/fall` khớp subscribe này. `AlertPayload`: chỉ `confidence` bắt buộc, `user_name`/`message` optional (process_alert chỉ dùng confidence). `handle_message` log `[MQTT][DROP]` kèm payload khi validation fail (không nuốt im lặng). Topic `event` có handler nhưng **firmware chưa publish** (còn nợ).

**Reconnection:** vòng lặp async, MqttError → sleep 5s → retry.

## Thuật toán tính khoảng cách
```python
height_m = wearer.height_cm / 100
distance_m = (walk_steps * 0.415 * height_m) + (run_steps * 0.5 * height_m)
```
Fetch `wearer.height_cm` từ DB tại thời điểm xử lý mỗi MQTT message. `StatusPayload` đã nhận `walk_steps`/`run_steps` riêng (firmware D-010) — process_status dùng đúng 2 field này (không còn dùng tổng `steps × 0.415`).

## is_online Logic (schemas/domain.py DeviceResponse)
```python
is_online = (datetime.now(UTC) - device.last_online).total_seconds() < settings.DEVICE_ONLINE_TIMEOUT_SECONDS
# Default timeout = 60s
```

## Chạy local trên Windows (gotcha)
- **Event loop:** chạy `uvicorn app.main:app` (CLI) trên Windows tạo **ProactorEventLoop** TRƯỚC khi `patch_loop` kịp set Selector → asyncpg/aiomqtt lỗi `add_reader NotImplementedError`. Dùng `run_local.py` (set `WindowsSelectorEventLoopPolicy` rồi `asyncio.run(server.serve())` với `loop="none"`).
- **File env:** `config.py` đọc đúng tên **`.env`** (không phải `env`). Nếu chỉ có file `env` → `Settings` thiếu `DATABASE_URL`, app không khởi động. `.env` đã trong `.gitignore`.
- **Python:** target 3.12.2 (Render); local test trên 3.13 OK (deps `>=` resolve bản tương thích).

## Dependency Injection (api/deps.py)
- `get_db()` → yield AsyncSession, commit on success, rollback on exception
- `get_current_user()` → decode JWT, query User by `sub` claim, raise 401 nếu không hợp lệ

## Cấu hình (.env / core/config.py)
```
DATABASE_URL          # PostgreSQL asyncpg URL
INFLUXDB_URL          # default http://localhost:8086
INFLUXDB_TOKEN
INFLUXDB_ORG
INFLUXDB_BUCKET
MQTT_HOST
MQTT_PORT             # 8883 (mqtts) trên Render
MQTT_PROTOCOL         # mqtts | wss
MQTT_WS_PATH          # /mqtt
MQTT_USERNAME
MQTT_PASSWORD
SECRET_KEY
DEVICE_ONLINE_TIMEOUT_SECONDS  # 60
ACCESS_TOKEN_EXPIRE_MINUTES    # 1440
```
