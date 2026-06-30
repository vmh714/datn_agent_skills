# Plan: Per-org broker + auto-provision (MAC→device_id ngữ nghĩa) + firmware_version auto-report

## Context (vì sao làm)

`device_id` là khóa trong mọi MQTT topic `eldercare/{id}/...`. Backend hiện khớp tuyệt đối
`Device.device_id == {id từ topic}` (`backend/app/services/mqtt_service.py`) và **không auto-provision**:
device chưa đăng ký tay đúng id ⇒ mọi status/alert/command bị bỏ qua.

Bốn vấn đề / yêu cầu:
1. **device_id hardcode.** Firmware dùng `CONFIG_DEVICE_ID "esp32_eldercare_01"` (`hardware_config.h:21`)
   → nhiều board cùng id, đụng topic. Form lại ghi sai "Device ID (MAC Address)" (`DeviceFormDialog.tsx:86`).
2. **`firmware_version` nhập tay & lệch.** OTA ĐÃ CÓ (`endpoints/firmware.py`: list/upload/trigger; model
   `FirmwareRelease`; có `firmware_v0.0.1/0.0.2`). Nhưng firmware **không tự báo** version đang chạy
   (`schemas/mqtt.py` không có field) ⇒ sau OTA cột `Device.firmware_version` lệch. Cần auto-report.
3. **Broker hardcode.** `CONFIG_MQTT_BROKER_URI "mqtts://mqtt.toolhub.app:8883"` (`hardware_config.h:18`)
   cố định lúc compile ⇒ không tách broker theo org.
4. **Muốn device_id NGỮ NGHĨA.** MAC chỉ là vân tay phần cứng; id vận hành phải đẹp & tuần tự kiểu
   `esp32_eldercare_01` (giống device hiện tại), do hệ thống tự sinh.

**Quyết định kiến trúc (đã chốt với user):**
- **Multi-tenancy = per-org broker.** Mỗi org deploy 1 full-stack (broker + backend + DB). Org của
  auto-provision = org của chính deployment (không đoán).
- **MAC = vân tay phần cứng (eFuse), KHÔNG phải device_id.** Firmware lấy MAC làm **khóa topic MQTT**
  (`eldercare/<mac>/...`). MAC sống sót qua erase-flash + OTA, không cần provision.
- **device_id = tên ngữ nghĩa do backend sinh** (`esp32_eldercare_NN`, tuần tự trong org) khi auto-provision.
  Thêm cột `mac` (unique) để khớp MQTT đến với bản ghi. **device_id (PK, semantic) ≠ topic key (MAC).**
- **Auto-provision**: backend nhận MQTT theo MAC lạ → sinh device_id ngữ nghĩa + lưu mac; admin chỉ gán wearer.
- **`firmware_version` auto-report**: firmware gửi `fw_version` trong config/status; backend tự cập nhật.
  Bỏ ô nhập tay ở form, vẫn hiển thị 'Fw:' read-only.
- **Broker URI**: `#define CONFIG_MQTT_BROKER_URI` = broker org (default) → NVS reset vẫn đúng broker;
  NVS override (`config/mqtt_uri`) chỉ cần khi 1 build dùng chung nhiều org.

**Kết quả mong muốn:** Flash firmware (broker org là default) → cắm máy → device dùng MAC làm topic key,
nối broker org → backend sinh `esp32_eldercare_01` + lưu mac → tự hiện ở /devices (chưa gán) → admin gán
wearer. Không gõ id, không nhập version, không provision bắt buộc, không build lại per-board.

---

## Luồng init thiết bị mới (onboarding) + trách nhiệm từng service

