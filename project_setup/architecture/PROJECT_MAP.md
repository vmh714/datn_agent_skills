# PROJECT MAP — Index tra cứu nhanh (đọc đầu tiên)

> **Cập nhật lần cuối:** 2026-06-30 · **Verified against firmware code @ 2026-06-30, SisFall train code @ 2026-06-22** (D-019/D-021/D-022/D-024/D-025/D-026 cập nhật 2026-06-30)
> Mục đích: tra "cái gì ở đâu" trong **một** file thay vì grep/đọc cả codebase. Mở full file chỉ khi cần SỬA.
> Quy ước: `path:line` là điểm neo có thể click. Phần Firmware có `file:line` đã verify; Backend/Frontend trỏ tới doc canonical tương ứng.

---

## 1. FIRMWARE (ESP32-S3, ESP-IDF) — gốc repo `firmware/`
> Mọi `path:line` mục này tương đối **gốc project firmware** (`components/...`, `main/...`) — portable dù firmware ở `firmware/` (máy gốc) hay `firmware/<repo>/` (máy clone).

### 1.1 Pin map — `components/sys_manager/include/hardware_config.h`
| Chức năng | Pin |
|---|---|
| I2C SCL / SDA (MPU6050) | GPIO9 / GPIO8 (`I2C_NUM_0`) |
| MPU6050 INT | GPIO7 |
| A7680C UART TX / RX | GPIO5 / GPIO4 (`UART_NUM_2`) (D-018) |
| A7680C RST | GPIO6 (Vô hiệu hóa trong code, xem D-019) |
| APN | `A7680C_APN "v-internet"` |
| Battery monitor | GPIO1 (ADC) |

### 1.2 Components & Public API
| Component | Loại | API public (header) |
|---|---|---|
| `drv_mpu6050` | driver | `mpu6050_init(bus)`, `mpu6050_config`, `mpu6050_read`, `mpu6050_read_raw`, `mpu6050_raw_to_float`, `mpu6050_read_fifo`, `mpu6050_reset_fifo`, `mpu6050_get_sample_rate`, `mpu6050_calibrate_gyro` — `include/mpu6050.h:126-179` |
| `drv_a7680c` | driver | `drv_a7680c_init(rst_pin)`, `drv_a7680c_reset(did_reset)`, `drv_a7680c_emergency_mqtt_publish(...)` — `include/drv_a7680c.h` (GPIO reset & AT khẩn cấp) |
| `drv_battery` | driver | `drv_battery_init(gpio,ratio)`, `drv_battery_read_mv`, `drv_battery_read_percent` — `include/drv_battery.h` (ADC + cầu phân áp) |
| `lib_kalman` | lib | `kalman_init`/`kalman_get_angle` (2-state) `:31/:41`; `kalman_1d_init`/`kalman_1d_update` (1D) `:66/:74` — `include/kalman_filter.h` |
| `lib_pedometer` | lib | `pedometer_init(fs)`, `pedometer_process(ax,ay,az)→bool` — `include/pedometer.h` |
| `lib_model` | lib | `g_model_data[]`, `g_model_data_len` — `include/model_data.h` (ResNet-1D INT8, in (200,6), out 5 lớp, 81384B) |
| `lib_tinyml` | lib | `tflite_init`, `tflite_run_inference`, `get_input_bytes`, `tflite_run_inference_with_data` — `include/tflite_wrapper.h:14/19/47/55`; enum `ai_posture_class_t:25`, struct `ai_inference_result_t:35` |
| `svc_imu` | service | `imu_service_init(int_pin)`, `imu_service_get_latest_roll`, `imu_service_register_batch_callback`, `imu_service_get_steps(walk,run)`, `imu_service_get_last_impact(out)`→`{ts_us,peak_g,had_freefall}` (D-021) — `include/imu_service.h` |
| `svc_ai` | service | `svc_ai_init`, `svc_ai_process_window`, `svc_ai_get_latest_prediction`, `svc_ai_get_latest_confidence`, `svc_ai_set_confirm_window_ms`/`svc_ai_get_confirm_window_ms` (D-021) — `include/svc_ai.h` |
| `svc_cloud` | service | `svc_cloud_init`, `svc_cloud_is_connected`, `svc_cloud_publish`, `svc_cloud_enqueue_imu_batch` — `include/svc_cloud.h:16/22/32/40` |
| `svc_network` | service | `svc_network_init(ssid,pass)` (WiFi), `svc_network_init_cellular(cfg)` (4G/PPP), `svc_network_is_connected`, `svc_network_get_rssi`, `svc_network_set_rssi_interval_ms`/`get` (0=tắt, D-022) — `include/svc_network.h` |
| `sys_manager` | system | `sys_manager_init`, `sys_manager_get_state`, `sys_manager_set_state`, `sys_manager_bump_comms_critical(ms)`/`sys_manager_is_comms_critical` (D-022) — `include/sys_manager.h` |

