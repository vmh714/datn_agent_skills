# Báo cáo thay đổi — Frontend & Backend

> Tổng hợp toàn bộ thay đổi (telemetry real-time qua MQTT → auth-gate `proxy.ts` → vá bảo mật backend → dựng test suite FE & BE → fix alert log nhân đôi).
> **Tất cả thay đổi hiện CHƯA commit.** FE và BE là **2 git repo riêng biệt**.

---

## 1. Tổng quan

| Repo | Mốc HEAD | File sửa | File/thư mục mới | Test |
|------|----------|---------:|------------------|-----:|
| Frontend (`fall-detection/fall-detection`) | `8b380c2` | 10 | `lib/jwt.ts`, `store/useTelemetryStore.ts`, `test/` (9 file), `vitest.config.mts`, `.npmrc` | **77 pass** |
| Backend (`HAR_and_Fall-detection-backend`) | `f789cd7` | 6 + `tests/conftest.py` | `tests/test_auth_api.py`, `test_security_org_scoping.py`, `test_security_byid_routes.py`, `test_crud_api.py` | **36 pass** |

Năm nhóm công việc:
1. **FE — Telemetry real-time:** đẩy battery/steps từ MQTT lên dashboard không cần chờ polling.
2. **FE — Auth gate `proxy.ts`:** siết xác thực route phía server (chặn cả token hết hạn), bỏ CORS wildcard.
3. **BE — Bảo mật:** scope mọi endpoint theo `org_id`, vá các lỗ hổng truy cập chéo tổ chức còn sót, thêm tag InfluxDB.
4. **Test:** dựng từ đầu bộ test cho FE (Vitest) và BE (pytest).
5. **FE — Fix alert log nhân đôi:** bảng cảnh báo hiển thị 2 dòng/cú ngã → cho bảng log chỉ lấy từ backend.

---

## 2. Lưu ý chung

- Toàn bộ thay đổi đang ở trạng thái **uncommitted** (working tree) trên cả hai repo.
- Hai repo độc lập → khi commit nên commit riêng từng repo.
- Backend dùng DB **Supabase remote (prod)**; mọi test được thiết kế để **KHÔNG đụng tới DB/Influx thật** (xem mục 7).

---

## 3. Frontend — Real-time telemetry qua MQTT

Mục tiêu: dữ liệu `battery_pct`, `walk_steps`, `run_steps` từ MQTT cập nhật thẳng lên UI, ưu tiên hơn API polling.

| File | Trạng thái | Thay đổi |
|------|-----------|----------|
| [lib/mqtt-client.ts](fall-detection/fall-detection/lib/mqtt-client.ts) | sửa (+115) | Xử lý topic `eldercare/+/telemetry`; thêm types `TelemetrySample`, `TelemetryCallback`; thêm `telemetryCallbacks` + `connectionCallbacks`; method `onConnectionChange()`; **ref-count** kết nối (chỉ teardown khi về 0) chống "zombie WebSocket" qua StrictMode/HMR; mock phát telemetry định kỳ. |
| [store/useTelemetryStore.ts](fall-detection/fall-detection/store/useTelemetryStore.ts) | **mới** | Zustand store: `telemetry: Record<deviceId, DeviceTelemetry>` + cờ `mqttConnected`; actions `updateTelemetry`, `getTelemetry`, `setMqttConnected`. |
| [hooks/useMqtt.ts](fall-detection/fall-detection/hooks/useMqtt.ts) | sửa | Truyền callback telemetry (tham số thứ 4 của `subscribe`) → `updateTelemetry`; gọi `setDeviceOnline` từ batch. |
| [components/shared/GlobalMqttInit.tsx](fall-detection/fall-detection/components/shared/GlobalMqttInit.tsx) | sửa | `onConnectionChange → setMqttConnected`; telemetry `*` → store; phát chuông khi `fall_detected` + sound bật; cleanup đối xứng khi unmount. |
| [components/features/dashboard/DeviceGrid.tsx](fall-detection/fall-detection/components/features/dashboard/DeviceGrid.tsx) | sửa | Trước render card: `rt = getTelemetry(d.id)` → nếu có thì override `batteryLevel` bằng giá trị real-time. **Ưu tiên MQTT > polling.** |
| [components/layout/TopNav.tsx](fall-detection/fall-detection/components/layout/TopNav.tsx) | sửa | Badge trạng thái: "MQTT: Live" (chấm xanh nhấp nháy) / "MQTT: Reconnecting..." theo `mqttConnected`. |