> Không có service "định tuyến device → broker". Ràng buộc device↔org là **tĩnh** (broker org nằm trong
> #define firmware). Không registrar/discovery động. device_id ngữ nghĩa do backend sinh, không cần
> firmware handshake (firmware chỉ biết MAC của nó).

1. **(Một lần) Build & flash** firmware cho board với `#define CONFIG_MQTT_BROKER_URI` = broker org.
   `idf.py flash` không đụng NVS; MAC ở eFuse → không provision gì cho single-org.
2. **Boot**: `app_main` đọc MAC → topic key `<mac>`; `svc_cloud` (firmware) nối broker org. → service
   **phía firmware** lo "nối đúng broker" + định danh phần cứng.
3. **MQTT connected** (kể cả reconnect/sau OTA): `svc_cloud` publish `eldercare/<mac>/config/status` kèm
   `fw_version`.
4. **Backend `mqtt_service.MQTTService`** (1 instance/org, nối broker org) — service **phía backend** đón
   device mới: nhận config/status từ `<mac>` lạ → `_get_or_create_device_by_mac` → **sinh device_id
   `esp32_eldercare_NN`** (số kế tiếp trong org) + lưu `mac`, `fw_version`. Đây là toàn bộ "handle new device".
5. **Frontend `/devices`**: hiện `esp32_eldercare_NN` (id ngữ nghĩa) + mac phụ; chưa gán người. Admin gán wearer.
6. **Lệnh/OTA**: backend publish tới `eldercare/<device.mac>/command` (tra mac từ bản ghi).

→ Service: **firmware `svc_cloud`** = nối broker org + định danh MAC; **backend `mqtt_service.MQTTService`**
(1/org) = đón & sinh device_id ngữ nghĩa + auto-provision. Không thêm service nào.

---

## A. Backend

### A1. `app/core/config.py`
```python
ORG_ID: Optional[str] = None        # org của deployment; None = org duy nhất trong DB
DEVICE_ID_PREFIX: str = "esp32_eldercare_"   # tiền tố id ngữ nghĩa (tùy chỉnh)
```
(`MQTT_HOST/PORT/USERNAME/PASSWORD` đã là env per-deployment → mỗi org broker riêng, không đổi.)

### A2. `app/models/domain.py` + Alembic — thêm cột `mac`
- `Device`: thêm `mac: Mapped[Optional[str]] = mapped_column(String(64), unique=True, index=True)`.
  `device_id` vẫn là PK (nay = id ngữ nghĩa do BE sinh). Alert/Event/VerificationSession giữ FK →
  `devices.device_id` (không đổi).
- **Migration mới** (`alembic/versions/`): add column `mac` unique+index. Với device cũ
  `esp32_eldercare_01`: set `mac` thủ công (hoặc để re-provision) — xem mục Migration note.

### A3. `app/schemas/mqtt.py`
- `ConfigStatusPayload`: thêm `fw_version: Optional[str] = None` (đi cùng config/status lúc connect/
  reconnect — metadata tĩnh, không spam status 5s).

### A4. `app/services/mqtt_service.py` — auto-provision theo MAC, sinh id ngữ nghĩa
- `topic.split('/')[1]` nay là **MAC** (đặt tên biến `mac`), không phải device_id.
- Helper `_resolve_org_id(db)`: `settings.ORG_ID` nếu set; else org duy nhất (`order_by(created_at).limit(1)`).
- Helper `_next_device_id(db, org_id)`: lấy các `device_id` trong org khớp `^{PREFIX}(\d+)$`, `max(NN)+1`,
  zero-pad 2 → `f"{PREFIX}{NN:02d}"`.
- Helper `_get_or_create_device_by_mac(db, mac) -> Device | None`:
  - `select(Device).where(Device.mac == mac)`; có → trả về.
  - không → resolve org (None → skip, log); `device_id = _next_device_id`; tạo
    `Device(device_id=..., mac=mac, org_id=org, is_active=True)`, `db.add` + `flush`. Log
    `Auto-provisioned <device_id> (mac=<mac>)`. Bọc `IntegrityError` → rollback + re-select theo mac.
- Sửa handler khớp theo **mac** (thay `Device.device_id == device_id`):
  - `process_config_status` (90-95): dùng `_get_or_create_device_by_mac` (điểm provision đẹp nhất, mang
    config + version); cập nhật `device.firmware_version` nếu `payload.fw_version` khác.
  - `process_status` (113-118): `_get_or_create_device_by_mac` (provision dự phòng). Influx tag có thể
    giữ `device_id`=mac hoặc đổi sang `device.device_id` — **thống nhất dùng `device.device_id`** cho nhất
    quán dashboard (cần rà query history/influx đang tag bằng gì).
  - `process_alert` (161) & `process_event` (183): `_get_or_create_device_by_mac`; FK lưu
    `device.device_id` (semantic). alert vẫn skip nếu chưa gán wearer.

### A5. `app/api/api_v1/endpoints/devices.py` + `firmware.py` — publish theo `device.mac`
- 3 chỗ publish hiện dùng `eldercare/{device_id}/...` phải đổi sang `eldercare/{device.mac}/...`:
  - `devices.py` `send_device_command` (~168) `.../command`; `update_device` (~112) `.../config/set`.
  - `firmware.py` `trigger_ota_update` (~167) `.../command`.
  - Tra `device` (đã select theo PK device_id) rồi dùng `device.mac`; nếu `mac` None (device pre-register
    chưa online) → trả lỗi rõ "device chưa online".

> **Influx/History rà soát**: history endpoints query InfluxDB theo tag `device_id`. Nếu đổi tag sang
> semantic id (A4) thì nhất quán; nếu giữ mac thì FE phải map. **Chọn: tag bằng semantic `device.device_id`**
> ở mọi điểm ghi Influx để FE/history không cần biết MAC.

---

## B. Firmware

### B0. `components/svc_cloud/svc_cloud.c` — báo fw_version trong config/status (connect + reconnect)
config/status đã publish trong `MQTT_EVENT_CONNECTED` (87-102) → thêm `fw_version` vào **cả 2 chỗ** dựng
`root_cfg` (connect sau 95; reply config-change sau 301):
`cJSON_AddStringToObject(root_cfg, "fw_version", esp_app_get_description()->version);` + `#include "esp_app_desc.h"`.
Version từ app descriptor (`project(... VERSION ...)`), nên trùng convention `FirmwareRelease.version`.

### B1. `main/app_main.c` — topic key = MAC (dòng 68-69)
```c
#include "esp_mac.h"
uint8_t mac[6]; esp_read_mac(mac, ESP_MAC_WIFI_STA);
char mac_id[16]; snprintf(mac_id, sizeof(mac_id), "%02x%02x%02x%02x%02x%02x",
    mac[0],mac[1],mac[2],mac[3],mac[4],mac[5]);
svc_cloud_init(CONFIG_MQTT_BROKER_URI, mac_id, CONFIG_MQTT_USERNAME, CONFIG_MQTT_PASSWORD);
```
MAC ở eFuse → khóa topic ổn định, không cần NVS. `CONFIG_DEVICE_ID` deprecated. `svc_cloud.c` không đổi
(nhận client_id qua tham số → `s_device_id` → mọi topic).

### B2. `components/svc_cloud/svc_cloud.c` — broker default + NVS override (tùy chọn)
- **Bắt buộc**: đặt `#define CONFIG_MQTT_BROKER_URI` = broker thật của org (default, đỡ NVS reset).
- **Tùy chọn (multi-org)**: trong `svc_cloud_init` sau `strncpy` tham số (612-619), mở NVS `config`
  READONLY, `nvs_get_str(h, "mqtt_uri"/"mqtt_user"/"mqtt_pass", ...)` override nếu có (mirror load
  `tel_int` ở 622-628).

### B3. Provisioning NVS — CHỈ khi override broker cho multi-org (không bắt buộc)
device_id (semantic) do backend sinh, MAC từ eFuse → **không provision gì phía device**. Broker chỉ
provision khi 1 build chia nhiều org: CSV → `nvs_partition_gen.py` → `esptool write_flash 0x9000 nvs.bin`
(offset `nvs` theo `partitions.csv`). Single-org bỏ qua.

---

## C. Frontend

### C1. `components/features/devices/DeviceFormDialog.tsx`
- **Bỏ ô nhập tay** `firmwareVersion` (state 27/29/38/46-47, input 98-107) khỏi form + payload.
- device_id giờ do BE sinh → **bỏ luôn ô nhập device_id ở `create`** (hoặc giữ `create` chỉ để
  pre-register theo MAC; đơn giản nhất: bỏ nút "Đăng ký thiết bị", dựa hoàn toàn vào auto-provision).
  `edit` chỉ còn toggle `is_active`.

### C2. `components/features/devices/DevicesTable.tsx`
- Cột chính hiển thị `device.id` (= device_id ngữ nghĩa `esp32_eldercare_NN`); thêm dòng phụ `MAC: <mac>`.
  **GIỮ** `Fw: {device.firmwareVersion}` (read-only, auto-report). Header `"Device ID (MAC)"` → `"Device ID"`.
- (tùy chọn) badge "Mới" khi `wearerId == null`.

### C3. Types
- `src/types` + `openapi.json`: `Device` thêm `mac?: string`. `firmwareVersion` chuyển read-only (không gửi).

---

## D. Cập nhật tài liệu (bắt buộc theo codebase_context rule)
- `architecture/DECISIONS.md` → mục mới: per-org broker; MAC=vân tay/topic-key (eFuse); device_id ngữ
  nghĩa do BE sinh + cột `mac`; auto-provision; broker #define org + NVS override; fw_version qua config/status.
- `architecture/backend.md` + `db_schema.md` → cột `mac`; MQTT bridge khớp theo mac, sinh id; publish theo
  device.mac; org resolution. Vẽ lại ERD nếu cần.
- `architecture/frontend.md` → form bỏ nhập device_id/firmware; bảng hiện semantic id + mac.
- `architecture/firmware.md` + `PROJECT_MAP.md` → topic key = MAC; broker #define org + NVS; config/status
  thêm fw_version.
- `architecture/overview.md` MQTT Topics → topic dùng `<mac>`; config/status kèm fw_version.

---

## E. Verification (end-to-end)
1. **Migration**: chạy alembic upgrade → cột `mac` xuất hiện, unique+index; device cũ có mac (set tay/re-provision).
2. **Backend**: `backend/tests` (pytest) không vỡ. Thêm test: nhận config/status từ mac lạ → tạo Device
   `esp32_eldercare_01` + mac; mac thứ 2 → `esp32_eldercare_02`.
3. **Firmware**: flash (broker org = default). Boot → log topic key = MAC; nối đúng broker (không toolhub).
4. **Live**: Postgres (`net start postgresql-x64-17`) + backend trỏ broker org; firmware/`fake_device.py`
   publish `eldercare/<mac>/config/status`. Log `Auto-provisioned esp32_eldercare_NN (mac=...)`.
5. **Frontend**: `/devices` hiện `esp32_eldercare_NN` + MAC, chưa gán; gán wearer; telemetry/alert chạy.
   Trigger OTA → backend publish tới `eldercare/<mac>/command`; sau reboot, fw_version cập nhật tự động.
6. **Lệnh**: start/stop_stream từ FE tới đúng device (publish theo mac). History/telemetry hiển thị theo
   semantic id (Influx tag = device.device_id).

## Migration note (device hiện tại `esp32_eldercare_01`) — ĐÃ IMPLEMENT auto-adopt
Device cũ publish topic bằng `esp32_eldercare_01` (id hardcode); InfluxDB tag + Postgres FK đều theo id này.
Sau đổi, firmware publish bằng MAC. Để **giữ liền mạch lịch sử** (không phải rewrite InfluxDB):
- **Auto-adopt (mặc định bật)**: `settings.ADOPT_SINGLE_LEGACY_DEVICE=True`. Khi reflash + reconnect,
  `_get_or_create_device_by_mac` thấy org có ĐÚNG MỘT device chưa gắn mac → gắn mac vào chính bản ghi cũ
  `esp32_eldercare_01` (giữ device_id) thay vì tạo `_02`. → InfluxDB vẫn tag `esp32_eldercare_01` (vì
  `process_status` tag bằng `device.device_id`), Postgres alerts/events vẫn trỏ đúng. **Không cần đụng InfluxDB.**
- Sau khi migrate xong nên đặt `ADOPT_SINGLE_LEGACY_DEVICE=False` (tránh nhận nhầm khi thêm device thật mới).
- **Thủ công thay thế** (nếu tắt auto-adopt hoặc có >1 legacy): đọc MAC từ log boot firmware
  (`Device topic key (MAC): ...`) rồi `UPDATE devices SET mac='<mac>' WHERE device_id='esp32_eldercare_01';`
  trước khi device reconnect.
- **Nếu đã lỡ split** (đã tạo `_02`): InfluxDB không sửa tag tại chỗ được → cần script copy point sang tag
  mới rồi xoá cũ; hoặc gộp Postgres. Tránh bằng cách bật auto-adopt / backfill mac TRƯỚC khi reconnect.

## F. Out-of-scope (ghi chú để làm sau, KHÔNG làm lần này)
- Bootstrap registrar (firmware học id ngữ nghĩa qua handshake, dùng id đó trong topic) — đã chọn model
  MAC-topic + BE sinh id nên không cần.
- Multi-broker trong 1 backend (mô hình B) — đã chọn per-org full-stack.

### Ghi chú bảo mật — MAC spoofing & device auth (chốt: chỉ ghi chú, ghi vào DECISIONS.md)
- **Bản chất**: id trong topic (MAC / semantic / UUID) chỉ là *claim*, KHÔNG phải auth. Định dạng id
  không quyết định an toàn — broker auth/ACL mới quyết định. Dùng MAC không kém an toàn hơn id ngữ nghĩa
  (semantic tuần tự còn dễ đoán hơn; thiếu ACL thì kiểu id nào cũng spoof được).
- **Rủi ro hiện tại**: firmware dùng 1 cặp MQTT username/password **dùng chung** nhúng trong firmware →
  ai có creds đó publish được vào bất kỳ `eldercare/<mac>/...` (giả telemetry/alert, spam auto-provision rác).
- **Đỡ sẵn**: per-org broker giới hạn blast radius trong 1 org (cần creds đúng broker org).
- **Mitigation tương lai (khi production)**: (1) credential per-device + broker ACL `eldercare/<id>/#`;
  (2) mTLS client cert (mỗi device 1 cert, broker map CN→topic). Cả hai **tái xuất hiện bước provision**
  (nạp cred/cert vào NVS/flash) → cân bằng bảo mật ↔ tiện onboarding.
- **Quyết định lần này**: KHÔNG thêm vào scope. Giữ MAC-in-topic + per-org broker; ghi rủi ro + mitigation
  vào `DECISIONS.md` để hardening sau (gợi ý kèm: cổng claim `is_active=False` cho auto-provision là bước
  rẻ nhất khi muốn siết).
