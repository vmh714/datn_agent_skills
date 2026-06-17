# Debug Playbook — Web Fullstack Fix Pack (cho Antigravity)

> **Đối tượng:** agent Antigravity chạy ở **máy gốc** (code TRỰC TIẾP trong `backend/`, `frontend/`, `firmware/` — KHÔNG có thư mục con kiểu `backend/HAR_and_Fall-detection-backend/`).
> **Tiền đề:** các fix trong `project_setup/web_fullstack_fixes_2026-06-17.md` được viết **"mù"** (không build/chạy khi sửa). File này hướng dẫn **verify + debug** chúng. Đọc fix pack đó trước.
> **Công cụ Antigravity:** `view_file`/`list_dir` (đọc), `grep_search` (tìm). Path dưới đây tương đối gốc repo tương ứng.
> **Shell:** Windows + PowerShell — nối lệnh bằng `;` (KHÔNG `&&`).

---

## 0. Quy trình debug tổng (làm theo thứ tự — fail-fast)

1. **Bắt lỗi compile TRƯỚC khi chạy** (fix mù dễ sai cú pháp/kiểu):
   - Backend: `cd backend; python -c "import app.main"` → bắt lỗi import/Pydantic. Hoặc chạy `uvicorn app.main:app --reload` và đọc traceback.
   - Frontend: `cd frontend; npm run build` → bắt lỗi TypeScript. (`npm run lint` nếu có.)
2. **Khởi động hạ tầng:** backend (`uvicorn`), frontend (`npm run dev`), và `python datn-agent-skills/tools/fake_device.py`.
3. **Chạy 8 TC** trong fix pack (§3). Mỗi TC fail → tra bảng §3 dưới đây.
4. Sau khi xanh hết → nếu có sửa code, cập nhật `architecture/*` + `PROJECT_MAP.md` theo rule `codebase_context`.

> **Nguyên tắc:** khi code lệch doc → **code là chuẩn**, sửa doc cho khớp. Khi nghi ngờ một fix, mở đúng `file` ở §2/§3 và so với "Expected".

---

## 1. Bản đồ file đã đụng (máy gốc)

| Fix | File |
|---|---|
| B1 | `frontend/lib/mqtt-client.ts` |
| B2 | `backend/app/schemas/mqtt.py`, `backend/app/services/mqtt_service.py`, `backend/app/schemas/history.py`, `backend/app/api/api_v1/endpoints/history.py`, `frontend/services/api.ts` |
| B3 | `frontend/services/api.ts`, `frontend/components/features/dashboard/FallDetectionOverlay.tsx`, `frontend/components/features/dashboard/CriticalAlertBanner.tsx`, `frontend/components/features/alerts/AlertHistoryTable.tsx` |
| M1 | `backend/app/schemas/mqtt.py`, `datn-agent-skills/tools/fake_device.py` |
| M2 | `backend/app/services/mqtt_service.py`, `datn-agent-skills/tools/fake_device.py` |
| M4 | `backend/app/services/mqtt_service.py` |
| L2 | `frontend/components/features/dashboard/WeeklyActivityTrends.tsx` |
| L4 | `backend/app/api/api_v1/endpoints/devices.py`, `datn-agent-skills/tools/fake_device.py` |

> Nếu máy gốc đang ở commit CŨ (chưa có fix), agent phải **tự áp lại** các thay đổi theo "Expected state" §2 — fix pack viết trên máy clone, KHÔNG tự đồng bộ sang máy gốc qua git.

---

## 2. Trạng thái đúng (Expected) — dùng `grep_search` để xác minh nhanh

**B1 · `frontend/lib/mqtt-client.ts`**
- `grep_search "eldercare/+/status"` → PHẢI thấy ở chỗ `client.subscribe(...)`. KHÔNG còn `subscribe('eldercare/+/telemetry')`.
- Handler có `if (topic.endsWith('/status'))` và `battery_pct: data.battery_pct ?? data.battery ?? 0`.
- ⚠️ Bẫy: mock mode (`NEXT_PUBLIC_MOCK_MQTT=true`) bắn telemetry callback trực tiếp, KHÔNG qua topic → B1 chỉ kiểm được với broker thật (mock luôn "chạy" kể cả khi B1 sai).

**B2 · backend**
- `schemas/mqtt.py` `StatusPayload` có `walk_steps: int = 0` và `run_steps: int = 0`.
- `services/mqtt_service.py` `process_status`: `distance_m = (payload.walk_steps * 0.415 * height_m) + (payload.run_steps * 0.5 * height_m)`; Influx point có `.field("walk_steps", ...)` và `.field("run_steps", ...)`.
- `schemas/history.py` `StepHistoryResponse` có `walk_steps`/`run_steps`.
- `endpoints/history.py` Flux filter có `r["_field"] == "walk_steps" or r["_field"] == "run_steps"`; `StepHistoryResponse(... walk_steps=, run_steps=)`.
- `frontend/services/api.ts` `BackendStepsDay` có `walk_steps?`/`run_steps?`.

**B3 · frontend**
- `services/api.ts` `acknowledgeAlert: async (alertId: string, deviceId?: string)` và build `?device_id=${encodeURIComponent(deviceId)}`.
- `grep_search "api.acknowledgeAlert"` → 3 caller đều truyền tham số 2 (`activeAlert.deviceId` / `alert.deviceId`).

**M1 · `backend/app/schemas/mqtt.py`**
- `AlertPayload`: `confidence: float` (bắt buộc), `user_name: Optional[str] = None`, `message: Optional[str] = None`.
- `tools/fake_device.py` `send_fall_alert` gửi `{"user_name","message","confidence"}` (KHÔNG còn `alert_type`).

