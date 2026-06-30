# Plan — RSSI 4G: chu kỳ đo cấu hình được (0=tắt) + guard chống rớt link lúc confirm/alert

> Phạm vi: Firmware + Backend + Frontend. CMUX **loại** (đã thử không chạy). Lưu theo CLAUDE.md tại `datn_agent_skills/plans/`.

## Context

Đo RSSI 4G hiện làm bằng cách **thoát PPP → `AT+CSQ` → `ATO` nối lại** trong `cellular_rssi_update_task`
([svc_network.c:50](firmware/components/svc_network/svc_network.c#L50)). Mỗi lần đo **đứt MQTT TCP socket 15-20s**
(comment [svc_network.c:55-56](firmware/components/svc_network/svc_network.c#L55-L56)), chạy mỗi 120s và **chỉ trong
`STATE_NORMAL`** ([:61](firmware/components/svc_network/svc_network.c#L61)) — tức ~12-17% thời gian đường cảnh báo
chết, ngay trong chế độ giám sát ngã. `ATO` fail → `esp_restart()` ([:102](firmware/components/svc_network/svc_network.c#L102)).

Hệ quả nguy hiểm: một cú ngã rơi đúng cửa sổ 15-20s chết → alert bị trễ nguyên chu kỳ reconnect (vẫn được cache QoS1/NVS, nhưng trễ).

Hai việc cần làm:
- **Cách 1** — đưa chu kỳ đo thành config từ xa, **`0 = tắt hẳn`** (giá trị chính: tắt được hành vi rớt-link khi deploy thật, chỉ bật lúc demo).
- **Cách 2** — guard: **không đo RSSI (không `+++`) khi đang xác nhận ngã hoặc vừa báo ngã** (cửa sổ comms-critical).

> Governance: code hiện đi ngược **D-015** (vốn hoãn 4G-RSSI để tránh đứt link). Plan này hợp thức hóa hack + thêm van an toàn → thêm **D-022** vào DECISIONS.

---

## CÁCH 1 — `rssi_interval` (giây, 0=off) xuyên tầng

Tham số mới `rssi_interval`: default **300** (giảm so với 120 hiện tại; mỗi lần đo quá đắt), range hợp lệ `0 (off) | 60 | 120 | 300 | 600`. Firmware clamp giá trị non-zero `< 60` lên 60.

### Firmware
- **svc_network** ([svc_network.c](firmware/components/svc_network/svc_network.c)):
  - Thêm `static volatile uint32_t s_rssi_interval_ms = 300000;`. Bỏ hardcode `vTaskDelay(120000)` ([:57](firmware/components/svc_network/svc_network.c#L57)).
  - Vòng task: nếu `s_rssi_interval_ms == 0` → `vTaskDelay(60s)` rồi `continue` (ngủ, không đo); ngược lại `vTaskDelay(s_rssi_interval_ms)` rồi đo.
  - API mới (header `svc_network.h`): `void svc_network_set_rssi_interval_ms(uint32_t ms);` + `uint32_t svc_network_get_rssi_interval_ms(void);` (clamp: 0 hoặc ≥60000).
- **svc_cloud** ([svc_cloud.c](firmware/components/svc_cloud/svc_cloud.c)) — mirror y `fall_confirm_window`:
  - Parse `rssi_interval` trong handler `config/set` (gần [:286](firmware/components/svc_cloud/svc_cloud.c#L286)) → `svc_network_set_rssi_interval_ms(val*1000)` + `cfg_changed=true`.
  - NVS: lưu key `rssi_int` (gần [:302](firmware/components/svc_cloud/svc_cloud.c#L302)); load lúc init (gần [:674](firmware/components/svc_cloud/svc_cloud.c#L674)) → gọi setter.
  - Echo `rssi_interval` trong payload `config/status` (cả 2 chỗ [:97](firmware/components/svc_cloud/svc_cloud.c#L97) và [:317](firmware/components/svc_cloud/svc_cloud.c#L317)).

### Backend (mirror migration `add_fall_confirm_window`)
- Migration mới `add_rssi_interval_to_devices`: cột `devices.rssi_interval` Integer, `server_default='300'`, NOT NULL. `down_revision` = head hiện tại `d1e2f3a4b5c6`.
- [models/domain.py](backend/app/models/domain.py): `rssi_interval` (default 300).
- [schemas/domain.py](backend/app/schemas/domain.py): `DeviceBase`/`DeviceUpdate`/`DeviceResponse` thêm `rssi_interval: int = Field(300, ge=0, le=3600)` (0=off; ràng buộc dropdown phía FE).
- [schemas/mqtt.py](backend/app/schemas/mqtt.py): `ConfigStatusPayload.rssi_interval: Optional[int]`.
- [endpoints/devices.py](backend/app/api/api_v1/endpoints/devices.py): thêm `"rssi_interval"` vào `config_keys` ([:103](backend/app/api/api_v1/endpoints/devices.py#L103)) + payload `config/set` ([:108-112](backend/app/api/api_v1/endpoints/devices.py#L108-L112)).
- [services/mqtt_service.py](backend/app/services/mqtt_service.py): sync ngược DB từ echo (mirror [:176](backend/app/services/mqtt_service.py#L176)).

### Frontend (mirror `fall_confirm_window`)
- [types/index.d.ts](frontend/src/types/index.d.ts): `Device.rssi_interval?: number`.
- [services/api.ts](frontend/services/api.ts): `BackendDevice` + `mapDevice` + payload type `updateDevice`.
- [hooks/useDeviceData.ts](frontend/hooks/useDeviceData.ts): payload type `useUpdateDevice`.
- [DeviceConfig.tsx](frontend/components/features/device-detail/DeviceConfig.tsx): Card mới "Chu kỳ đo sóng 4G (RSSI)" — Select gồm **`Tắt (0)` | 60s | 120s | 300s | 600s** + `handleSaveRssiInterval`. Mô tả rõ: "Mỗi lần đo 4G làm gián đoạn kết nối ~15-20s; chọn Tắt khi không cần."

---

## CÁCH 2 — Guard comms-critical (firmware-only, qua sys_manager)

Tránh `+++` khi đang trong cửa sổ quan trọng. Cờ đặt ở **`sys_manager`** để né circular-dep (svc_cloud→svc_network đã có; svc_network KHÔNG được include svc_cloud/svc_ai). svc_network đã gọi `sys_manager_get_state()` nên 0 thêm phụ thuộc.

Dùng **mốc hết hạn đơn điệu** (monotonic expiry) để 2 writer không tranh nhau xoá cờ:
- **sys_manager** ([sys_manager.h](firmware/components/sys_manager/include/sys_manager.h) / `.c`):
  - `static volatile int64_t s_comms_critical_until_us = 0;`
  - `void sys_manager_bump_comms_critical(uint32_t ms);` → `s_comms_critical_until_us = MAX(cũ, esp_timer_get_time()+ms*1000)`.
  - `bool sys_manager_is_comms_critical(void);` → `esp_timer_get_time() < s_comms_critical_until_us`.
- **svc_ai** ([svc_ai.c](firmware/components/svc_ai/svc_ai.c)): khi vào `FALL_FSM_CONFIRMING` ([:163](firmware/components/svc_ai/svc_ai.c#L163)) → `sys_manager_bump_comms_critical(s_confirm_window_ms + 5000)` (phủ trọn cửa sổ xác nhận + biên để alert kịp publish).
- **svc_cloud** ([svc_cloud.c](firmware/components/svc_cloud/svc_cloud.c)): ngay sau khi publish `alert/fall` → `sys_manager_bump_comms_critical((uint32_t)(s_fall_cooldown_us/1000))` (giữ link suốt cooldown để alert QoS1 chắc chắn đi + tránh trễ alert lặp).
- **svc_network** ([svc_network.c:61](firmware/components/svc_network/svc_network.c#L61)): trước khi `+++`, thêm điều kiện skip:
  ```c
  if (sys_manager_get_state() != STATE_NORMAL || sys_manager_is_comms_critical()) {
      ESP_LOGD(TAG, "Skip RSSI: state hoặc đang trong cửa sổ confirm/alert");
      continue;
  }
  ```

> Cách 2 hoạt động độc lập với Cách 1 (kể cả khi `rssi_interval` bật, lần đo vẫn bị hoãn nếu đang confirm/alert). Cách 2 là van an toàn cốt lõi → nên giữ ngay cả khi sau này bỏ knob.

---

## Tái dùng
- Pipeline NVS + `config/set` + `config/status` + cột DB + echo sync: copy nguyên khuôn `fall_confirm_window` vừa làm.
- `svc_network_get_rssi()` ([svc_cloud.c:467](firmware/components/svc_cloud/svc_cloud.c#L467)) giữ nguyên.
- `esp_timer_get_time()` cho expiry.

## Đánh đổi
- `rssi_interval=0`: không còn RSSI 4G (FE hiển thị "—"/giá trị cũ). WiFi không bị ảnh hưởng (đọc RSSI tức thời, không qua task này).
- Guard có thể làm RSSI 4G cập nhật thưa hơn khi hay xảy ra confirm/alert — chấp nhận được (an toàn > độ tươi của chỉ số chẩn đoán).

## Docs sau khi code
- **DECISIONS D-022**: chấp nhận hack drop-link cho 4G-RSSI + knob `rssi_interval` (0=off) + guard comms-critical; CMUX loại (đã thử fail). Cập nhật ghi chú D-015.
- `firmware.md` (svc_network rssi task cấu hình + guard, sys_manager cờ comms-critical), `backend.md` + `db_schema.md` (cột + erd.png), `frontend.md` (DeviceConfig), `overview.md` (field MQTT `rssi_interval`), `PROJECT_MAP.md` (§1.2 API mới, §1.5 hằng số + command, §2 MQTT).

## Verification (E2E)
1. **FW build**: `idf.py build`.
2. **Guard (cách 2)** — `idf.py monitor`, đeo thiết bị 4G: tạo ngã → trong lúc log `CONFIRMING` và suốt `fall_cooldown`, **không** xuất hiện log "Tạm ngắt PPP (+++)"; MQTT không đứt; alert đi đúng giờ. Sau khi hết cooldown, lần đo RSSI tiếp theo mới chạy.
3. **Config (cách 1)**: FE đổi "Chu kỳ đo sóng" = Tắt → BE `config/set` → FW log set interval=0 + NVS persist (reboot vẫn tắt) → task không còn `+++`. Đổi = 600s → đo mỗi 600s. Echo `config/status` → BE sync `devices.rssi_interval` → FE hiển thị đúng.
4. **BE**: `alembic upgrade head` (Supabase: chạy thẳng, không cần start Postgres local). **FE**: `npx tsc --noEmit` sạch + `npm run dev`.

## Thứ tự: sys_manager (cờ) → svc_ai/svc_cloud bump → svc_network (interval + guard) → FW build → BE → FE → E2E → docs.
