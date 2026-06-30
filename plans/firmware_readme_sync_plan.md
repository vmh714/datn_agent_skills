# Plan: Đồng bộ README component firmware với code hiện tại

> **Giao cho model rẻ.** Mục tiêu: sửa các README trong `firmware/components/*/README.md` cho **khớp code đang chạy** (sau loạt thay đổi network auto-detect, FSM gating, MQTT watchdog, A7680C RST).

## Nguyên tắc bắt buộc (đọc kỹ trước khi sửa)
1. **Code là chuẩn.** Với MỖI README: ĐỌC file `.c`/`.h` của component đó TRƯỚC, rồi sửa README cho khớp. KHÔNG bịa, KHÔNG chép từ plan này mà không kiểm code.
2. **Đối chiếu DECISIONS** liên quan: `datn_agent_skills/project_setup/architecture/DECISIONS.md` (D-019 RST/PWRKEY, D-021 post-impact, D-022 RSSI, D-024 gating/watchdog/boot, D-025 data integrity, D-026 auto-detect 4G).
3. **Chỉ bump `> Cập nhật cuối (Timestamp)` → 2026-06-30 ở file THỰC SỰ có sửa nội dung.** File không đổi thì để nguyên ngày.
4. **Không tô vẽ tính năng chưa có trong code.** Nếu code chưa có thứ DECISIONS mô tả → ghi đúng hiện trạng code (hoặc bỏ), không claim.
5. Giữ văn phong + cấu trúc heading sẵn có của từng README; chỉ sửa/ô thêm phần liên quan, không viết lại toàn bộ.

## Việc theo từng file

### 🔴 Ưu tiên cao — drift rõ rệt

**`firmware/components/drv_a7680c/README.md`** — STALE NẶNG. README mô tả API **PWRKEY** không tồn tại.
- Đọc [drv_a7680c.c](firmware/components/drv_a7680c/drv_a7680c.c) + [drv_a7680c.h](firmware/components/drv_a7680c/include/drv_a7680c.h) lấy API THẬT (hiện tại là `drv_a7680c_init(rst_pin)`, `drv_a7680c_reset(...)` — **no-op**, `drv_a7680c_emergency_mqtt_publish(...)`).
- Xóa/sửa các mục `drv_a7680c_power_on()`, `drv_a7680c_power_off()`, `A7680C_PWRKEY_PIN` (không có trong code).
- Ghi đúng: breakout **KHÔNG có chân PWRKEY**; điều khiển qua **RST** nhưng đã **vô hiệu** (đụng RST là module tắt nguồn) → `drv_a7680c_reset()` chỉ log + return (no-op), module dựa mạch auto-power-on. Nguồn: **D-019**.
- Thêm mục `drv_a7680c_emergency_mqtt_publish` (MQTT nội bộ qua AT khi PPP đứt) nếu README chưa có.
- Bump timestamp.

**`firmware/components/svc_imu/README.md`** — mâu thuẫn nội bộ.
- [README dòng 29](firmware/components/svc_imu/README.md) còn ghi `svc_ai_process_window` chạy ở `STATE_NORMAL / STATE_STREAMING` — **mâu thuẫn** với ma trận gating ngay bên dưới (dòng 66-79) đã ghi STREAMING bỏ AI. Sửa dòng 29 → **chỉ `STATE_NORMAL`** (đối chiếu [imu_service.c:265](firmware/components/svc_imu/imu_service.c#L265): điều kiện hiện là `is_normal`).
- Rà phần luồng dữ liệu cho khớp: NORMAL = Kalman+impact+pedometer+AI; STREAMING = chỉ Kalman+batch. Nguồn: **D-024**.
- Bump timestamp.

### 🟡 Ưu tiên vừa — bổ sung/đối chiếu

**`firmware/components/sys_manager/README.md`** (đang 2026-06-17):
- Thêm **ma trận service × state** (copy/khớp bảng trong [firmware/CLAUDE.md](firmware/CLAUDE.md) mục FSM): Drain FIFO mọi state; Kalman/normalize NORMAL+STREAMING; AI/pedometer/impact + telemetry + RSSI chỉ NORMAL; stream chỉ STREAMING.
- Thêm **cờ comms-critical** (`sys_manager_bump_comms_critical`/`is_comms_critical`, monotonic expiry) — nguồn **D-022**; và stream-timeout timer (auto STOP_STREAM).
- Đối chiếu [sys_manager.c](firmware/components/sys_manager/sys_manager.c) cho đúng transition. Bump timestamp.

**`firmware/components/svc_cloud/README.md`** (đang 2026-06-17):
- Watchdog MQTT 2-bậc (60s stop/start, 150s `esp_restart`) **đã có** (dòng 15) — kiểm lại số liệu khớp [svc_cloud.c](firmware/components/svc_cloud/svc_cloud.c) (`svc_cloud_task`).
- Nếu code đã set các tham số MQTT (`session.keepalive`, `network.timeout_ms`, `reconnect_timeout_ms`, `task.priority`) thì bổ sung 1 mục ngắn; **nếu code CHƯA set thì bỏ qua** (đừng claim).
- Chính sách drop/giữ IMU batch khi mất MQTT + (nếu liên quan) gap-detection phía FE — tham chiếu **D-025** một dòng. Bump timestamp nếu có sửa.

**`firmware/components/svc_ai/README.md`** (đang 2026-06-17):
- Đảm bảo có **Post-Impact Confirmation FSM** (`CONFIRMING`/abort, `fall_confirm_window`) — nguồn **D-021**; và nêu AI chỉ chạy ở `STATE_NORMAL` (D-024). Đối chiếu [svc_ai.c](firmware/components/svc_ai/svc_ai.c). Bump timestamp nếu có sửa.

### 🟢 Đã xong / không cần đụng
- **`svc_network/README.md`** — đã cập nhật 2026-06-30 (auto-detect sniff bus, LTE fast-path). Chỉ **đọc lại xác nhận** khớp [svc_network.c](firmware/components/svc_network/svc_network.c), không sửa thêm trừ khi phát hiện sai.
- **`drv_battery`, `drv_mpu6050`, `lib_kalman`, `lib_pedometer`, `lib_tinyml`, `lib_model`** — không đổi code đợt này → **để nguyên** (kể cả timestamp), trừ khi đọc thấy drift thật.

## Verification (sau khi sửa)
1. `grep -ri "PWRKEY\|power_on\|power_off" firmware/components/drv_a7680c/README.md` → không còn (trừ khi code thật có).
2. `grep -rn "NORMAL / STATE_STREAMING\|NORMAL/STREAMING" firmware/components/svc_imu/README.md` → không còn ở chỗ mô tả svc_ai.
3. Mỗi README đã sửa có `Cập nhật cuối` = 2026-06-30; file không sửa giữ ngày cũ.
4. Đọc chéo: mọi API/hằng số/chân GPIO nêu trong README phải trùng `.h`/`.c` tương ứng (không còn hàm "ma").
5. Không có README nào claim tính năng mà code chưa có.
