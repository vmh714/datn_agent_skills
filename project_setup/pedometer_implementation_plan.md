# Kế hoạch: Pedometer (đã xong) + đổi posture Pitch → Roll + ghi DECISIONS

> **Ngày:** 2026-06-21
> **Người giao:** Solution Architect (qua `/brainstorm`)
> **Đối tượng:** AI/agent thực thi tiếp theo
> **Đọc trước:** `architecture/PROJECT_MAP.md`, `firmware/CLAUDE.md`, `architecture/DECISIONS.md` (theo reading
> protocol trong `.agents/rules/codebase_context.md` — đừng grep mò).

---

## 0. Tóm tắt quyết định (từ buổi brainstorm)

- **Phát hiện ngã** dùng **class "Fall" của HAR model** (đã có), CHƯA làm High-G peak.
- **High-G peak + orientation** đẩy **backlog**, sau gắn làm **bộ lọc precision** giảm false-positive
  (ngồi phịch, đặt thiết bị xuống bàn) — **KHÔNG phải pre-gate tiết kiệm điện** (lý do: xem mục 3, D-013).
- **Orientation/posture dùng ROLL**, không phải pitch (thiết bị đeo **thắt lưng phía trước**).
- Dự án chạy **Phase 1 (thu data train v25→v30) + Phase 2 (edge inference) song song**.

---

## 1. Pedometer: ĐÃ HOÀN THÀNH — chỉ VERIFY, không code lại

Toàn bộ pipeline đếm bước đã tích hợp. Đối chiếu code:

| Hạng mục | Vị trí | Trạng thái |
|---|---|---|
| Thuật toán (magnitude → band-pass 0.5–3.5Hz → ngưỡng động → peak + refractory) | `components/lib_pedometer/pedometer.c` | ✅ |
| Gate theo HAR (`svc_ai_get_latest_prediction()` → chỉ đếm khi Walk/Run), tách `walk_steps`/`run_steps`, refractory theo nhịp (run 200ms / walk 300ms) | `components/svc_imu/imu_service.c:112-136` | ✅ |
| Nạp/lưu NVS định kỳ ~60s (`STEPS_SAVE_PERIOD_BATCHES=120`), giữ qua reboot | `components/svc_imu/imu_service.c:40-60, 280-283` | ✅ |
| Getter public `imu_service_get_steps(walk, run)` | `components/svc_imu/imu_service.c:355-359` | ✅ |
| Đẩy `walk_steps`/`run_steps`/`steps` vào status payload | `components/svc_cloud/svc_cloud.c:279-281` | ✅ |

**Checklist verify (chạy thật, không sửa):**
- [ ] `idf.py build` sạch.
- [ ] Boot log: `Pedometer init. Loaded steps: walk=.. run=..`.
- [ ] Đi bộ → `walk_steps` tăng; chạy → `run_steps` tăng; đứng yên → không tăng.
- [ ] Giữ số bước qua reboot (NVS).
- [ ] `eldercare/{id}/status` chứa đúng `walk_steps`/`run_steps`/`steps`.

> Nếu phát hiện sai lệch so với bảng trên → **code là chuẩn**, cập nhật lại tài liệu (`DECISIONS.md` /
> `architecture/*`) cho khớp.

---

## 2. Code change CÒN LẠI — posture Pitch → Roll

**File:** `components/svc_imu/imu_service.c` (hiện ở dòng **138-140**).

**Hiện tại (pitch):**
```c
// Pitch chỉ dùng để xác định tư thế (nằm/đứng/ngồi)
float accel_pitch = atan2(-ax_body, sqrt(ay_body * ay_body + az_body * az_body)) * RAD_TO_DEG;
last_pitch = kalman_get_angle(&kal_pitch, accel_pitch, gy_body, dt);
```

**Đổi sang roll:**
```c
/// Roll xác định tư thế (nằm/đứng/ngồi) — hợp với mounting thắt lưng phía trước.
float accel_roll = atan2(ay_body, sqrt(ax_body * ax_body + az_body * az_body)) * RAD_TO_DEG;
last_roll = kalman_get_angle(&kal_roll, accel_roll, gx_body, dt);
```

