# Checklist Test: Firmware Upload & DB-backed OTA

> **Mục tiêu:** Kiểm tra luồng upload firmware lên hệ thống (backend + frontend) và tích hợp với luồng OTA.
> File này bổ sung cho `ota_test_checklist.md` (phần test firmware-side: tải, flash, reboot).
> Test file này TRƯỚC — khi đã có file .bin trong DB mới chạy `ota_test_checklist.md`.
>
> **Ngày tạo:** 2026-06-23  
> **Liên quan:** `endpoints/firmware.py`, `app/settings/page.tsx`, `alembic/versions/b2e9f4a1c3d7_*`

---

## 0. Chuẩn bị bắt buộc

- [ ] Chạy `alembic upgrade head` — tạo bảng `firmware_releases`
- [ ] Xác nhận bảng đã có: `psql -c "\d firmware_releases"` hoặc kiểm tra qua pgAdmin
- [ ] Start backend: `uvicorn app.main:app --reload`
- [ ] Xác nhận thư mục `static/firmware/` được tạo tự động khi backend start
- [ ] Chuẩn bị file test: copy `firmware/HAR-and-Fall-detection-firmware/build/eldercare_firmware.bin` ra desktop (hoặc dùng file giả `echo test > test.bin`)

---

## 1. Test Backend — API trực tiếp (Swagger `/docs`)

### 1.1 GET /api/v1/firmware/versions — DB rỗng
- [ ] Login lấy token (POST `/api/v1/auth/login`)
- [ ] GET `/api/v1/firmware/versions` → trả về `[]` (array rỗng, không phải 404)

### 1.2 GET /api/v1/auth/me — kiểm tra role
- [ ] Dùng token ADMIN account → trả về `{"role": "ADMIN", ...}`
- [ ] Dùng token MANAGER account → trả về `{"role": "MANAGER", ...}`

### 1.3 POST /api/v1/firmware/upload — MANAGER bị từ chối
- [ ] Dùng token MANAGER
- [ ] Upload bất kỳ file → nhận **403 Forbidden** `"Yêu cầu quyền ADMIN"`

### 1.4 POST /api/v1/firmware/upload — ADMIN upload thành công
Dùng token ADMIN, form-data:
- `file`: file `.bin` hợp lệ
- `version`: `1.4.0`
- `release_date`: `2026-06-23`
- `changelog`: `Fix OTA timeout`
- `is_stable`: `true`

Kỳ vọng:
- [ ] Status **201 Created**
- [ ] Response có `version`, `download_url`, `sha256`, `bin_size`, `is_latest: true`
- [ ] `download_url` format: `http://localhost:8000/static/firmware/firmware_v1.4.0_<sha8>.bin`
- [ ] File thực sự tồn tại trong `static/firmware/`: `ls backend/.../static/firmware/`
- [ ] `curl <download_url>` → trả về binary (không phải HTML/404)

### 1.5 GET /api/v1/firmware/versions — sau upload
- [ ] Trả về 1 record, `is_latest: true`, `download_url` đúng
- [ ] `sha256` khớp với `sha256sum <file>` trên máy

### 1.6 Upload version trùng — bị từ chối
- [ ] Upload lại `version: 1.4.0` → nhận **409 Conflict** `"Version 1.4.0 đã tồn tại"`

### 1.7 Upload file không phải .bin — bị từ chối
- [ ] Upload file `.txt` → nhận **422 Unprocessable Entity** `"Chỉ chấp nhận file .bin"`

### 1.8 Upload version mới → rotate is_latest
- [ ] Upload `version: 1.5.0` (file .bin khác)
- [ ] GET `/api/v1/firmware/versions`:
  - [ ] v1.5.0: `is_latest: true`
  - [ ] v1.4.0: `is_latest: false`

### 1.9 POST /api/v1/firmware/{device_id}/update — version không tồn tại
- [ ] Body: `{"version": "9.9.9", "download_url": "http://..."}`
- [ ] Nhận **404** `"Firmware version 9.9.9 không tồn tại"`