---

## 4. Frontend — Auth gate `proxy.ts` (đã harden)

> **Quan trọng:** Next 16 đã **đổi tên `middleware.ts` → `proxy.ts`** (file convention cũ deprecated — xem `node_modules/next/dist/docs/.../file-conventions/proxy.md`). Vì vậy "middleware" của dự án nằm ở [proxy.ts](fall-detection/fall-detection/proxy.ts), không phải file thiếu.

| File | Trạng thái | Thay đổi |
|------|-----------|----------|
| [lib/jwt.ts](fall-detection/fall-detection/lib/jwt.ts) | **mới** | `isJwtExpired(token, leeway?)`: decode payload đọc `exp` để chặn sớm token hết hạn. **KHÔNG verify chữ ký** ở edge (FE không giữ secret; backend mới là nguồn xác thực thật). Token không decode được → coi như không hợp lệ. |
| [proxy.ts](fall-detection/fall-detection/proxy.ts) | sửa (+19) | Xem before/after dưới. |

**Before:** chỉ kiểm tra cookie `auth_token` có tồn tại; set `Access-Control-Allow-Origin: '*'` lên mọi response trang.

**After:**
- Coi là đã đăng nhập khi **có token VÀ token chưa hết hạn** (`isJwtExpired`).
- Token thiếu/hết hạn/rác + không ở `/login` → redirect `/login` **và xoá cookie chết**.
- Token hợp lệ + đang ở `/login` → redirect `/`.
- **Bỏ `Access-Control-Allow-Origin: '*'`** (vô dụng cho response HTML/RSC, là smell bảo mật; CORS cho API là việc của backend). Giữ `ngrok-skip-browser-warning`.
- `matcher` giữ nguyên: loại trừ `api`, `_next/static`, `_next/image`, `favicon.ico`, `sitemap.xml`, `robots.txt`.

---

## 5. Frontend — Fix lỗi báo động hiển thị 2 dòng (alert log nhân đôi)

**Triệu chứng:** trên `/alerts` và dashboard, mỗi cú ngã hiện **2 dòng** cùng thời điểm nhưng message khác nhau:
- `Cảnh báo: Phát hiện té ngã mạnh tại...` — alert **live do FE tạo** từ payload MQTT (`lib/mqtt-client.ts`, `id = crypto.randomUUID()`).
- `Phát hiện té ngã (confidence: 96%)` — alert **từ DB** qua API (`services/api.ts` `mapAlert`, `id` server).

**Nguyên nhân:** `useCombinedAlerts` trộn 2 nguồn (API + `useAlertStore` live) rồi dedup theo `alert.id`. Cùng 1 sự kiện nhưng 2 `id` khác nhau → không gộp được → 2 dòng. **Backend KHÔNG nhân đôi** — DB chỉ 1 bản ghi/sự kiện.

| File | Trạng thái | Thay đổi |
|------|-----------|----------|
| [hooks/useDeviceData.ts](fall-detection/fall-detection/hooks/useDeviceData.ts) | sửa | `useCombinedAlerts` giờ **chỉ lấy alert từ backend API** (bỏ merge `useAlertStore`). Bảng log = nguồn sự thật duy nhất. Bỏ import `useAlertStore`/`Alert` không còn dùng. |
| [components/shared/GlobalMqttInit.tsx](fall-detection/fall-detection/components/shared/GlobalMqttInit.tsx) | sửa | Khi nhận fall alert live → `qc.invalidateQueries(['alerts'])` (trễ 1.5s) để bảng kéo bản ghi DB về ngay (~1–2s) thay vì chờ poll 30s. `addAlert` vẫn giữ (cho overlay + chuông). |

