# Backend — HAR & Fall Detection API

> **Path:** `backend/` (code trực tiếp; đường dẫn dưới đây tương đối gốc repo backend, vd `app/...`)
> **Cập nhật lần cuối:** 2026-06-29

## Tech Stack
FastAPI + Uvicorn async, PostgreSQL (SQLAlchemy 2.x + asyncpg), InfluxDB (influxdb-client[ciso]), Alembic, JWT (python-jose + passlib/bcrypt), aiomqtt 2.x, Pydantic v2, pytest (harness SQLite in-memory + mock Influx — `tests/conftest.py`; +`tests/test_verification_api.py` 18 test cho verify recording), deploy Render (Python 3.12.2).
> ℹ️ `numpy`/`scipy` đã GỠ khỏi `requirements.txt` cùng với endpoint `data_collection` (windowing IMU train) — không còn code nào dùng. Test deps: pytest/pytest-asyncio/httpx/aiosqlite. Local test chạy trên venv `.venv` (Python 3.13) — xem mục "Chạy local".

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
│           ├── history.py        # GET /alerts, PATCH resolve, GET /steps (Flux), GET /timeline
│           └── verification.py   # Verify recording: sessions CRUD + submit data → .txt SisFall, download, export ZIP
├── core/
│   ├── config.py             # Pydantic BaseSettings (DATABASE_URL, INFLUX_*, MQTT_*, SECRET_KEY)
│   └── security.py           # create_access_token, verify_password, get_password_hash (bcrypt)
├── db/
│   ├── session.py            # AsyncSessionLocal (asyncpg engine)
│   └── influx_client.py      # InfluxDB singleton: write_api (ASYNC) + query_api
├── models/
│   ├── base.py               # DeclarativeBase + created_at/updated_at mixins + Organization model
│   └── domain.py             # User, Wearer, Device, Alert, DeviceEvent, VerificationSession (SQLAlchemy 2.x)
├── schemas/
│   ├── domain.py             # Pydantic Device/Wearer/Alert Create/Update/Response
│   ├── mqtt.py               # StatusPayload (alias: battery, steps), AlertPayload, EventPayload
│   ├── user.py               # Token, TokenData, UserCreate, UserResponse
│   ├── verification.py       # VerificationSessionCreate/Data/Response
│   └── history.py            # TimelineEntry, AlertHistory, StepHistoryResponse
└── services/
    ├── mqtt_service.py       # aiomqtt listener (status, alert, event), write InfluxDB + Postgres
    └── alert_maintenance.py  # Background task (asyncio loop) auto-resolve alert > 24h
```

## PostgreSQL Schema
> Chi tiết đầy đủ + Mermaid ERD xem tại [`architecture/db_schema.md`](db_schema.md)

```
organizations: id(UUID PK), name, address, created_at, updated_at
users:         id(UUID PK), username[unique+idx], password_hash, role(ADMIN|MANAGER), org_id FK, created_at, updated_at
wearers:       id(UUID PK), full_name, height_cm(float), org_id FK, created_at, updated_at
devices:       device_id(str PK = id ngữ nghĩa esp32_eldercare_NN do BE sinh), mac(str[unique+idx] = MAC = khóa topic MQTT),
               firmware_version(auto-report), current_wearer_id[unique FK→wearers], is_active,
               telemetry_interval(int,5s), fall_threshold(float,0.25), fall_cooldown(int,15s),
               fall_confirm_window(int,4s = cửa sổ xác nhận post-impact, D-021), rssi_interval(int,300s = chu kỳ đo RSSI 4G, 0=tắt, D-022), stream_timeout(int),
               org_id FK→organizations, battery_pct(int), last_rssi(int), last_online(datetime), created_at, updated_at
alerts:        id(UUID PK), device_id FK, wearer_id FK(nullable), alert_type, confidence(float), is_resolved(bool), created_at, updated_at
device_events: id(UUID PK), device_id FK, wearer_id FK(nullable), event_type, description, created_at, updated_at
verification_sessions: id(UUID PK), device_id FK, wearer_id FK(nullable, snapshot), subject_code(str4 SVxx),
               activity_code(str3 D01/F06), trial_no(str3 R01), sample_count(int,null), duration_s(float,null),
               file_path(str500,null → .txt SisFall trên đĩa), org_id FK, created_at, updated_at  [idx: org_id, device_id]