### 1.10 POST /api/v1/firmware/{device_id}/update — version hợp lệ
- [ ] Body: `{"version": "1.5.0", "download_url": "<download_url từ response>"}`
- [ ] MQTT broker nhận message trên `eldercare/{device_id}/command`:
  ```json
  {"action": "ota_update", "url": "http://localhost:8000/static/firmware/firmware_v1.5.0_XXXXXXXX.bin"}
  ```
- [ ] Response: `{"ok": true, "device_id": "...", "target_version": "1.5.0"}`

---

## 2. Test Frontend — trang Settings

### 2.1 Login MANAGER — không thấy form upload
- [ ] Đăng nhập bằng account MANAGER
- [ ] Vào `/settings`
- [ ] Card "Upload Firmware (ADMIN)" **không hiển thị**
- [ ] Card MQTT Config và Notification vẫn hiển thị bình thường

### 2.2 Login ADMIN — thấy form upload
- [ ] Đăng nhập bằng account ADMIN
- [ ] Vào `/settings`
- [ ] Card "Upload Firmware (ADMIN)" hiện ra với:
  - [ ] Input file `.bin`
  - [ ] Input version, ngày phát hành
  - [ ] Textarea changelog
  - [ ] Switch is_stable
  - [ ] Button "Upload firmware" **disabled** khi chưa điền đủ

### 2.3 Upload firmware từ UI
- [ ] Chọn file `.bin`
- [ ] Điền version: `1.6.0`, changelog: `UI test`
- [ ] Nhấn "Upload firmware"
- [ ] Button hiện "Đang upload..."
- [ ] Sau upload: toast "Firmware 1.6.0 đã upload thành công"
- [ ] Form reset về trống

### 2.4 Kiểm tra dropdown DeviceConfig sau upload
- [ ] Vào `device/[id]/settings`
- [ ] Dropdown version hiển thị v1.6.0 (và các version cũ)
- [ ] Badge "Mới nhất" hiện đúng trên v1.6.0

### 2.5 Download URL đúng host khi dùng ngrok
- [ ] Nếu có ngrok: start `ngrok http 8000`, lấy URL `https://xxxx.ngrok.io`
- [ ] Upload firmware khi backend đang dùng ngrok URL
- [ ] GET `/api/v1/firmware/versions` → `download_url` có prefix `https://xxxx.ngrok.io/static/...`
- [ ] Truy cập `download_url` từ mobile (4G) → tải được file

---

## 3. Test tích hợp đầy đủ (Upload → OTA)

> Sau khi pass section này, tiếp tục với `ota_test_checklist.md` để test phần firmware-side.

- [ ] Upload firmware mới v1.7.0 từ trang Settings (ADMIN)
- [ ] Vào `device/[id]/settings` → chọn v1.7.0 trong dropdown
- [ ] Nhấn "Cập nhật firmware"
- [ ] MQTT broker nhận đúng command với `download_url` của v1.7.0
- [ ] URL trong command có thể `curl` được → trả về binary (xác nhận trước khi flash thật)

---

## 4. Edge cases

| Tình huống | Kết quả mong đợi |
|---|---|
| Upload file 0 bytes | 422 "File không được rỗng" |
| Upload khi MQTT không connect | /upload thành công (lưu DB + file), /update trả 503 |
| 2 ADMIN upload cùng lúc | Không race condition — `is_latest` rotate đúng |
| Xóa file vật lý trong `static/firmware/` | DB record còn nhưng `curl <url>` → 404; rebuild sau khi re-upload |
| Backend restart | `static/firmware/` vẫn còn file, DB vẫn còn record → hoạt động bình thường |

---

## 5. Ghi chú khi chưa có phần cứng

Các bước ở section 1 và 2 có thể test hoàn toàn **không cần ESP32**:
- Dùng file `.bin` giả (bất kỳ binary file nào đổi extension thành `.bin`)
- Monitor MQTT bằng `mosquitto_sub -t "eldercare/+/command" -v` để xác nhận command được publish
- Section 3 cần ESP32 đã flash firmware OTA-capable → kết hợp với `ota_test_checklist.md`