### 1.3 FSM — `sys_manager/include/sys_manager.h:8-55`
- **States** (`:8`): `STATE_INIT`, `STATE_CONNECTING`, `STATE_NORMAL`, `STATE_STREAMING`, `STATE_OTA`, `STATE_ERROR`.
- **Event bases** (`:19`): `SYS_EVENT`, `NET_EVENT`, `CLOUD_EVENT`, `IMU_EVENT`, `AI_EVENT`.
- **Event IDs**: `SYS_EVT_{READY,ENTER_STREAM_MODE,ENTER_NORMAL_MODE,HARDWARE_ERROR}` · `NET_EVT_{WIFI_CONNECTED,CELLULAR_CONNECTED,DISCONNECTED}` · `CLOUD_EVT_MQTT_CONNECTED`, `CLOUD_CMD_{START,STOP,OTA_UPDATE}` · `IMU_EVT_{BATCH_READY(deprecated),WINDOW_READY}` · `AI_EVT_FALL_DETECTED`.
- Handler tự lái FSM theo NET/CLOUD/SYS event (đăng ký trong `sys_manager_init`). Khi nhận `SYS_EVT_HARDWARE_ERROR`, vào `STATE_ERROR` và auto-reboot.
- **FSM phụ trong `svc_ai`** (độc lập system FSM): `FALL_FSM_NORMAL`/`CONFIRMING` cho Post-Impact Confirmation (D-021).
- **Cờ comms-critical** ở `sys_manager` (monotonic expiry): `svc_ai` (vào CONFIRMING) + `svc_cloud` (sau alert) bump; `svc_network` đọc để hoãn đo RSSI (D-022).

### 1.4 HAR / AI
- Lớp: `Walk(0) Run(1) Idle(2) Transition(3) Fall(4) Unknown(5)` — `tflite_wrapper.h:25`.
- Ngưỡng Fall: `prob[FALL] >= 0.25` ép predicted=Fall (`tflite_wrapper.cpp:235`) = **ML trigger**; `svc_ai` KHÔNG phát ngay mà vào FSM `CONFIRMING` quan sát post-impact (`Idle`+ROLL=lying) đa số window trong `fall_confirm_window`s → **CONFIRMED** mới phát `AI_EVT_FALL_DETECTED`; ABORT nếu hồi phục (Walk/Run+upright). Impact/free-fall (SVM accel thô, `svc_imu`) = bằng chứng boost. (D-021)
- Posture: `Idle` + pitch ∈ [-45,45] → đứng/ngồi, ngoài → nằm (`svc_ai.c`).

### 1.5 Hằng số chốt
`IMU_WINDOW_SIZE=200` (2s), `IMU_BATCH_SIZE=50` (0.5s) — `imu_service.h:9-10` · Tensor arena `100KB` PSRAM — `tflite_wrapper.cpp:22` · `FALL_COOLDOWN_US` mặc định 15s (NVS `fall_cd`) — `svc_cloud.c` · **`fall_confirm_window` mặc định 4s, range 1–15 (NVS `fall_cf`)** — `svc_ai.c` (D-021) · **`rssi_interval` mặc định 300s, `0=tắt`, clamp non-zero ≥60 (NVS `rssi_int`)** — `svc_network.c` (D-022) · free-fall<0.6g/impact>2.5g (SVM thô) — `svc_imu.c` · telemetry interval mặc định `5000ms` (NVS `tel_int`) — `svc_cloud.c` · LTE-only `AT+CNMP=38` · PWRKEY Ton~50ms/Toff 2.5s.

---

## 2. MQTT TOPICS (nguồn chuẩn = firmware `svc_cloud.c`, prefix `eldercare/`)
> **`{id}` = MAC chip** (firmware lấy từ eFuse), KHÔNG phải device_id ngữ nghĩa. Backend khớp theo MAC,
> auto-provision sinh `device_id` `esp32_eldercare_NN`, publish lệnh tới `eldercare/<device.mac>/...`.
> Xem `architecture/DECISIONS.md` D-020.

| Topic | Hướng | QoS | Payload |
|---|---|---|---|
| `eldercare/{mac}/status` | pub | 0 | `battery, steps, walk_steps, run_steps, state, ai_pred, ai_conf, interval` |
| `eldercare/{mac}/config/status` | pub | 1 | `interval, fall_threshold, fall_cooldown, fall_confirm_window, rssi_interval, stream_timeout, fw_version` (fire lúc connect/reconnect → auto-provision + cập nhật firmware_version; cũng echo sau mỗi `config/set`) |
| `eldercare/{mac}/alert/fall` | pub | 1 | `{user_name, message, confidence}` |
| `eldercare/{mac}/imu_stream` | pub | 0 | `{ts,fs,cnt,data_b64}` (int16 base64) |
| `eldercare/{mac}/event` | pub | 1 | `{"event_type": "...", "description": "..."}` (LOW_BATTERY, HARDWARE_ERROR) |
| `eldercare/{mac}/command` | sub | 1 | `{"action":start_stream\|stop_stream\|set_interval\|set_fall_threshold\|set_fall_cooldown\|ota_update,"val":<num>}` |

> Firmware/BE/FE/`fake_device.py` đều dùng `alert/fall`. Firmware tự động publish cảnh báo pin yếu (`LOW_BATTERY`) & lỗi phần cứng (`HARDWARE_ERROR`) qua `event`. Chi tiết payload: `architecture/protocol.md`.