```

**Migrations (Alembic — 5 file tracked):**
1. `4c400002ec88` — initial schema (organizations, users, wearers, devices)
2. `4686844feabb` — add timestamp mixins (created_at, updated_at with timezone)
3. `56ec4e5d8c21` — add alerts + device_events; thêm battery_pct, last_online vào devices
4. `f1eda2d1e58f` — add org_id vào devices (backfill + NOT NULL)
5. `cade8bab7f74` — add telemetry_interval to devices (5s default)
6. `a8f3c2d1e9b5` — add verification_sessions table (+ idx org_id, device_id)
7. `a6efb11dc16b` — add stream_timeout vào devices
8. `c1d2e3f4a5b6` — add `mac` vào devices (unique+index)
9. `d1e2f3a4b5c6` (head) — add `fall_confirm_window` vào devices (server_default 4, D-021)
10. *(kế hoạch D-022)* `add_rssi_interval_to_devices` — add `rssi_interval` vào devices (server_default 300); down_revision `d1e2f3a4b5c6`

> ⚠️ `fall_threshold`, `fall_cooldown`, `last_rssi` có trong `domain.py` nhưng không có migration file — đã thêm trực tiếp vào DB. Cần `alembic revision --autogenerate` nếu deploy lại từ đầu.

## InfluxDB Measurements
| Measurement | Tags | Fields |
|-------------|------|--------|
| `telemetry` | device_id, wearer_id, state, ai_pred | battery_pct, steps, walk_steps, run_steps, ai_conf, distance_m (+ rssi khi firmware gửi) |

> ℹ️ Chỉ còn measurement `telemetry` (ghi bởi `mqtt_service.py` mỗi gói status; đọc bởi `/history/steps` + `/history/{id}/telemetry`). Measurement `imu_windowed` (data thu train) **đã ngừng** — endpoint `data_collection` bị gỡ. Data cũ trong bucket (nếu có) cần `influx delete` thủ công.

## API Endpoints
| Method | Path | Mô tả |
|--------|------|-------|
| POST | `/api/v1/auth/login` | Login OAuth2 → access_token (JWT) |
| GET/POST/PUT/DELETE | `/api/v1/wearers/` | CRUD bệnh nhân |
| GET/POST/PUT/DELETE | `/api/v1/devices/` | CRUD thiết bị ESP32 |
| POST | `/api/v1/devices/{id}/assign` | Gán thiết bị cho wearer (unique) |
| POST | `/api/v1/devices/{id}/unassign` | Gỡ gán |
| POST | `/api/v1/devices/{id}/command` | Gửi lệnh realtime (start/stop_stream) → backend publish MQTT (B5). PUT `/devices/{id}` đổi bất kỳ tham số config bền vững (`telemetry_interval`/`fall_threshold`/`fall_cooldown`/`fall_confirm_window`/`rssi_interval`/`stream_timeout`) → publish gói gộp lên `config/set` |
| GET | `/api/v1/dashboard/telemetry` | Trạng thái realtime tất cả devices |
| GET | `/api/v1/history/alerts` | Lịch sử alert ngã (từ Postgres, giới hạn 20) |
| PATCH | `/api/v1/history/alerts/{id}/resolve` | Đánh dấu alert đã xử lý |
| GET | `/api/v1/history/steps` | Bước chân theo ngày (InfluxDB Flux, daily max aggregate) |
| GET | `/api/v1/history/{device_id}/timeline` | Timeline UNION ALL alerts + events |
| GET | `/api/v1/history/{device_id}/telemetry` | Lịch sử telemetry từ InfluxDB (dựa trên eldercare/{device_id}/status) |
| POST | `/api/v1/data-collection/sessions` | Tạo session verify; validate device thuộc org (404) + đã mount wearer (400); snapshot wearer_id |
| POST | `/api/v1/data-collection/sessions/{id}/data` | Nhận `samples[]` (g/deg/s), lưu raw `.txt` SisFall (`verification_dataset/<SV>/<ACT>_<SV>_<R>.txt`), cập nhật sample_count/duration_s/file_path |
| GET | `/api/v1/data-collection/sessions` | List session của org (filter `subject_code`/`activity_code`), mới nhất trước |
| GET | `/api/v1/data-collection/sessions/{id}/download` | Tải 1 file `.txt` (FileResponse) |
| GET | `/api/v1/data-collection/export` | ZIP toàn bộ `.txt` của org (StreamingResponse, arcname `SV/ACT_SV_R.txt`) |

> ℹ️ Router file vẫn là `endpoints/verification.py` + schema `VerificationSession*` + bảng `verification_sessions` (tên nội bộ), nhưng **prefix + Swagger tag = `data-collection`** (thay endpoint train cũ đã xoá) cho nhất quán với FE.

## MQTT Service (mqtt_service.py) — Core Pipeline
> **Khóa topic = MAC** (vân tay phần cứng), KHÔNG phải device_id. Handler khớp Device theo `mac` qua
> `_get_or_create_device_by_mac()` → **auto-provision**: mac lạ → sinh `device_id` ngữ nghĩa
> `esp32_eldercare_NN` (`_next_device_id`, tuần tự trong org) + lưu mac. Org của deployment =
> `settings.ORG_ID` hoặc org duy nhất (`_resolve_org_id`). Xem [DECISIONS.md](DECISIONS.md) D-020.

Subscribe 4 topics với wildcard `+`:
- **`eldercare/+/config/status`** → `process_config_status()`: get-or-create device theo mac (điểm
  provision đẹp nhất — fire lúc connect/reconnect), đồng bộ config (interval/threshold/cooldown/**fall_confirm_window**/**rssi_interval**/timeout)
  + cập nhật **`Device.firmware_version`** từ `fw_version` (auto-report OTA).
- **`eldercare/+/status`** → `process_status()`: get-or-create theo mac (provision dự phòng); cập nhật
  battery_pct, last_online, tính distance_m, ghi InfluxDB (**tag `device_id` = id ngữ nghĩa**, không phải mac).
- **`eldercare/+/alert/fall`** → `process_alert()`: tạo Alert (FK `device_id` ngữ nghĩa); skip nếu chưa gán wearer.
- **`eldercare/+/event`** → `process_event()`: tạo DeviceEvent record Postgres.

> Backend publish lệnh/config/OTA tới `eldercare/<device.mac>/...` (tra `mac` từ PK). Nếu `mac` còn None
> (device pre-register chưa online) → trả 409.
> ℹ️ `AlertPayload`: chỉ `confidence` bắt buộc. `handle_message` log `[MQTT][DROP]` khi validation fail.
> Topic `event` có handler nhưng **firmware chưa publish** (còn nợ).

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