**Giữ nguyên:** `useAlertStore` (nay chỉ phục vụ UX real-time), `FallDetectionOverlay` (popup ngã tức thì), `GlobalAlertToaster`, chuông báo động.

**Lỗi liên quan (PRE-EXISTING, chưa xử):** overlay/table bấm "Xác nhận" gửi `id` client (uuid live) lên `/resolve`, không khớp `id` DB → backend rơi vào nhánh fallback "resolve alert chưa xử lý mới nhất". Đúng cho ca 1 ngã đơn lẻ, có thể sai nếu nhiều alert chưa xử lý cùng lúc.

---

## 6. Frontend — Hạ tầng test (Vitest)

Dựng mới: [vitest.config.mts](fall-detection/fall-detection/vitest.config.mts) (alias `@/*`), `test/setup.ts` (jest-dom + cleanup + polyfill localStorage cho zustand persist); thêm script `test` / `test:watch` vào `package.json`; `.npmrc` (giới hạn heap node).

| File test | Case | Phủ |
|-----------|-----:|-----|
| `test/useTelemetryStore.test.ts` | 7 | init, merge default, partial update, đa thiết bị |
| `test/mqtt-client.test.ts` | 19 | mock-mode (fake timers) + real-mode (mock module `mqtt`): parse telemetry/fall/imu, payload hỏng, ref-count, error/close, reconfigure |
| `test/useMqtt.test.tsx` | 6 | connect/subscribe/cleanup, telemetry→store, alert→store |
| `test/GlobalMqttInit.test.tsx` | 8 | render null, wire connection, telemetry, playAlarm (sound on/off/non-fall), cleanup (bọc `QueryClientProvider`) |
| `test/DeviceGrid.test.tsx` | 5 | loading/empty, render card, telemetry override pin |
| `test/TopNav.test.tsx` | 4 | Live/Reconnecting, click menu, reactivity |
| `test/jwt.test.ts` | 9 | exp tương lai/quá khứ, thiếu exp, không phải JWT, leeway |
| `test/proxy.test.ts` | 17 | matcher include/exclude + mọi nhánh redirect/pass-through + xoá cookie (Node env, dùng `unstable_doesMiddlewareMatch` + `getRedirectUrl`) |
| `test/useCombinedAlerts.test.tsx` | 2 | alert live trong store KHÔNG tạo dòng trùng trong bảng log; sort theo thời gian giảm dần |

**Chạy:** `cd fall-detection/fall-detection && npm test` → **9 file, 77 case pass.**

> Ghi chú: `npx tsc --noEmit` còn vài lỗi **tồn tại sẵn, ngoài thay đổi này**: `store/useTelemetryStore.ts` (TS2783 spread-overwrite, vô hại) và 3 component `AlertHistoryTable`/`CriticalAlertBanner`/`FallDetectionOverlay` (TS2554 — nhiều khả năng do API đổi ở Next 16). 4 file mới (jwt.ts, proxy.ts, các test) type-check sạch.

---

## 7. Backend — Bảo mật (org-scoping) & InfluxDB tags

### 7.1 Phần đã có từ trước (security fix + tags)

| File | Endpoint | Thay đổi |
|------|----------|----------|
| [dashboard.py](HAR_and_Fall-detection-backend/app/api/api_v1/endpoints/dashboard.py) | `GET /telemetry` | Thêm `get_current_user` + `WHERE Device.org_id == current_user.org_id` (trước trả **tất cả** device). |
| [history.py](HAR_and_Fall-detection-backend/app/api/api_v1/endpoints/history.py) | `GET /alerts` | Lọc `Alert.device_id.in_(org_device_ids)`. |
| history.py | `PATCH /alerts/{id}/resolve` | Verify alert thuộc org trước khi resolve. |
| history.py | `GET /{device_id}/timeline` | Verify device thuộc org → **404** nếu không. |
| history.py | `GET /steps` | Lấy device_id của org rồi nhét `contains(... set: [...])` vào Flux query (trước query **toàn bộ** telemetry). |
| [mqtt_service.py](HAR_and_Fall-detection-backend/app/services/mqtt_service.py) | `process_status` | Thêm tag `wearer_id` vào point `telemetry` khi device có người đeo. |
| [data_collection.py](HAR_and_Fall-detection-backend/app/api/api_v1/endpoints/data_collection.py) | `POST /sessions` | Sinh `session_id = uuid4()`, gắn tag `session_id` vào mỗi point `imu_raw` + trả về trong response. |

