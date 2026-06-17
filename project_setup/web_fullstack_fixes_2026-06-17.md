# Web Fullstack ↔ Protocol — Fix Pack (2026-06-17)

> Phiên rà nhất quán end-to-end Firmware → MQTT → Backend (FastAPI) → REST → Frontend (Next.js) đối chiếu `architecture/protocol.md`.
> File này gói gọn **bug đã fix + file đã đụng + kịch bản test** để verify ở máy có env. M3 (bảo mật đa tenant MQTT) → chọn **D: chấp nhận rủi ro ở phạm vi đồ án** (xem cuối file).
>
> Layout: code thật ở `backend/HAR_and_Fall-detection-backend/`, `frontend/Fall-Detection-dashboard/`. Path bảng dưới tương đối gốc repo tương ứng.

---

## 1. Checklist bug đã fix

| # | Bug | File đã sửa | Bản chất fix |
|---|-----|-------------|--------------|
| **B1** | FE subscribe `eldercare/+/telemetry` nhưng cả hệ publish `status` (không ai republish) → telemetry realtime CHẾT với thiết bị thật | `frontend: lib/mqtt-client.ts` | Sub `eldercare/+/status`; handler parse `/status`, map `battery_pct ?? battery` |
| **B2** | `walk_steps`/`run_steps` bị drop ở `StatusPayload` → distance dùng `tổng steps × 0.415` (sai cho người chạy); steps history không tách walk/run | `backend: schemas/mqtt.py, services/mqtt_service.py, schemas/history.py, api/api_v1/endpoints/history.py` · `frontend: services/api.ts` | StatusPayload nhận walk/run; `distance = walk×0.415×h + run×0.5×h`; ghi Influx field `walk_steps`/`run_steps`; `StepHistoryResponse` + Flux trả thêm walk/run (giữ `steps` tổng); `BackendStepsDay` thêm field optional |
| **B3** | `acknowledgeAlert` không truyền `device_id` → hybrid fallback (§4) resolve nhầm alert thiết bị khác (overlay dùng UUID tạm) | `frontend: services/api.ts, FallDetectionOverlay.tsx, CriticalAlertBanner.tsx, AlertHistoryTable.tsx` | `acknowledgeAlert(id, deviceId?)` → `?device_id=`; 3 caller truyền `alert.deviceId` |
| **M1** | `AlertPayload` bắt buộc `user_name`/`message` (process_alert chỉ dùng `confidence`) → alert thiếu field bị nuốt | `backend: schemas/mqtt.py` · `tools/fake_device.py` | 2 field optional; fake_device gửi `{user_name,message,confidence}` |
| **M2** | `rssi` chết end-to-end (backend không ghi Influx) → Vitals RSSI rỗng | `backend: services/mqtt_service.py` · `tools/fake_device.py` | Ghi Influx `rssi` khi payload có; fake_device gửi rssi. **Firmware AT+CSQ vẫn còn nợ** |
| **M4** | `handle_message` nuốt exception (chỉ print chung) → mất bản ghi/alert âm thầm | `backend: services/mqtt_service.py` | Log `[MQTT][DROP] topic=… err=… payload=…`, service không crash |
| **L2** | `WeeklyActivityTrends` hardcode dữ liệu tĩnh, không gọi API | `frontend: WeeklyActivityTrends.tsx` | Nối `useStepsHistory(7)`, vẽ tổng bước/ngày thật (cột trống cho ngày thiếu, highlight hôm nay, tooltip km) |
| **L4** | `set_interval` publish `retain=True` → device reconnect replay lệnh cũ | `backend: api/api_v1/endpoints/devices.py` · `tools/fake_device.py` | `retain=False`; fake_device xử lý `set_interval` + heartbeat theo interval động |

**Doc đã đồng bộ:** `architecture/protocol.md`, `backend.md`, `frontend.md`, `PROJECT_MAP.md`, `DECISIONS.md` (+D-011 telemetry→status, cập nhật D-007).

---

## 2. Còn nợ (cần firmware / quyết định)

- **Firmware publish `event`**: backend có handler `process_event` + topic `eldercare/+/event` nhưng firmware chưa publish.
- **Firmware gửi `rssi`**: cần đọc AT+CSQ (A7680C) đưa vào status payload. Backend đã sẵn đường ghi Influx.
- **M3 đa tenant MQTT** → chọn **D** (xem §4).

---

## 3. Kịch bản kiểm thử (máy có env)

**Chuẩn bị:**
- Backend chạy (`uvicorn`), Frontend (`npm run dev`), `python datn-agent-skills/tools/fake_device.py`.
- Device `dev_01` đã đăng ký + gán wearer có `height_cm` (để tính distance).
- Hữu ích: `mosquitto_pub`/`mosquitto_sub` để bơm payload thủ công.

