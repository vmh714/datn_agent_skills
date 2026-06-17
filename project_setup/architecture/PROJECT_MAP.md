# PROJECT MAP — Index tra cứu nhanh (đọc đầu tiên)

> **Cập nhật lần cuối:** 2026-06-17 · **Verified against firmware code @ 2026-06-17**
> Mục đích: tra "cái gì ở đâu" trong **một** file thay vì grep/đọc cả codebase. Mở full file chỉ khi cần SỬA.
> Quy ước: `path:line` là điểm neo có thể click. Phần Firmware có `file:line` đã verify; Backend/Frontend trỏ tới doc canonical tương ứng.

---

## 1. FIRMWARE (ESP32-S3, ESP-IDF) — gốc repo `firmware/`
> Mọi `path:line` mục này tương đối **gốc project firmware** (`components/...`, `main/...`) — portable dù firmware ở `firmware/` (máy gốc) hay `firmware/<repo>/` (máy clone).

### 1.1 Pin map — `main/hardware_config.h`
| Chức năng | Pin |
|---|---|
| I2C SCL / SDA (MPU6050) | GPIO9 / GPIO8 (`I2C_NUM_0`) |
| MPU6050 INT | GPIO7 |
| A7680C UART TX / RX | GPIO43 / GPIO44 (`UART_NUM_2`) |
| A7680C PWRKEY | GPIO38 |
| Switch mạng | macro `NETWORK_USE_CELLULAR` (comment = WiFi dev) |
| APN | `A7680C_APN "v-internet"` |

### 1.2 Components & Public API
| Component | Loại | API public (header) |
|---|---|---|
| `drv_mpu6050` | driver | `mpu6050_init(bus)`, `mpu6050_config`, `mpu6050_read`, `mpu6050_read_raw`, `mpu6050_raw_to_float`, `mpu6050_read_fifo`, `mpu6050_reset_fifo`, `mpu6050_get_sample_rate`, `mpu6050_calibrate_gyro` — `include/mpu6050.h:126-179` |
| `drv_a7680c` | driver | `drv_a7680c_init(pwrkey)`, `drv_a7680c_power_on`, `drv_a7680c_power_off` — `include/drv_a7680c.h` (chỉ GPIO nguồn) |
| `drv_battery` | driver | `drv_battery_init(gpio,ratio)`, `drv_battery_read_mv`, `drv_battery_read_percent` — `include/drv_battery.h` (ADC + cầu phân áp) |
| `lib_kalman` | lib | `kalman_init`/`kalman_get_angle` (2-state) `:31/:41`; `kalman_1d_init`/`kalman_1d_update` (1D) `:66/:74` — `include/kalman_filter.h` |
| `lib_pedometer` | lib | `pedometer_init(fs)`, `pedometer_process(ax,ay,az)→bool` — `include/pedometer.h` |
| `lib_model` | lib | `g_model_data[]`, `g_model_data_len` — `include/model_data.h` (ResNet-1D INT8, in (200,6), out 5 lớp, 81384B) |
| `lib_tinyml` | lib | `tflite_init`, `tflite_run_inference`, `get_input_bytes`, `tflite_run_inference_with_data` — `include/tflite_wrapper.h:14/19/47/55`; enum `ai_posture_class_t:25`, struct `ai_inference_result_t:35` |
| `svc_imu` | service | `imu_service_init(int_pin)`, `imu_service_get_latest_pitch`, `imu_service_register_batch_callback`, `imu_service_get_steps(walk,run)` — `include/imu_service.h:40/46/54/+` |
| `svc_ai` | service | `svc_ai_init`, `svc_ai_process_window`, `svc_ai_get_latest_prediction`, `svc_ai_get_latest_confidence` — `include/svc_ai.h:22/35/41/47` |
| `svc_cloud` | service | `svc_cloud_init`, `svc_cloud_is_connected`, `svc_cloud_publish`, `svc_cloud_enqueue_imu_batch` — `include/svc_cloud.h:16/22/32/40` |
| `svc_network` | service | `svc_network_init(ssid,pass)` (WiFi), `svc_network_init_cellular(cfg)` (4G/PPP), `svc_network_is_connected` — `include/svc_network.h` |
| `sys_manager` | system | `sys_manager_init`, `sys_manager_get_state`, `sys_manager_set_state` — `include/sys_manager.h:63/69/75` |