### 7.2 Vá bổ sung các lỗ hổng còn sót (phát hiện khi viết test)

Các route theo-ID/create ban đầu **thiếu `get_current_user` và/hoặc filter org** → có thể truy cập/sửa/xoá chéo tổ chức, hoặc tự gán org khác. Đã vá:

| File | Endpoint | Rủi ro trước | Cách vá |
|------|----------|--------------|---------|
| devices.py | `PUT /{id}`, `DELETE /{id}` | Không token cũng gọi được; sửa/xoá device org khác theo ID | Thêm auth + `Device.org_id == current_user.org_id`; không thấy → 404 |
| devices.py | `POST /{id}/assign` | Gán chéo org; còn gán được wearer của org khác | Auth + verify **cả device lẫn wearer** cùng org |
| devices.py | `POST /{id}/unassign` | Gỡ gán device org khác | Auth + filter org |
| devices.py | `POST /` (create) | Client tự truyền `org_id` → tạo device cho org khác | **Ép** `org_id = current_user.org_id`, bỏ override |
| wearers.py | `GET/PUT/DELETE /{id}` | Đọc/sửa/xoá hồ sơ người bệnh org khác | Auth + filter org → 404 |
| wearers.py | `POST /` (create) | Tự truyền `org_id` | Ép `org_id` theo user |
| data_collection.py | `POST /sessions` | **Không auth** → ai cũng ghi InfluxDB cho device bất kỳ | Thêm auth + **verify device thuộc org** (404 nếu không) |

---

## 8. Backend — Hạ tầng test (pytest)

Kiến trúc **cô lập, offline, an toàn** ([tests/conftest.py](HAR_and_Fall-detection-backend/tests/conftest.py)):
- **SQLite in-memory** (`create_async_engine("sqlite+aiosqlite://", poolclass=StaticPool)` → 1 connection dùng chung) **override `get_db`** → không đụng Supabase prod.
- **Mock toàn bộ InfluxDB** (`write_point` / `write_api.write` / `query_api.query`).
- Seed **2 org + 2 user** (alice/org A, bob/org B) + device mỗi org; ký **JWT thật** → test phân quyền theo org.
- **Override `get_current_user`** bằng bản ép `uuid.UUID(sub)` — vì cột `UUID` của SQLite không tự coerce string như Postgres (vẫn decode JWT thật → giữ nguyên 401 cho token thiếu/hỏng/hết hạn).
- `collect_ignore` 2 script thủ công cũ (`test_db_conn.py`, `test_devices_manual.py` — cần server/DB thật).

| File test | Case | Phủ |
|-----------|-----:|-----|
| `tests/test_auth_api.py` | 7 | login OK/sai pass/unknown; route bảo vệ: thiếu/sai/hết hạn token → 401; token hợp lệ → 200 |
| `tests/test_security_org_scoping.py` | 8 | dashboard/devices/wearers/alerts chỉ thấy org mình; timeline & resolve chéo-org → 404; steps: Flux query giới hạn đúng device của org |
| `tests/test_security_byid_routes.py` | 11 | cross-org → 404 (devices/wearers theo-ID), gán wearer chéo-org → 404, create bị ép `org_id`, data-collection chéo-org → 404 + no-token → 401 |
| `tests/test_crud_api.py` | 5 | wearers CRUD; devices create/dup/update/assign/unassign/delete; data-collection (session_id + ghi Influx) |
| `tests/test_mqtt_bridge.py` | 3 | (cũ) process_status/alert/event — nay chạy offline |
| `tests/test_timeline_api.py` | 2 | (cũ) dashboard + timeline — đã chạy với auth |

