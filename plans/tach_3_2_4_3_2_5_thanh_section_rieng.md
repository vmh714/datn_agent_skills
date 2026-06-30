# Plan: Tái cấu trúc §3.2 Ch3 + fall_threshold 0.6→0.25 + Auto-resolve alert 24h

## Context

Ba việc gom trong một plan (A, B chạm cùng §3.2.5 Ch3; D độc lập bên backend):

1. **(B) Tách section Ch3**: §3.2 tên "Chiến Lược Thiết Kế Nhãn" nhưng §3.2.4 (Post-Impact FSM) và §3.2.5 (fall_threshold/cooldown) là cơ chế kiểm soát cảnh báo, **không liên quan thiết kế nhãn** → tách thành section riêng.
2. **(A) Đổi default `fall_threshold` 0.6 → 0.25** (khớp θ dùng lúc train, ưu tiên Fall Recall). Cũng sửa mâu thuẫn: §3.2 ghi θ=0.25 nhưng §3.2.5 đang ghi 0.6. Range [0.15, 0.95] nên 0.25 hợp lệ.
3. **(D) Auto-resolve alert quá 24h**: alert chưa xử lý quá 24h thì tự `is_resolved=true`.

**Lưu ý**: KHÔNG đụng các giá trị 0.6 khác — `svc_ai.c:219` (ratio xác nhận FSM 60%) và `imu_service.c:32` (freefall 0.6G) giữ nguyên.

---

## PHẦN A — Đổi default fall_threshold 0.6 → 0.25

### Firmware (2 vị trí)
- `firmware/components/lib_tinyml/tflite_wrapper.cpp:15` — `static volatile float s_fall_threshold = 0.6f;` → `0.25f`
- `firmware/components/svc_cloud/svc_cloud.c:672` — `uint32_t fall_thr_pct = 60;` → `25` (NVS lưu %; comment `// Default 0.6` → `// Default 0.25`)

### Backend (model + schema)
- `backend/app/models/domain.py:46` — `mapped_column(Float, default=0.6)` → `default=0.25`
- `backend/app/schemas/domain.py:36` — `Field(0.6, ge=0.15, le=0.95, ...)` → `Field(0.25, ...)`

### Backend (migration mới)
`alembic revision -m "lower fall_threshold default to 0.25"` (auto-link down_revision = head):
- **upgrade()**: `op.alter_column('devices','fall_threshold', server_default='0.25')` + `op.execute("UPDATE devices SET fall_threshold = 0.25 WHERE fall_threshold = 0.6")`
- **downgrade()**: đảo lại.
- Giữ nguyên migration cũ `a7b3f9c1d2e4`.

### Frontend (2 vị trí)
- `frontend/services/api.ts:288` — `?? 0.6` → `?? 0.25`
- `frontend/components/features/device-detail/DeviceConfig.tsx:20` — `useState(0.6)` → `useState(0.25)`

---

## PHẦN B — Tái cấu trúc §3.2 Chương 3

File: `report/Do_an_tot_nghiep_Vu_Manh_Hung/Chuong/3_Phuong_phap_de_xuat.tex`

| Trước | Sau |
|---|---|
| §3.2.4 Post-Impact FSM | §3.3 *(mới)* > §3.3.1 |
| §3.2.5 fall_threshold/cooldown | §3.3 *(mới)* > §3.3.2 |
| §3.3 TinyML (line 112) | §3.4 |
| §3.4 PCNT (line 207) | §3.5 |
| §3.5 Pedometer (line 229, `\label{sec:3.5}`) | §3.6 |

Labels `subsec:fall_confirm` + `subsec:fall_config` giữ nguyên tên → `\ref{}` ở Ch4.2 (24, 84) + Ch3 (102) vẫn hợp lệ. Không có ref text cứng "3.2.4"/"3.2.5".

**Edit** (chèn trước line 80): thêm `\section{Chiến Lược Kiểm Soát Độ Tin Cậy và Tần Suất Cảnh Báo Ngã}` + `\label{sec:3.3_alert}` ngay trên `\subsection{Cơ chế xác nhận ngã hai pha...}`.

**Text §3.3.2**: "Giá trị mặc định trên firmware là 0,6" → **"0,25"**, diễn giải lại theo tinh thần "ngưỡng thấp ưu tiên Recall, pha CONFIRMING bù precision".

---

## PHẦN C — Đồng bộ tài liệu

- `3_Phuong_phap_de_xuat.tex` §3.3.2 (Phần B).
- `architecture/DECISIONS.md` D-012: `(float 0.6)` → `0.25` + ghi chú đổi default khớp θ train.
- `architecture/tinyml_model.md`: default fall_threshold → 0.25.
- Kiểm tra `db_schema.md` + `backend.md` — sửa nếu có ghi 0.6.
- Cập nhật `> **Cập nhật lần cuối:**`.

---

## PHẦN D — Auto-resolve alert quá 24h

Backend **không có scheduler** — chỉ 1 background task (MQTT) qua `asyncio.create_task` trong lifespan (`app/main.py:18`). Tận dụng pattern đó, không thêm dependency.
**Chốt**: chỉ lật `is_resolved` (không cột mới, không migration); query `is_resolved=false` + lọc `created_at`; chạy mỗi giờ.

- **Model**: dùng sẵn `is_resolved` (bool) + `created_at` (tz-aware). Không đổi.
- **Config** `app/core/config.py`: thêm `ALERT_AUTO_RESOLVE_HOURS=24`, `ALERT_AUTO_RESOLVE_INTERVAL_SECONDS=3600`.
- **Service mới** `app/services/alert_maintenance.py`: `auto_resolve_stale_alerts_loop()` — vòng `while True`: mở `AsyncSessionLocal`, bulk `update(Alert).where(is_resolved==False, created_at < now-24h).values(is_resolved=True)`, commit, log rowcount, `await asyncio.sleep(interval)` ở cuối (quét ngay lúc start rồi mỗi giờ). Bulk UPDATE idempotent → multi-worker an toàn.
- **Lifespan** `app/main.py`: `resolve_task = asyncio.create_task(...)` cạnh `mqtt_task`; teardown cancel + await nuốt `CancelledError`.
- **Docs**: thêm DECISION mới vào `DECISIONS.md` (vì sao asyncio loop thay scheduler); cập nhật `architecture/backend.md`.

---

## Verification

- **Backend A**: `alembic heads` → `alembic upgrade head`; device mới = 0.25, device cũ (0.6) → 0.25.
- **Backend D**: seed alert `created_at=now-25h, is_resolved=false` → sau tick đầu thành `true`; alert `now-1h` vẫn `false`; start/shutdown không treo task.
- **Firmware**: `idf.py build` không lỗi.
- **Frontend**: `npm run build` / `tsc --noEmit` không lỗi.
- **LaTeX**: `pdflatex 3_Phuong_phap_de_xuat.tex` build sạch; §3.3 "Chiến Lược Kiểm Soát...", §3.4 TinyML, §3.5 PCNT, §3.6 Pedometer; §3.3.2 ghi 0,25.