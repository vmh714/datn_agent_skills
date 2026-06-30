# Plan — Chốt sổ đồ án: bổ sung REPORT mô tả rõ hệ thống + backlog cần xây thêm

> Deliverable: (A) hướng dẫn bổ sung luận văn cho khớp hệ thống hiện tại, (B) danh sách phần còn phải xây, (C) polish trước chốt.

## Context

Hai tính năng mới đã code + đã cập nhật docs kiến trúc nhưng **luận văn chưa mô tả**:
- **D-021** — Phát hiện ngã 2 pha: ML trigger (θ) → FSM `CONFIRMING` quan sát post-impact (Idle+ROLL=lying) trong `fall_confirm_window`s → CONFIRMED; impact/free-fall detector (SVM accel thô) boost. Mục tiêu giảm báo giả, giữ recall.
- **D-022** — RSSI 4G: `rssi_interval` cấu hình (0=tắt) + guard comms-critical (cờ `sys_manager`) không rớt link lúc confirm/alert.

Mục tiêu phiên này: mô tả hệ thống trong REPORT cho đúng hiện trạng, chốt danh sách việc còn lại, và chải chuốt.

> ⚠️ **Đính chính so với khảo sát tự động** (đã verify bằng code): **battery ĐÃ đọc ADC thật** (`drv_battery_read_percent()`, svc_cloud.c:471 — KHÔNG phải hardcode 100); **OTA ĐÃ hiện thực** (`svc_ota` + `CLOUD_CMD_OTA_UPDATE`→`STATE_OTA`, sys_manager.c:53-56); **RSSI 4G đã đo + publish** (svc_cloud.c:467 + `cellular_rssi_update_task`). Những mục này KHÔNG còn là blocker.

---

## PHẦN A — Bổ sung REPORT để mô tả rõ hệ thống

> File gốc: `report/Do_an_tot_nghiep_Vu_Manh_Hung/Chuong/`. Mỗi mục ghi rõ chèn ở đâu.
> ⚠️ Tránh drift: confirmation là **FSM phụ trong `svc_ai`** (`FALL_FSM_NORMAL`/`CONFIRMING`), KHÔNG thêm system-state `STATE_FALL_CONFIRMING`. Cấu hình đi qua **`config/set` gộp**, KHÔNG tạo topic `config/rssi`. Cờ comms-critical là **runtime ở firmware**, KHÔNG phải cột DB.

**A1 · Ch3 `3_Phuong_phap_de_xuat.tex` (sau `sec:3.2`)** — thêm `\subsection{Cơ chế xác nhận ngã hai pha (Post-Impact Confirmation)}`: vì sao θ=0.25 nhạy (ưu tiên recall) ⇒ cần pha xác nhận; mô tả ML-trigger → quan sát post-impact (Idle+ROLL=lying, đa số window/N giây) → CONFIRMED/ABORT; impact/free-fall (SVM accel thô <0.6g→>2.5g) làm bằng chứng boost. Đây là chỗ đặt **đóng góp giảm-báo-giả**.

**A2 · Ch4.2 `4_2_Thiet_ke.tex` — Kiến trúc Firmware:** (i) bổ sung sơ đồ/đoạn FSM phụ `svc_ai`; (ii) `svc_imu` thêm impact detector; (iii) `sys_manager` cờ comms-critical (D-022). **Bảng devices**: thêm `fall_confirm_window`, `rssi_interval` (KHÔNG thêm `comms_critical_flag`). **Thiết kế giao thức**: `config/set`+`config/status` thêm 2 field.

**A3 · Ch4.1 `4_1_Phan_tich_yeu_cau.tex` (`section:2.4` NFR)** — thêm yêu cầu phi chức năng **"Độ tin cậy cảnh báo"**: giảm false-positive trong ADL nhưng giữ Fall recall ≥ ngưỡng; confirmation delay ≈ N giây. (Nền lý do cho D-021.) Thêm 1 dòng đặc tả "cấu hình thiết bị từ xa" liệt kê tham số.

**A4 · Ch5 `5_Trien_khai_thuc_nghiem.tex`** — (i) §5.4/§5.x: thêm `\subsubsection` triển khai Confirmation FSM (pseudo-code NORMAL→CONFIRMING→CONFIRMED/ABORT) + impact detector; (ii) §5.5 backend & §5.6 FE: bổ sung `fall_confirm_window` + `rssi_interval` vào luồng config-sync (FE form → PUT → `config/set` → device → echo `config/status` → DB); (iii) **sửa "cooldown 10-20s" → 15s** cho khớp code; (iv) §5.7 integration test: thêm **ma trận test báo giả** (ngồi phịch/nhảy→ABORT; ngã thật→CONFIRMED; guard không rớt link lúc confirm) — số liệu để trống chờ đo.

**A5 · Ch6 `6_Ket_luan.tex`** — thêm đóng góp #4 "phát hiện ngã 2 pha giảm báo giả không mất recall"; đưa vào hướng phát triển: CMUX (đo RSSI không rớt link), bảo mật MQTT per-device, sleep mode.

**A6 · Hình** — `fsm.png` vẽ lại (thêm nhánh CONFIRMING của svc_ai); `erd.png` regen (đã có Mermaid + 2 cột mới); xem `plans/report_missing_figures_plan.md`.

**A7 · Glossary `Tu_viet_tat.tex`** — thêm: SVM (Signal Vector Magnitude), post-impact, free-fall, RSSI, comms-critical (nếu dùng trong thân bài).

---