**Các bước bắt buộc:**
1. Đổi rate gyro `gy_body → gx_body` (roll quay quanh trục X, không phải Y).
2. Rename biến/state: `last_pitch → last_roll`, `kal_pitch → kal_roll` (cả khai báo + nơi `kalman_init`).
3. `grep -rn last_pitch components/` → đổi **mọi** chỗ tiêu thụ (status payload, fall logic nếu có).
4. **Caveat — xác minh trước khi chốt:** trục/dấu công thức roll phụ thuộc **orientation vật lý của IMU**
   trên mounting thắt lưng trước. Kiểm tra thực nghiệm: đứng thẳng → roll ≈ 0°, nằm nghiêng/ngã → |roll| lớn.
   Nếu dấu ngược, đảo `atan2(ay_body, ...)` ↔ `atan2(-ay_body, ...)`.
5. Cập nhật comment dòng 138 cho đúng (đang ghi "Pitch").

> `last_pitch/last_roll` hiện chỉ phục vụ posture cho fall (đang backlog) → đổi an toàn, ít rủi ro runtime.

---

## 3. Cập nhật `architecture/DECISIONS.md`

1. Sửa dòng `> **Cập nhật lần cuối:**` → `2026-06-21`.

2. Thêm **D-013** (mới nhất, ngay dưới header, trên D-012), đúng format ADR:

```markdown
### D-013 · Fall = class "Fall" HAR; High-G + orientation (ROLL) là backlog precision-filter
- **Bối cảnh:** `instruction.md` mô tả fall = post-impact (High-G peak + orientation, <1s); `tinyml_model.md`
  lại để `Fall` là 1 class HAR → 2 cơ chế. High-G CHƯA code; ưu tiên hiện tại là pedometer.
- **Quyết định:** (1) Hiện tại fall = output class "Fall" của HAR model, không thêm High-G/orientation ngay.
  (2) High-G peak + orientation đẩy backlog, sau gắn làm **bộ lọc precision** (không phải pre-gate).
  (3) Khi làm orientation check: dùng **ROLL** (mounting thắt lưng trước), thay pitch ở D-003.
- **Lý do:** `svc_ai` đã chạy inference liên tục để gate pedometer (D-010) → High-G "gác cổng tiết kiệm điện"
  vô nghĩa vì ML đã chạy sẵn; vai trò đúng của High-G là **precision**, không phải power. Ship pedometer
  trước đúng ưu tiên; fall thuần ML rẻ nhất, đủ giai đoạn đầu. Roll thay pitch vì với mounting thắt lưng
  trước, trục phân biệt đứng/nằm là roll. Phát alert + cooldown vẫn ở svc_cloud (D-006).
- **Phase:** Phase 1 (thu data train v25→v30) song song Phase 2 (edge inference).
```

3. Thêm 1 dòng vào cuối **D-003**:
   `- (2026-06-21) Posture chuyển pitch → ROLL cho hợp mounting thắt lưng trước — xem D-013.`

4. Thêm 1 dòng vào phần "Còn nợ" của **D-007**:
   `datn-agent-skills/CLAUDE_firmware.md` còn ghi topic cũ `v1/devices/{id}/...` — **stale**, cần sync về
   canonical `eldercare/{id}/alert/fall|status|imu_stream|command` (`firmware/CLAUDE.md` đã đúng).

---

## 4. Backlog (KHÔNG làm bây giờ — ghi để nhớ)

- **High-G + orientation precision filter cho fall:** thêm High-G peak (`|accel|` vượt ngưỡng, ~vài dòng
  trong `svc_imu`) + orientation ROLL; chỉ chạy như lớp xác nhận sau khi HAR báo "Fall" → giảm false-positive.
- **Sync doc:** cập nhật `datn-agent-skills/CLAUDE_firmware.md` mục MQTT Topics cho khớp `overview.md` /
  `firmware/CLAUDE.md`.

---

## 5. Verification tổng (sau khi thực thi mục 2-3)

1. `idf.py build` sạch sau đổi roll.
2. `grep -rn last_pitch components/` → 0 kết quả.
3. Thực nghiệm roll: đứng thẳng ≈ 0°, nằm/nghiêng → |roll| lớn (dấu đúng).
4. Pedometer vẫn chạy đúng (checklist mục 1) — không bị regress.
5. `DECISIONS.md`: D-013 trên cùng, D-003 & D-007 có dòng note; "Cập nhật lần cuối" = 2026-06-21.
