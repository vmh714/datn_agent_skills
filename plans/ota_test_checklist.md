# Checklist Test OTA End-to-End

> **Mục tiêu:** Xác nhận toàn bộ luồng OTA hoạt động đúng:
> Frontend chọn version → Backend publish MQTT → Firmware tải binary → Flash → Reboot → Version mới lên DB.
>
> **Ngày tạo:** 2026-06-23
> **Liên quan:** `components/svc_ota/`, `endpoints/firmware.py`, `DeviceConfig.tsx`

---

## 1. Chuẩn bị môi trường

### Backend
- [ ] Backend đang chạy, `/api/v1/firmware/versions` trả về 3 phiên bản mock (test bằng Swagger `/docs`)
- [ ] Thư mục `static/firmware/` đã tạo trong repo backend
- [ ] Đặt một file binary hợp lệ vào `static/firmware/firmware_v1.3.0.bin`
  - Có thể dùng chính file build hiện tại: copy `build/eldercare_firmware.bin` vào đây
- [ ] Backend phục vụ static file — thêm vào `main.py` nếu chưa có:
  ```python
  from fastapi.staticfiles import StaticFiles
  app.mount("/static", StaticFiles(directory="static"), name="static")
  ```
- [ ] Kiểm tra URL binary accessible: `curl http://localhost:8000/static/firmware/firmware_v1.3.0.bin` → trả về binary, không phải 404

### MQTT Broker
- [ ] MQTT broker đang chạy (local Mosquitto hoặc remote)
- [ ] Mở terminal subscribe topic command để quan sát lệnh OTA được gửi xuống:
  ```bash
  mosquitto_sub -h <broker> -t "eldercare/+/command" -v
  ```

### Firmware
- [ ] `partitions.csv` có `ota_0`, `ota_1`, `otadata` — đã kiểm tra ✅ (đã có sẵn)
- [ ] Build firmware với `CONFIG_PARTITION_TABLE_CUSTOM=y` trỏ đúng `partitions.csv`
- [ ] Kiểm tra binary size < 2MB (giới hạn partition OTA): `ls -lh build/*.bin`
- [ ] Flash firmware lần đầu qua USB (factory partition): `idf.py flash`
- [ ] Monitor log để xác nhận device boot vào `STATE_INIT` → `STATE_CONNECTING` → `STATE_NORMAL`

### Frontend
- [ ] Frontend đang chạy (`npm run dev`)
- [ ] Đăng nhập thành công, vào trang `device/[id]/settings`
- [ ] Card "Cập nhật Firmware (OTA)" hiện ra — có dropdown chọn version

---

## 2. Test Happy Path (OTA thành công)

### Bước 1 — Verify API
- [ ] Frontend gọi `GET /api/v1/firmware/versions` thành công — dropdown hiện 3 phiên bản
- [ ] Version hiện tại của device hiện đúng trong badge (badge "Phiên bản hiện tại")
- [ ] Button "Cập nhật firmware" bị disable khi chưa chọn version
- [ ] Button bị disable khi chọn đúng version hiện tại (thông báo "Thiết bị đã chạy phiên bản này")

### Bước 2 — Trigger OTA từ Frontend
- [ ] Chọn version mới (khác version hiện tại) trong dropdown
- [ ] Changelog hiện ra đúng với version đã chọn
- [ ] Nhấn "Cập nhật firmware"
- [ ] Button hiện "Đang gửi lệnh OTA..." (loading state)
- [ ] Toast success "Đã gửi lệnh OTA..." xuất hiện

### Bước 3 — Verify MQTT Command
- [ ] Terminal mosquitto_sub nhận được message trên topic `eldercare/{device_id}/command`:
  ```json
  {"action": "ota_update", "url": "http://<backend_ip>:8000/static/firmware/firmware_v1.3.0.bin"}
  ```
- [ ] `action` đúng là `ota_update`, `url` trỏ đúng file binary

