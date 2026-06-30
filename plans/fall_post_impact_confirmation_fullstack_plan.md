# Plan tổng (full-stack) — AI chống báo động giả: Post-Impact Confirmation + đồng bộ config xuyên tầng

> Phạm vi: **Firmware + Backend + Frontend + Broker**. Lưu theo CLAUDE.md tại `datn_agent_skills/plans/`.

## Context

`svc_ai` hiện báo ngã **tức thì** chỉ từ 1 window (`prob[Fall] ≥ fall_threshold` → post thẳng
`AI_EVT_FALL_DETECTED`, [svc_ai.c:147-154](firmware/components/svc_ai/svc_ai.c#L147-L154)). Cooldown 15s ở
`svc_cloud` chỉ chống *spam*, không chống *sai*. → dương tính giả lẻ (ngồi phịch, nhảy, va chạm) vẫn bắn alert.

Mục tiêu: **giảm báo động giả mà KHÔNG mất recall** (KPI #1 = Fall recall). Giải pháp đã chốt với user:
giữ ML làm **trigger nhạy** → **không báo ngay** mà xác nhận **pha post-impact** (nằm im + tư thế lying)
trong **N giây** rồi mới alert. Khớp **D-013** (High-G/orientation là *precision filter*, không pre-gate) và
đúng tên "Post-Impact Fall Detection".

Vì N (cửa sổ xác nhận) cần tinh chỉnh theo bệnh nhân khi test thật → **cấu hình từ xa**, đồng bộ xuyên
**FW ↔ Broker ↔ BE ↔ FE** theo đúng khuôn `fall_threshold` (D-012) / `fall_cooldown` (D-014) đã có sẵn.

Quyết định user đã chốt: **Post-impact confirmation** (không 4-hard-gate AND, không majority-vote cứng trên ML);
**N cấu hình NVS/MQTT, mặc định ~4s**.

---

## Tham số mới xuyên tầng: `fall_confirm_window` (giây)

| Tầng | Thể hiện | Default / range |
|---|---|---|
| Firmware NVS | key `config/fall_cf` (ms nội bộ) | 4000 ms |
| MQTT `config/set` (BE→FW) | field `fall_confirm_window` (giây) | — |
| MQTT `config/status` (FW→BE echo) | field `fall_confirm_window` | — |
| PostgreSQL | cột `devices.fall_confirm_window` (int, giây) | 4, range 1–15 |
| REST PUT `/devices/{id}` | field `fall_confirm_window` | — |
| FE form | "Cửa sổ xác nhận ngã (s)" | 1–15 |

> **KHÔNG tạo topic MQTT mới**: tái dùng `config/set` (payload gộp) + `config/status` (echo). Broker không đổi schema.

---

## 1. FIRMWARE

### 1a. `svc_imu` — impact/free-fall detector per-sample (bằng chứng hỗ trợ)
- File: [svc_imu.c](firmware/components/svc_imu/svc_imu.c) (extend vòng per-sample của pedometer — đã ăn accel **thô**, Kalman làm cùn đỉnh nên không dùng data lọc, theo D-010) + [imu_service.h](firmware/components/svc_imu/include/imu_service.h).
- `svm = sqrt(ax²+ay²+az²)` (g). State nhỏ: free-fall (`svm<FREEFALL_THR≈0.6g`) → impact (`svm>IMPACT_THR≈2.5g`) trong ≈0.5s; lưu `{ts_us, peak_g, had_freefall}`.
- Getter (phong cách `imu_service_get_latest_roll`):
  ```c
  typedef struct { int64_t ts_us; float peak_g; bool had_freefall; } imu_impact_info_t;
  void imu_service_get_last_impact(imu_impact_info_t *out);
  ```

### 1b. `svc_ai` — Fall Confirmation FSM (thay post tức thì)
- File: [svc_ai.c](firmware/components/svc_ai/svc_ai.c) + [svc_ai.h](firmware/components/svc_ai/include/svc_ai.h). FSM nội bộ `FALL_FSM_NORMAL` / `FALL_FSM_CONFIRMING` (KHÔNG đụng system FSM).
- Thay [svc_ai.c:147-154](firmware/components/svc_ai/svc_ai.c#L147-L154):
  - **NORMAL** + `predicted_class==FALL` → CONFIRMING: lưu `confirm_start_us`, `trigger_conf`; `imu_service_get_last_impact()` (impact trong ~1.5s → boost log/confidence); reset `hits=0,total=0`.
  - **CONFIRMING** (mỗi window ~0.5s): post-impact OK = `class==AI_CLASS_IDLE && roll∈lying` (đảo điều kiện stand/sit ở [svc_ai.c:139-141](firmware/components/svc_ai/svc_ai.c#L139-L141), tái dùng nguyên range). `total++`, OK→`hits++`; `TRANSITION`=trung tính. **ABORT** nếu `class∈{WALK,RUN} && roll upright`. Khi `elapsed ≥ confirm_window_ms`: `hits/total ≥ 0.6` → **CONFIRMED** → `esp_event_post(AI_EVENT, AI_EVT_FALL_DETECTED,...)` (contract downstream GIỮ NGUYÊN); ngược lại ABORT.
- Thêm `void svc_ai_set_confirm_window_ms(uint32_t ms);`; đọc NVS `config/fall_cf` lúc `svc_ai_init` (default 4000).
- Hằng số: `FALL_CONFIRM_WINDOW_MS_DEFAULT=4000`, `CONFIRM_MAJORITY_RATIO=0.6f`, `IMPACT_RECENT_US=1500000`, `FREEFALL_THR_G≈0.6`, `IMPACT_THR_G≈2.5`.

### 1c. `svc_cloud` — nhận/echo config (mirror `fall_threshold`)
- File: [svc_cloud.c](firmware/components/svc_cloud/svc_cloud.c). Handler `config/set` (gần [svc_cloud.c:259-264](firmware/components/svc_cloud/svc_cloud.c#L259-L264)): parse field `fall_confirm_window` (1–15s) → `svc_ai_set_confirm_window_ms(val*1000)` + lưu NVS `fall_cf`.
- Load NVS lúc init (gần [svc_cloud.c:643-648](firmware/components/svc_cloud/svc_cloud.c#L643-L648)).
- Thêm `fall_confirm_window` vào payload `config/status` (echo cùng `fall_threshold`/`fall_cooldown`).

## 2. BACKEND (mirror migration `87ece1774913_add_fall_cooldown`)
- **Migration** Alembic mới `add_fall_confirm_window_to_devices`: cột `devices.fall_confirm_window` (Integer, default 4, NOT NULL).
- [models/domain.py](backend/app/models/domain.py): `Device.fall_confirm_window`.
- [schemas/domain.py](backend/app/schemas/domain.py): thêm vào `DeviceUpdate` + `DeviceResponse` (validate 1–15).
- [schemas/mqtt.py](backend/app/schemas/mqtt.py): `ConfigStatus` thêm `fall_confirm_window: Optional[int]` (để echo sync).
- [endpoints/devices.py](backend/app/api/api_v1/endpoints/devices.py): thêm `"fall_confirm_window"` vào `config_keys` + vào payload `config/set` ([devices.py:103-112](backend/app/api/api_v1/endpoints/devices.py#L103-L112)).
- [services/mqtt_service.py](backend/app/services/mqtt_service.py): sync ngược DB từ `config/status` (mirror [mqtt_service.py:174-175](backend/app/services/mqtt_service.py#L174-L175)).
- Auto-provision: gán default 4.

## 3. FRONTEND (mirror `fall_cooldown` trong DeviceConfig)
- [types/index.d.ts](frontend/src/types/index.d.ts): `Device.fall_confirm_window?: number`.
- [services/api.ts](frontend/services/api.ts): thêm vào kiểu payload update.
- [hooks/useDeviceData.ts](frontend/hooks/useDeviceData.ts): include nếu có khai báo trường cho update.
- [DeviceConfig.tsx](frontend/components/features/device-detail/DeviceConfig.tsx): state `fallConfirmWindow` + load từ `device` + `handleSaveFallConfirmWindow` (mirror [DeviceConfig.tsx:50-55](frontend/components/features/device-detail/DeviceConfig.tsx#L50-L55)) + ô Select 1–15s (mirror block Cooldown ~[DeviceConfig.tsx:191-195](frontend/components/features/device-detail/DeviceConfig.tsx#L191-L195)).

## 4. BROKER
- **Không thay đổi.** Tái dùng topic `eldercare/{mac}/config/set` và `config/status` (chỉ thêm field trong payload JSON). ACL wildcard `eldercare/<id>/#` đã phủ → không sửa cấu hình/quyền broker. (Chỉ cần *xác nhận* ACL hiện tại cho phép, không có việc code.)

---

## Tái dùng (không viết mới)
- FW: `imu_service_get_latest_roll()`, accel thô pedometer (D-010), `esp_timer_get_time()`, đường NVS+`config/set`+`config/status` của `fall_threshold`/`fall_cooldown`, event `AI_EVT_FALL_DETECTED` + cooldown `svc_cloud` (D-006).
- BE/FE: nguyên khuôn `fall_cooldown` (migration, schema, config_keys, echo sync, form Select) — chỉ nhân bản thêm 1 trường.

## Đánh đổi (đã thống nhất)
- Alert trễ ~N giây (≈4s) sau ML trigger — bản chất post-impact, chấp nhận được.
- Recall của trigger giữ nguyên (ML single-window không đổi); confirmation chỉ lọc precision.
- Ngã rồi đứng dậy ngay trong N giây bị suppress (chủ ý).

## Cập nhật tài liệu sau khi code (codebase_context.md §2)
- `DECISIONS.md`: **D-021** (post-impact confirmation FSM + vì sao bỏ majority-vote cứng trên ML + N cấu hình); note D-013 phần precision-filter **đã hiện thực**.
- `firmware.md` (svc_ai FSM, svc_imu impact detector), `backend.md` (cột + config/status field), `frontend.md` (DeviceConfig), `overview.md`/`db_schema.md` (cột mới + field MQTT), `PROJECT_MAP.md` (§1.2/§1.4/§1.5 + API mới), `db_schema.md` + vẽ lại `erd.png`.

## Verification (end-to-end)
1. **FW build**: skill `esp-idf-build-manager` → `idf.py build`.
2. **BE migration**: `alembic upgrade head` (Postgres phải `net start postgresql-x64-17` trước — xem memory) + chạy backend; **FE**: `npm run build`/dev.
3. **FW on-device** (`idf.py flash monitor`):
   - Ngã thật/drop test có đệm → log `NORMAL→CONFIRMING→CONFIRMED` → publish `alert/fall` kèm confidence (~4s).
   - Ngồi phịch/nhảy rồi đứng → `CONFIRMING→ABORT`, KHÔNG alert.
4. **Đồng bộ config**: FE đổi "Cửa sổ xác nhận ngã" = 6s → PUT → BE publish `config/set` → FW log áp dụng + NVS persist (reboot vẫn giữ) → FW echo `config/status` → BE sync `devices.fall_confirm_window=6` → FE hiển thị 6.
5. Dashboard vẫn nhận alert/fall như cũ (contract không đổi).

## Thứ tự thực thi đề xuất
FW (1a→1b→1c, build) → BE (migration→model→schema→endpoint→mqtt_service) → FE (types→api→form) → đồng bộ end-to-end → cập nhật docs.