### 1.3 FSM — `sys_manager/include/sys_manager.h:8-55`
- **States** (`:8`): `STATE_INIT`, `STATE_CONNECTING`, `STATE_NORMAL`, `STATE_STREAMING`, `STATE_OTA`, `STATE_ERROR`.
- **Event bases** (`:19`): `SYS_EVENT`, `NET_EVENT`, `CLOUD_EVENT`, `IMU_EVENT`, `AI_EVENT`.
- **Event IDs**: `NET_EVT_{WIFI_CONNECTED,CELLULAR_CONNECTED,DISCONNECTED}` · `CLOUD_EVT_MQTT_CONNECTED`, `CLOUD_CMD_{START,STOP}_STREAM` · `IMU_EVT_{BATCH_READY(deprecated),WINDOW_READY}` · `AI_EVT_FALL_DETECTED`.
- Handler tự lái FSM theo NET/CLOUD event (đăng ký trong `sys_manager_init`). OTA/ERROR transition **chưa hiện thực**.

### 1.4 HAR / AI
- Lớp: `Walk(0) Run(1) Idle(2) Transition(3) Fall(4) Unknown(5)` — `tflite_wrapper.h:25`.
- Ngưỡng Fall: `prob[FALL] >= 0.6` ép predicted=Fall (`tflite_wrapper.cpp:235`); `svc_ai` phát `AI_EVT_FALL_DETECTED`.
- Posture: `Idle` + pitch ∈ [-45,45] → đứng/ngồi, ngoài → nằm (`svc_ai.c`).

### 1.5 Hằng số chốt
`IMU_WINDOW_SIZE=200` (2s), `IMU_BATCH_SIZE=50` (0.5s) — `imu_service.h:9-10` · Tensor arena `100KB` PSRAM — `tflite_wrapper.cpp:22` · `FALL_COOLDOWN_US=15s` — `svc_cloud.c:304` · telemetry interval mặc định `5000ms` (NVS `config/tel_int`) — `svc_cloud.c:28` · LTE-only `AT+CNMP=38` · PWRKEY Ton~50ms/Toff 2.5s.

---

## 2. MQTT TOPICS (nguồn chuẩn = firmware `svc_cloud.c`, prefix `eldercare/`)
| Topic | Hướng | QoS | Payload |
|---|---|---|---|
| `eldercare/{id}/status` | pub | 0 | `battery, steps, walk_steps, run_steps, state, ai_pred, ai_conf, interval` |
| `eldercare/{id}/alert/fall` | pub | 1 | `{user_name, message, confidence}` |
| `eldercare/{id}/imu_stream` | pub | 0 | `{ts,fs,cnt,data_b64}` (int16 base64) |
| `eldercare/{id}/command` | sub | 1 | `{"action":start_stream\|stop_stream\|set_interval\|ota_update,"val":<sec>}` |

> Firmware/BE/FE/`fake_device.py` đều dùng `alert/fall`. Firmware **chưa** publish `event`. Chi tiết payload: `architecture/protocol.md`.

---

## 3. BACKEND (FastAPI) — chi tiết tại `architecture/backend.md`
- **Endpoints**: `auth/login`, CRUD `wearers`/`devices`, `devices/{id}/assign|unassign`, `dashboard/telemetry`, `history/alerts(+resolve)`, `history/steps`, `history/{id}/timeline`, `history/{id}/telemetry`, `data-collection/sessions`.
- **PostgreSQL**: organizations, users, wearers, devices (+telemetry_interval), alerts, device_events (5 migrations).
- **InfluxDB**: `telemetry` (battery_pct, steps, ai_conf, distance_m), `imu_windowed` (ax..gz).
- **MQTT bridge**: `mqtt_service.py` sub `eldercare/+/{status,alert/fall,event}`. Distance = `walk_steps×0.415×h + run_steps×0.5×h`.

## 4. FRONTEND (Next.js) — chi tiết tại `architecture/frontend.md`
- MQTT WS singleton `lib/mqtt-client.ts`; sub `eldercare/+/{alert/fall,status}` (status = realtime telemetry, map `battery`→`battery_pct`); Zustand stores (alert/telemetry); IMU parser; FallDetectionOverlay.
- Resolve alert: `api.acknowledgeAlert(id, deviceId)` truyền `?device_id=` để hybrid fallback (protocol §4) scope đúng thiết bị.

## 5. LUỒNG / SƠ ĐỒ
- Sơ đồ tích hợp (4 loại): `architecture/system_integration.md`.
- Quyết định thiết kế & lý do: `architecture/DECISIONS.md`.
- Debug web fullstack (fix pack 2026-06-17): `architecture/debug_web_fullstack.md` + `../web_fullstack_fixes_2026-06-17.md`.

---
*File này nên được tái sinh bằng `tools/gen_project_map.py` sau thay đổi lớn (mục Firmware), rồi rà lại thủ công.*