**TC-B1 · Realtime telemetry sống lại**
1. fake_device chạy, bấm `w` (walk) vài giây.
2. Dashboard → DeviceCard `dev_01`: pin/last_seen cập nhật ≤ chu kỳ; walk_steps tăng realtime không cần reload.
3. ✅ Pass nếu store cập nhật từ MQTT (trước fix: đứng im với thiết bị thật, chỉ mock chạy).

**TC-B2 · Distance đúng walk vs run**
1. fake_device: `w` ~20s rồi `r` ~20s.
2. Influx `telemetry` có field `walk_steps`, `run_steps`. `GET /api/v1/history/steps?days=1` → có `walk_steps`, `run_steps`, `distance_km`.
3. Verify `distance_km ≈ (walk×0.415 + run×0.5)×height_m/1000`.
4. ✅ Pass nếu run dùng hệ số **0.5** (trước fix mọi bước = 0.415).

**TC-B3 · Resolve không nhầm thiết bị**
1. ≥2 device có alert chưa resolve (2 instance fake_device khác DEVICE_ID, hoặc tạo thủ công).
2. `dev_01` bấm `f` → overlay đỏ (alert id = UUID tạm).
3. Bấm "Xác nhận cứu hộ" → Network: `PATCH …/resolve?device_id=dev_01`.
4. ✅ Pass nếu **chỉ** alert `dev_01` thành resolved; device kia vẫn "Chờ xử lý".

**TC-M1 · Alert giả lập không bị nuốt**
1. fake_device bấm `f`.
2. Backend log `Recorded Fall Alert for device dev_01` (KHÔNG có `[MQTT][DROP]`/ValidationError).
3. `GET /history/alerts` có bản ghi mới. ✅

**TC-M2 · RSSI hiển thị**
1. fake_device gửi status (rssi ngẫu nhiên −95..−55).
2. `device/dev_01/vitals` → biểu đồ RSSI có dữ liệu; `GET /history/{id}/telemetry` field `rssi` ≠ null. ✅
   *(Với firmware thật rssi vẫn null tới khi firmware gửi — đúng kỳ vọng.)*

**TC-M4 · Log dead-letter, không crash**
1. `mosquitto_pub -t eldercare/dev_01/status -m '{"foo":1}'` (thiếu `battery`).
2. Backend log `[MQTT][DROP] topic=eldercare/dev_01/status err=… payload={"foo":1}`; message kế tiếp vẫn xử lý. ✅

**TC-L2 · Biểu đồ tuần dùng dữ liệu thật**
1. Có dữ liệu steps vài ngày trong Influx.
2. Dashboard → "Hoạt động 7 ngày": cột theo ngày thật, hôm nay highlight, tooltip "X bước · Y km", ngày trống = 0, tổng bước ở góc. ✅

**TC-L4 · set_interval không retain**
1. `PUT /devices/dev_01` body `{"telemetry_interval":10}`.
2. fake_device log `set_interval -> 10s`; nhịp status đổi ~10s.
3. `mosquitto_sub -t eldercare/dev_01/command` subscribe **sau** khi lệnh đã gửi → KHÔNG nhận lại lệnh cũ. ✅

---

## 4. M3 — Quyết định: D (chấp nhận rủi ro, ghi nhận limitation)

**Vấn đề:** REST scope theo `org_id` (JWT) nhưng MQTT realtime thì không — FE sub `eldercare/+/...` nhận dữ liệu **mọi org**, và `NEXT_PUBLIC_MQTT_USERNAME/PASSWORD` lộ trong JS bundle (ai cũng có thể sub toàn bộ / publish alert giả).

**Quyết định:** **D — chấp nhận ở phạm vi đồ án/demo nội bộ.** KHÔNG fix bằng code (lọc client-side theo device-list rất nguy hiểm: có thể **drop alert té ngã sống còn** khi list chưa load; lại không phải bảo mật thật vì creds vẫn lộ).

**Cần ghi vào báo cáo (mục Hạn chế / Future work):**
- Tầng realtime MQTT chưa cô lập đa tenant; broker dùng credential dùng chung phía client.
- Hướng khắc phục tương lai (không làm trong phạm vi này):
  - **B.** Backend cấp MQTT token động (JWT scoped theo org, vd EMQX ACL) → bỏ creds tĩnh ở client.
  - **C.** Bỏ MQTT trực tiếp ở FE, relay realtime qua backend WS/SSE (tận dụng JWT/org sẵn có).
  - **A.** Topic prefix theo org `eldercare/{org_id}/{device_id}/...` + broker ACL (đắt: đụng firmware).

> Khi nâng cấp bảo mật thật về sau, ưu tiên **C** (sạch kiến trúc) hoặc **B** (ít đụng nhất nếu broker là EMQX).