## PHẦN B — Backlog hệ thống cần xây thêm (đã đối chiếu code)

> Mức độ: 🔴 blocker chốt sổ · 🟡 nên có · ⚪ future work (ghi vào "hướng phát triển", không cần làm).

### Firmware
- 🟡 **Publish topic `event`** — backend có `process_event()`, firmware chưa gửi (DECISIONS D-007 còn nợ). Cần verify nhanh; nếu chưa thì thêm event log (boot/OTA/disconnect).
- 🟡 **D-022 rssi_interval + guard comms-critical** — *đang code ở cửa khác*; cần build firmware (user tự build) + test.
- 🟡 **Test on-device D-021** — kiểm CONFIRMED vs ABORT với động tác thật (gắn vào §5.7).
- ⚪ **STATE_ERROR transition** — OTA đã có; chỉ còn ERROR path chưa hiện thực (PROJECT_MAP §1.3). Để future work.
- ⚪ Sleep mode / wake-on-motion (`plans/sleep_mode_implementation_plan.md`).

### Backend
- 🔴 **Migration `rssi_interval`** — *đang code ở cửa khác*; phải có file Alembic + `alembic upgrade head` trước deploy. (`fall_confirm_window` migration `d1e2f3a4b5c6` đã xong.)
- 🟡 **`verify_pipeline.py`** — script eval `v30_optimize` trên verification dataset → confusion matrix (DECISIONS D-017 còn nợ). Cần cho số liệu §5.7/Ch4.3.
- ⚪ Dọn measurement InfluxDB `imu_windowed` cũ.

### Frontend
- 🟡 **Form `rssi_interval`** — *đang code ở cửa khác* (state đã thấy thêm `rssiInterval`); xác nhận card + dropdown "Tắt/60–600s".
- 🟡 **Screenshot UI cho báo cáo** (dashboard, overlay ngã, config, data-collection) — `report_missing_figures_plan.md` mục C.

### TinyML / Model
- 🟡 **Hình kết quả**: confusion matrix v30_optimize (float+INT8), chart latency/size, sơ đồ kiến trúc + windowing (`report_missing_figures_plan.md` A/B).
- ⚪ v32 (window 128/256) — thử nghiệm, chưa kết quả.

### Bảo mật (đều ⚪ — ghi "hướng phát triển", ngoài scope đồ án)
- Per-device MQTT creds + ACL `eldercare/<id>/#`; mTLS client cert (DECISIONS D-020 ghi chú chưa làm).

### Luận văn / REPORT
- 🔴 **~24 hình còn thiếu** (`report_missing_figures_plan.md`): 10 sơ đồ TikZ/vẽ tay, 4 plot dữ liệu, 5 screenshot, 2 hình redo (arch/fsm quá nhỏ).
- 🔴 **Chương "Nghiên cứu liên quan"** còn trống (state-of-the-art fall detection/HAR).
- 🟡 Phần A (mục trên) — mô tả D-021/D-022 + NFR độ tin cậy cảnh báo.
- 🟡 `erd.png` regen (TODO 2026-06-29 trong db_schema.md).

### Test / DevOps
- 🟡 Chạy & report `ota_test_checklist.md`, `firmware_upload_test_checklist.md`.
- 🟡 **Verification data collection** — thu 5-6 người để có số liệu thực (RQ3) cho §5.7.
- 🟡 Test cho 2 feature mới: firmware Unity (FSM/SVM với synthetic trace) + pytest config-sync (PUT→config/set, echo→DB).
- ⚪ Verify Render prod (Postgres/Influx/MQTT bridge) nếu deploy thật.

---

## PHẦN C — Polish trước chốt sổ
- Docs kiến trúc: **đã đồng bộ** D-021/D-022 (phiên trước). Còn `erd.png`/`fsm.png` cần render.
- Đảm bảo số liệu model chỉ sống ở **§4.3/bảng kết quả** (single source), nơi khác `\ref`. Sửa "cooldown 10-20s"→15s (A4).
- Rà các note "stale/drift" trong architecture docs (vd CLAUDE_firmware.md topic cũ `v1/devices/...`).
- Chốt ranh giới "đồ án done" vs "future work": đề xuất đẩy toàn bộ ⚪ (security, sleep, v32, ERROR state, CMUX) xuống Ch6 hướng phát triển.

## Ưu tiên đề xuất (thứ tự làm trước khi chốt)
1. 🔴 Migration `rssi_interval` (chờ cửa kia) + `alembic upgrade head`; build FW (user) + test nhanh D-021/D-022.
2. 🔴 REPORT: Chương "Nghiên cứu liên quan" + 24 hình (ưu tiên TikZ A1–A3, confusion matrix B1, screenshot C) — đây là khối lớn nhất.
3. 🟡 Phần A (chèn mô tả D-021/D-022 + NFR) — văn bản, làm nhanh sau khi có hình.
4. 🟡 `verify_pipeline.py` + verification data → số liệu §5.7.
5. 🟡 Test (Unity + pytest) nếu còn thời gian.

## Verification
- REPORT build sạch: `pdflatex -interaction=nonstopmode -halt-on-error 20225198_VuManhHung.tex` (×2 cho glossary/ref), EXIT=0; rasterize trang chèn mới để mắt thường kiểm hình.
- Backend: `alembic upgrade head` OK (Supabase cloud — không cần start Postgres local); `npx tsc --noEmit` FE sạch.
- Đối chiếu mô tả report ↔ `architecture/*` (đã là canonical) để không lệch.
