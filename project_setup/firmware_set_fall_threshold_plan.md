# Firmware Plan — `set_fall_threshold` (chỉnh độ nhạy phát hiện ngã từ xa)

> **Bối cảnh:** Phần WEB đã xong & test live (2026-06-18) — xem `web_fullstack_fixes` + `architecture/DECISIONS.md` D-012. Backend đã có cột `devices.fall_threshold`, publish command `set_fall_threshold`, sync echo từ status; FE có slider 15–95%. **Firmware là mảnh còn lại** để lệnh thực sự tác động lên thiết bị.
> **Nguyên tắc:** làm y khuôn `set_interval` đã có (NVS + command handler + echo status). Path `file:line` tương đối gốc firmware (xem `architecture/PROJECT_MAP.md` §1).

## 1. Mục tiêu
Cho phép đổi **ngưỡng xác suất chốt ngã** (hiện hardcode `0.6`) từ xa qua MQTT, lưu NVS để bền vững qua reboot, và echo lại trong status để web đồng bộ. Cao = ít báo nhầm (precision↑) nhưng dễ bỏ sót (recall↓).

## 2. MQTT contract (đã chốt phía web)
- **Command (sub)** `eldercare/{id}/command`: `{"action":"set_fall_threshold","val":<0.15..0.95>}`.
- **Status (pub)** `eldercare/{id}/status`: thêm field `"fall_threshold": <float>` (echo giá trị đang áp) — backend `process_status` đã đọc field này để sync DB.

## 3. Điểm chạm trong firmware
| File:line (PROJECT_MAP) | Việc |
|---|---|
| `lib_tinyml/tflite_wrapper.cpp:235` | Thay hằng `prob[FALL] >= 0.6` → so với biến runtime `g_fall_threshold` |
| `lib_tinyml/include/tflite_wrapper.h` | Thêm API `tflite_set_fall_threshold(float)` + `tflite_get_fall_threshold()`; biến nội bộ default `0.6f` |
| `svc_cloud/svc_cloud.c` (gần handler command + `:28` NVS `config/tel_int`) | (a) parse action `set_fall_threshold`, clamp **0.15–0.95**, bỏ qua nếu ngoài dải; (b) lưu NVS key `config/fall_thr`; (c) gọi `tflite_set_fall_threshold(val)` |
| `svc_cloud.c` (boot init, chỗ đọc `tel_int`) | Đọc NVS `config/fall_thr` (default `0.6`) lúc khởi động → áp qua setter |
| `svc_cloud.c` (chỗ build JSON status) | Thêm `"fall_threshold"` = `tflite_get_fall_threshold()` vào payload status |

## 4. Các bước
1. **lib_tinyml**: thêm biến `static float s_fall_threshold = 0.6f;` + setter/getter (header + .cpp). Sửa `:235` dùng `s_fall_threshold` thay `0.6`.
   - ⚠️ **Thread-safety**: `svc_ai` đọc threshold trong vòng inference, command handler ghi từ task khác. Dùng `volatile float` (đọc/ghi float 32-bit là atomic trên ESP32-S3) hoặc `portMUX` nếu muốn chặt. Float read đơn lẻ → `volatile` là đủ.
2. **svc_cloud command handler**: thêm nhánh `else if (action=="set_fall_threshold")` → `val` clamp 0.15–0.95 → `nvs_set` `config/fall_thr` + commit → `tflite_set_fall_threshold(val)`. (Mirror đúng nhánh `set_interval`.)
3. **Boot init**: đọc `config/fall_thr` từ NVS (default 0.6) → `tflite_set_fall_threshold(...)`. Đặt cạnh chỗ đọc `config/tel_int`.
4. **Status echo**: thêm `fall_threshold` vào JSON status (cjson/snprintf chỗ đang build `battery/steps/...`).
5. Build + flash + verify (mục 5).

## 5. Acceptance test (không cần fake — dùng web thật + thiết bị thật)
1. Web → trang Cấu hình thiết bị → kéo slider sang **80%** → Lưu. Backend publish `{"action":"set_fall_threshold","val":0.8}`.
2. Firmware log: nhận command → `set_fall_threshold -> 0.8` → ghi NVS.
3. Status kế tiếp có `"fall_threshold":0.8` → web GET `/devices/{id}` trả `0.8` (đồng bộ).
4. **Reboot thiết bị** → status sau boot vẫn `0.8` (NVS bền vững).
5. Hành vi: ở ngưỡng 0.8, các cú giả-ngã nhẹ (prob ~0.6–0.7) **không** còn kích `AI_EVT_FALL_DETECTED`; hạ về 0.3 thì kích lại → xác nhận threshold thực sự tác động.

## 6. Lưu ý / liên quan
- **Không** đụng `IMU_WINDOW_SIZE`/model (D-002) — chỉ đổi ngưỡng quyết định post-inference.
- Cooldown chống spam (`FALL_COOLDOWN_US=15s`, `svc_cloud.c:304`) độc lập, giữ nguyên.
- Sau khi xong: cập nhật `architecture/firmware.md` + `PROJECT_MAP.md` (API mới của lib_tinyml) + đánh dấu D-012 phần "firmware đã làm".
- Liên quan còn nợ firmware khác: publish `event` (backend có handler), gửi `rssi` (AT+CSQ) — xem `DECISIONS.md` D-007.