**M2 · backend + fake_device**
- `mqtt_service.py` có `if payload.rssi is not None: point = point.field("rssi", int(payload.rssi))`.
- `fake_device.py` `send_status` có `"rssi": random.randint(-95, -55)`.

**M4 · `mqtt_service.py`**
- `handle_message` except: `print(f"[MQTT][DROP] topic={topic} err={e} payload={payload_str}")`.

**L2 · `WeeklyActivityTrends.tsx`**
- Import `useStepsHistory` từ `@/hooks/useDeviceData`; KHÔNG còn mảng `WEEKLY_DATA` tĩnh; `<Bar dataKey="steps">`.

**L4 · `devices.py`**
- Publish command với `retain=False` (KHÔNG `retain=True`).
- `fake_device.py` `on_message` xử lý `action == "set_interval"`; heartbeat dùng `telemetry_interval`.

---

## 3. Bảng triệu chứng → nguyên nhân → chỗ sửa

| Triệu chứng khi test | Nguyên nhân khả dĩ | Kiểm / sửa ở |
|---|---|---|
| FE không cập nhật battery/steps realtime (broker thật) | B1 chưa áp, hoặc broker không đẩy `status` tới FE, hoặc FE đang MOCK | `mqtt-client.ts` subscribe `status`; tắt `NEXT_PUBLIC_MOCK_MQTT`; kiểm broker bằng `mosquitto_sub -t 'eldercare/+/status'` |
| FE realtime vẫn trống dù B1 đúng | Sai tên field: status gửi `battery` còn FE đọc `battery_pct` | `mqtt-client.ts` phải có `data.battery_pct ?? data.battery` |
| `distance_km` = 0 dù đang đi/chạy | wearer chưa gán / `height_cm` null; hoặc payload không có walk/run | gán wearer; `fake_device.send_status` phải gửi `walk_steps`/`run_steps`; `process_status` đọc đúng field |
| `distance` quá nhỏ với người chạy | Còn dùng `steps × 0.415` (B2 chưa áp) | `mqtt_service.process_status` công thức walk×0.415 + run×0.5 |
| `/history/steps` không có walk/run | Flux filter thiếu field, hoặc schema cũ | `endpoints/history.py` filter + `StepHistoryResponse` |
| Bấm "Xác nhận cứu hộ" resolve nhầm device khác | B3 chưa áp — thiếu `?device_id=` → fallback chọn alert mới nhất toàn org | `services/api.ts acknowledgeAlert` + 3 caller |
| Alert fake không vào DB, backend báo ValidationError | M1 chưa áp (user_name/message required) hoặc fake_device gửi `alert_type` | `schemas/mqtt.py AlertPayload`; `fake_device.send_fall_alert` |
| Backend "im lặng" khi payload lỗi | M4 chưa áp | tìm log `[MQTT][DROP]`; nếu không có → sửa `handle_message` |
| Vitals RSSI rỗng | Payload không có `rssi` (firmware thật chưa gửi — ĐÚNG), hoặc dùng fake_device mà M2 chưa áp | dùng fake_device (gửi rssi); `process_status` ghi rssi |
| "Hoạt động 7 ngày" vẫn ra số cố định | L2 chưa áp (còn `WEEKLY_DATA`) | `WeeklyActivityTrends.tsx` |
| Device reconnect tự đổi interval bất ngờ | L4 chưa áp (`retain=True`) | `devices.py` `retain=False` |
| `npm run build` lỗi type ở `acknowledgeAlert`/`BackendStepsDay` | caller chưa khớp chữ ký mới | so §2 B3/B2 |
| Backend không import được | sai cú pháp Pydantic ở `mqtt.py`/`history.py` | `python -c "import app.main"` đọc traceback |

---

## 4. Lệnh chạy nhanh (PowerShell, máy gốc)

```powershell
# Backend (smoke import trước)
cd backend; python -c "import app.main"; uvicorn app.main:app --reload

# Frontend (build bắt lỗi TS trước khi dev)
cd frontend; npm run build; npm run dev

# Thiết bị giả lập (không cần phần cứng)
python datn-agent-skills/tools/fake_device.py
# Phím: s=đứng w=đi r=chạy | f=gửi FALL | e=gửi EVENT | Ctrl+C=thoát

# Soi MQTT thô (nếu có mosquitto-clients)
mosquitto_sub -h <MQTT_HOST> -p <PORT> -t 'eldercare/+/status'
mosquitto_sub -h <MQTT_HOST> -p <PORT> -t 'eldercare/+/command'
```

> Bơm payload lỗi để test M4: `mosquitto_pub -t eldercare/dev_01/status -m '{"foo":1}'` → backend phải log `[MQTT][DROP]` và KHÔNG crash.

---

## 5. Lưu ý cho agent Antigravity

- **Đừng đoán cấu trúc** — `view_file` đúng file ở §1/§2 rồi mới kết luận. Dùng `grep_search` các chuỗi ở §2 để xác minh fix đã áp hay chưa.
- **M3 (bảo mật đa tenant MQTT) = quyết định D** (chấp nhận rủi ro phạm vi đồ án) — KHÔNG code, chỉ ghi vào mục Hạn chế/Future work của báo cáo. Chi tiết: fix pack §4 + `DECISIONS.md` D-007.
- **Còn nợ firmware** (không thuộc web): publish `event`, đọc/gửi `rssi` (AT+CSQ). Backend đã sẵn đường nhận.
- Sau khi verify/sửa: cập nhật `architecture/*` + `PROJECT_MAP.md` + (nếu có quyết định mới) `DECISIONS.md`, kèm dòng `> **Cập nhật lần cuối:**`.