### Bước 4 — Firmware nhận & xử lý
- [ ] Log firmware hiện: `SVC_CLOUD: Action: ota_update. URL: http://...`
- [ ] `sys_manager` log: `FSM State Transition: STATE_NORMAL -> STATE_OTA`
- [ ] `svc_ota` log: `OTA target partition: ota_0 at offset 0x...`
- [ ] Log hiện HTTP status 200 và firmware size (bytes)
- [ ] Log ghi tiến trình: `OTA progress: XXXX bytes written` (hoặc tương đương)
- [ ] Log cuối: `OTA success! Written XXXX bytes. Rebooting in 2s...`
- [ ] Device reboot sau 2 giây

### Bước 5 — Verify sau reboot
- [ ] Device boot lại, log hiện đúng version mới (nếu firmware mới có version string khác)
- [ ] Device kết nối lại MQTT, FSM trở về `STATE_NORMAL`
- [ ] `esp_ota_get_running_partition()` trả về `ota_0` (không còn là factory)
- [ ] Frontend poll lại device sau 60s — `firmwareVersion` cập nhật đúng (cần backend cập nhật DB)

---

## 3. Test Failure Scenarios (Rollback)

### Scenario A — URL sai / server không reach được
- [ ] Sửa tạm `download_url` trong mock backend thành URL không tồn tại
- [ ] Trigger OTA
- [ ] Firmware log: `HTTP open failed` hoặc `HTTP server returned status 404`
- [ ] `svc_ota` log: `OTA failed. Rolling back to STATE_NORMAL.`
- [ ] `sys_manager` log: `FSM State Transition: STATE_OTA -> STATE_NORMAL`
- [ ] Device tiếp tục hoạt động bình thường ở `STATE_NORMAL` — không bị treo

### Scenario B — Binary bị corrupt / size = 0
- [ ] Tạo file `firmware_corrupt.bin` rỗng (0 bytes), đặt vào static
- [ ] Trigger OTA với URL trỏ file này
- [ ] Firmware log: `No data received from server` hoặc `esp_ota_end failed`
- [ ] Device rollback về `STATE_NORMAL` — firmware cũ vẫn chạy

### Scenario C — MQTT broker mất kết nối khi đang ở STATE_NORMAL
- [ ] Ngắt broker giữa chừng khi device đang NORMAL
- [ ] Device ở `STATE_CONNECTING` (retry)
- [ ] Khởi động lại broker → device reconnect → `STATE_NORMAL`
- [ ] OTA trigger sau đó vẫn hoạt động bình thường

### Scenario D — Mất mạng giữa chừng khi đang download firmware
- [ ] Trigger OTA, ngắt mạng sau khi download bắt đầu
- [ ] `esp_http_client_read` trả về lỗi → `esp_ota_abort`
- [ ] Device rollback về `STATE_NORMAL`

---

## 4. Kiểm tra Frontend UX

- [ ] Khi thiết bị offline (status = offline): button OTA vẫn có thể nhấn nhưng backend sẽ publish MQTT (device sẽ nhận khi online lại — QoS 1)
- [ ] Không có double-submit: nhấn nút 2 lần liên tiếp → chỉ 1 request gửi (button disabled trong lúc pending)
- [ ] Responsive: card OTA hiển thị đúng trên mobile

---

## 5. Ghi chú khi test với 4G (không có WiFi)

- [ ] Đảm bảo backend URL trong `download_url` là **IP public** hoặc **domain** — không phải `localhost` hay `192.168.x.x` (device 4G không cùng LAN)
- [ ] Dùng ngrok hoặc Render URL để expose backend: `https://xxx.ngrok.io/static/firmware/firmware_v1.3.0.bin`
- [ ] Timeout `esp_http_client` 30s có thể cần tăng nếu 4G chậm (sửa trong `svc_ota.c`)
- [ ] Binary ~2MB trên 4G ≈ 10–30s download tuỳ sóng

---

## 6. Kết quả kỳ vọng tổng thể

| Kịch bản | Kết quả mong đợi |
|---|---|
| OTA thành công | Device reboot với firmware mới, FSM về NORMAL |
| URL không tồn tại | Rollback NORMAL ngay, không treo |
| Binary corrupt | `esp_ota_end` fail → rollback, firmware cũ giữ nguyên |
| Mất mạng giữa download | abort + rollback, không brick device |
| Trigger khi offline | MQTT QoS 1 giữ lại, device nhận khi online |