**Chạy:** `cd HAR_and_Fall-detection-backend && venv/Scripts/python.exe -m pytest tests/ -W ignore::DeprecationWarning` → **36 case pass.**

> Lưu ý: 2 test cũ (`test_mqtt_bridge`, `test_timeline_api`) trước đó **đã hỏng** do security fix (gọi API không token → 401); nay pass nhờ conftest mới mà **không cần sửa code test**.

---

## 9. Kết quả audit bảo mật

Quét tự động toàn bộ **18 route**:

| Nhóm | Route | Auth | Org-scope |
|------|-------|:----:|:---------:|
| auth | `POST /login` | — (public, đúng thiết kế) | — |
| dashboard | `GET /telemetry` | ✅ | ✅ |
| history | `GET /alerts`, `PATCH /alerts/{id}/resolve`, `GET /{id}/timeline`, `GET /steps` | ✅ | ✅ |
| devices | `GET /`, `POST /`, `PUT/DELETE /{id}`, `POST /{id}/assign`, `POST /{id}/unassign` | ✅ | ✅ |
| wearers | `GET /`, `POST /`, `GET/PUT/DELETE /{id}` | ✅ | ✅ |
| data_collection | `POST /sessions` | ✅ | ✅ |

→ **Không còn lỗ hổng phân quyền / truy cập chéo tổ chức.**

**Điểm nhỏ còn lại (mức thấp, chưa xử):** `create_device` kiểm tra trùng `device_id` ở phạm vi toàn cục (vì là primary key) → khi trùng trả `400 "already registered"`, về lý thuyết có thể để lộ việc một `device_id` đã tồn tại ở org khác (info-disclosure nhẹ, **không** lộ dữ liệu). Có thể đổi thành thông báo trung tính nếu cần.

---

## 10. Cách kiểm chứng

- **FE:** `cd fall-detection/fall-detection && npm test` → 77 pass.
- **BE:** `cd HAR_and_Fall-detection-backend && venv/Scripts/python.exe -m pytest tests/ -W ignore::DeprecationWarning` → 36 pass.
- **Alert nhân đôi (thủ công, có backend):** tạo 1 cú ngã → `/alerts` và dashboard chỉ còn **1 dòng**/sự kiện; overlay vẫn bật tức thì.
- **Proxy (thủ công):** `npm run dev`, đặt `document.cookie="auth_token=<JWT exp quá khứ>"` → vào `/` phải bị đá về `/login` và cookie bị xoá.

---

## 11. Phụ lục — diffstat

### Frontend (vs `8b380c2`)
```
components/features/dashboard/DeviceGrid.tsx |  26 +-
components/layout/TopNav.tsx                 |  20 +-
components/shared/GlobalMqttInit.tsx         |  17 +-   (+ invalidate alerts khi fall live)
hooks/useMqtt.ts                             |   6 +-
hooks/useDeviceData.ts                       |  ~25 +-   (useCombinedAlerts chỉ lấy API)
lib/mqtt-client.ts                           | 115 +-
next.config.ts                               |   5 +
package.json                                 |  10 +-
proxy.ts                                     |  19 +-
(mới) lib/jwt.ts, store/useTelemetryStore.ts, test/ (9 file), vitest.config.mts, .npmrc
       test/ gồm: useCombinedAlerts.test.tsx (mới nhất) + 8 file test khác
```

### Backend (vs `f789cd7`)
```
app/api/api_v1/endpoints/dashboard.py       |  12 +-
app/api/api_v1/endpoints/data_collection.py |  34 +-
app/api/api_v1/endpoints/devices.py         |  69 +-
app/api/api_v1/endpoints/history.py         |  73 +-
app/api/api_v1/endpoints/wearers.py         |  45 +-
app/services/mqtt_service.py                |   2 +
tests/conftest.py                           | 214 +-
(mới) tests/test_auth_api.py, test_security_org_scoping.py, test_security_byid_routes.py, test_crud_api.py
```