---

## 3. BACKEND (FastAPI) — chi tiết tại `architecture/backend.md`
- **Endpoints**: `auth/login`, CRUD `wearers`/`devices`, `devices/{id}/assign|unassign`, `devices/{id}/command` (B5: start/stop_stream), `dashboard/telemetry`, `history/alerts(+resolve)`, `history/steps`, `history/{id}/timeline`, `history/{id}/telemetry`, `data-collection/sessions`. PUT `devices/{id}` đổi `telemetry_interval`/`fall_threshold`/`fall_cooldown` → publish command.
- **PostgreSQL**: organizations, users, wearers, devices (+telemetry_interval, +fall_threshold, +fall_cooldown, +fall_confirm_window, +rssi_interval), alerts, device_events (9 migrations).
- **InfluxDB**: `telemetry` (battery_pct, steps, ai_conf, distance_m).
- **MQTT bridge**: `mqtt_service.py` sub `eldercare/+/{status,alert/fall,event}`. Distance = `walk_steps×0.415×h + run_steps×0.5×h`.

## 4. FRONTEND (Next.js) — chi tiết tại `architecture/frontend.md`
- MQTT WS singleton `lib/mqtt-client.ts`; sub `eldercare/+/{alert/fall,status}` (status = realtime telemetry, map `battery`→`battery_pct`); Zustand stores (alert/telemetry); IMU parser; FallDetectionOverlay.
- Resolve alert: `api.acknowledgeAlert(id, deviceId)` truyền `?device_id=` để hybrid fallback (protocol §4) scope đúng thiết bị.

## 5. TINYML TRAIN (SisFall fall-detection / HAR) — chi tiết tại `architecture/tinyml_model.md`
> Repo train **`SisFall-PreProcessing/`** (git repo riêng `sis_fall_har_and_fall-detection_trainning`, ngoài monorepo). `path:line` dưới đây gốc `SisFall-PreProcessing/`.
- **Bài toán**: 5 nhãn `['Walk','Run','Idle','Trans','Fall']` (Fall idx 4, `ml_pipeline.py:158`); window **200×6 @100Hz** (`step2_windowing.py:11`); KPI = **Fall recall** @ `fall_threshold=0.25` (`ml_pipeline.py:156`); split subject-independent `SA/SE` (`ml_pipeline.py:18-20`).
- **Pipeline**: `DataPreprocessor`/`OutputReporter` (`ml_pipeline.py:10/130`); scaling accel`clip/8`+gyro`/2000` (`:108-115`); cache `.npy` dùng chung theo windowing.
- **Export**: `export_tflite_with_ops.py:76` → INT8 + `model_data_<ver>.cc/.h` nhúng ops; quét ops chuẩn bằng gói `tflite` (`:112-124`) tránh ESP32 crash boot.
- **Kiến trúc**: bám ESP-NN accel (Conv1×1/relu6/depthwise/MaxPool/GAP), **tránh** LSTM/dilated-conv/sigmoid/SE. Hiện tại **v30/v31**; v1–v29 ở `archive_trainings/`. Rule đầy đủ: `SisFall-PreProcessing/AGENTS.md`.

## 6. BÁO CÁO LUẬN VĂN (REPORT — LaTeX) — chi tiết tại `architecture/report.md`
- Thư mục thật `REPORT/Do_an_tot_nghiep_Vu_Manh_Hung/`; file chính `20225198_VuManhHung.tex`; ảnh `Hinhve/`; viết tắt `Tu_viet_tat.tex`. Chương 1–6 ở `Chuong/<n>_*.tex`.
- Quy chuẩn dịch: `pdflatex -interaction=nonstopmode -halt-on-error 20225198_VuManhHung.tex`. Template `SOICT_..._Template/` chỉ là reference structure.
- Glossary: `\newglossaryentry` trong `Tu_viet_tat.tex` + `\glsaddall`+`\printnoidxglossaries`. Hình còn thiếu: `plans/report_missing_figures_plan.md`. Đồng bộ Overleaf bằng `ols` (đẩy đủ file, kể cả `20225198_VuManhHung.tex` khi sửa preamble).
- Multi-agent: mục TinyML/AI có thể do agent khác viết → tránh sửa song song `4_Ket_qua_thuc_nghiem.tex`.

## 7. LUỒNG / SƠ ĐỒ
- Sơ đồ tích hợp (4 loại): `architecture/system_integration.md`.
- Quyết định thiết kế & lý do: `architecture/DECISIONS.md`.
- Debug web fullstack (fix pack 2026-06-17): `architecture/debug_web_fullstack.md` + `../web_fullstack_fixes_2026-06-17.md`.
- Báo cáo phiên web (2026-06-18, đầy đủ chỉnh sửa + test live): `../session_report_2026-06-18.md`.
- Plan firmware `set_fall_threshold`: `../firmware_set_fall_threshold_plan.md`.

---
*File này nên được tái sinh bằng `tools/gen_project_map.py` sau thay đổi lớn (mục Firmware), rồi rà lại thủ công.*
