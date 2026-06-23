# Session Report — Thu Data Verify dán nhãn chuẩn SisFall · 2026-06-23

> Đóng gói phiên: kiểm tra implement 2 plan (`plans/verification_data_collection.md`, `plans/verification_recording_feature.md`) → viết test → **gộp 2 trang FE thành 1** → bỏ chế độ train→InfluxDB → đổi tên route/API cho nhất quán.
> Layout máy này: backend `backend/HAR_and_Fall-detection-backend/`, frontend `frontend/Fall-Detection-dashboard/`. Path dưới tương đối gốc repo tương ứng.
> Trạng thái cuối: **BE pytest verify 18/18 · FE tsc 0 lỗi (trừ 1 lỗi vitals pre-existing) · vitest 90/90**. (4 test alerts/timeline fail là **pre-existing**, không liên quan phiên này.)

---

## 0. Mục tiêu

Thu bộ data thực (đeo thiết bị thật) **đã dán nhãn theo đúng format SisFall** để **đánh giá (verify)** model fall-detection `v30_optimize` đã train trên SisFall — **KHÔNG train lại trên web**. Data thô xuất ra `.txt`, tải về máy để chạy eval offline.

---

## 1. Quy ước dán nhãn SisFall (cốt lõi)

### Đặt tên file (giữ nguyên convention SisFall)
```
<ACTIVITY_CODE>_<SUBJECT_CODE>_<TRIAL_NO>.txt
ví dụ: D01_SV01_R01.txt , F06_SV03_R04.txt
lưu tại: verification_dataset/<SUBJECT_CODE>/<file>.txt
```
- **SUBJECT_CODE** = `SV01..SVnn` (prefix `SV` = Subject Verification, không đụng `SA`/`SE` của SisFall gốc). Đặt trên **frontend** theo từng người đeo (xem §3).
- **ACTIVITY_CODE** = mã hoạt động SisFall (`D01`, `F06`, …).
- **TRIAL_NO** = `R01..R0n`, tự tăng theo (subject + activity) đã có trong log.

### Định dạng nội dung file
- Mỗi dòng = 1 mẫu, 6 cột `ax,ay,az,gx,gy,gz`, float `%.6f`, phân tách dấu phẩy.
- **Đơn vị đã scale** (khớp input `apply_preprocessing` của pipeline SisFall): accel = **g**, gyro = **deg/s**. FE scale sẵn (`ax/4096`, `gx/16.4`) trước khi gửi; backend lưu thẳng, không scale lại.
- 100 Hz → `duration_s = sample_count / 100`.

### Bản đồ nhãn hoạt động → nhãn model (hiển thị trên UI)
| Activity code | Nhãn model |
|---|---|
| D01, D02, D05 | Walk |
| D03 | Run |
| D00 | Idle |
| D07, D12 | Trans + Idle |
| D15 | Trans |
| F01, F02, F03, F06, F08, F09, F10, F11, F13, F15 | Fall |

> Nguồn mapping: `ml_pipeline.py:22-29` + `step2_windowing.py:66-68` (D05 = Walk vì xếp `cont_har`, sliding window liên tục).

---

## 2. Backend — API `data-collection` (lưu raw .txt + metadata)

- **Bảng mới** `verification_sessions` ([models/domain.py](../../backend/HAR_and_Fall-detection-backend/app/models/domain.py)): `id, device_id FK, wearer_id FK(nullable, snapshot), subject_code(str4), activity_code(str3), trial_no(str3), sample_count, duration_s, file_path(str500), org_id FK` + idx `org_id`, `device_id`. Migration `a8f3c2d1e9b5`.
- **Schemas** ([schemas/verification.py](../../backend/HAR_and_Fall-detection-backend/app/schemas/verification.py)): `VerificationSessionCreate / VerificationSessionData / VerificationSessionResponse`.
- **Router** ([endpoints/verification.py](../../backend/HAR_and_Fall-detection-backend/app/api/api_v1/endpoints/verification.py)) — **prefix + Swagger tag = `data-collection`** (xem §6). Endpoints:
  | Method | Path | Việc |
  |---|---|---|
  | POST | `/api/v1/data-collection/sessions` | Tạo session. Validate device **thuộc org** (404) + **đã mount wearer** (`current_wearer_id IS NOT NULL` → 400). Snapshot `wearer_id`. |
  | POST | `/api/v1/data-collection/sessions/{id}/data` | Nhận `samples[]`, ghi `.txt` SisFall ra đĩa, cập nhật `sample_count/duration_s/file_path`. Samples rỗng → không tạo file. |
  | GET | `/api/v1/data-collection/sessions` | List của org (filter `subject_code`/`activity_code`), mới nhất trước. |
  | GET | `/api/v1/data-collection/sessions/{id}/download` | Tải 1 file `.txt` (FileResponse). |
  | GET | `/api/v1/data-collection/export` | ZIP toàn bộ `.txt` của org (StreamingResponse, arcname `SV/ACT_SV_R.txt`). |
- **Cô lập đa tổ chức**: mọi truy vấn lọc `org_id` từ JWT; device/session khác org → 404 (không lộ 400).

---

## 3. Frontend — 1 trang gộp `Data Collector` (`/data-collection`)

- **Route + nav giữ tên cũ** `data-collection` / "Data Collector" (icon Activity). File [app/data-collection/page.tsx](../../frontend/Fall-Detection-dashboard/app/data-collection/page.tsx) (component `DataCollectionPage`).
- **Luồng 2 bước** (giữ tính năng "ngon" của data-collection cũ — xem preview trước khi ghi):
  1. **Kết nối** → `start_stream` (qua backend) → xem `AccelChart`/`GyroChart` realtime, *chưa ghi*.
  2. Khi tín hiệu ổn định → **Bắt đầu ghi** → `POST /sessions` (tạo) + buffer 100Hz vào `useRef`.
  3. **Kết thúc ghi** → `POST /sessions/{id}/data` (submit raw), **vẫn giữ stream** để thu trial kế tiếp.
  4. **Ngắt kết nối** → `stop_stream`.
- **Chọn người đeo thật + đặt SV trên FE**: dropdown liệt kê **device đã mount** (hiện `full_name` người đeo). Ô "Mã subject (SisFall)" tự gợi ý `SV01/SV02/…`, **nhớ theo từng người trong `localStorage`** (`verification_subject_map` keyed by `wearerId`) — bỏ hardcode 6 người.
- **Activity dropdown**: nhóm theo loại (ADL/Falls), mỗi option có badge nhãn model. **Trial** tự tăng từ log. Bảng "Lịch sử phiên thu": download từng file + "Xuất ZIP tất cả".
- Hooks [useVerification.ts](../../frontend/Fall-Detection-dashboard/hooks/useVerification.ts), API trong [services/api.ts](../../frontend/Fall-Detection-dashboard/services/api.ts) (5 hàm).

---

## 4. Đã GỠ — chế độ train → InfluxDB (`imu_windowed`)

Quyết định: **chỉ verify + tải data gốc về máy tự train**, bỏ luồng windowing/augment ghi InfluxDB.
- **Backend xoá**: `endpoints/data_collection.py`, `schemas/data_collection.py`, đăng ký router trong `api.py`; gỡ `numpy`/`scipy` khỏi `requirements.txt`. Gỡ 4 test data_collection (2 ở `test_crud_api.py`, 2 ở `test_security_byid_routes.py`).
- **Frontend xoá**: trang train cũ `app/data-collection/page.tsx` (bản cũ), components `ControlPanel.tsx`/`DeviceSelector.tsx`, `useSaveRecording`, `api.saveRecordingSession`, type `RecordingSession`/`ActivityLabel`, util `exportToCSV`/`downloadCSV`.
- **InfluxDB còn lại**: chỉ measurement `telemetry` (mqtt_service ghi mỗi gói status; đọc bởi `/history/steps` + `/history/{id}/telemetry`). `imu_windowed` ngừng ghi; data cũ trong bucket cần `influx delete` thủ công nếu muốn dọn.

---

## 5. Test viết mới

[tests/test_verification_api.py](../../backend/HAR_and_Fall-detection-backend/tests/test_verification_api.py) — **18 test, pass hết** (harness SQLite in-memory + JWT thật, ghi `.txt` vào tmp qua monkeypatch `VERIFICATION_DATASET_DIR`):
- Tạo session: mounted→201, chưa mount→400, khác org→404, device lạ→404, no-auth→401, snapshot `wearer_id/org_id`.
- Submit: lưu file đúng tên + format `%.6f`, `sample_count/duration_s` (n/100Hz), rỗng→không file, session lạ/khác org→404.
- List (scope org + filter), download (ok/chưa file→404/khác org→404), export ZIP (arcname đúng, không lẫn org khác).
- Sửa [conftest.py](../../backend/HAR_and_Fall-detection-backend/tests/conftest.py): thêm `verification_sessions` vào danh sách dọn giữa test (SQLite không enforce FK → rows rò rỉ).

---

## 6. Đổi tên prefix/Swagger: `verification` → `data-collection`

- `api.py`: `prefix="/data-collection", tags=["data-collection"]` (tên `data-collection` trống vì endpoint train cũ đã xoá).
- FE `services/api.ts` + `tests/test_verification_api.py`: path đổi sang `/api/v1/data-collection/*`.
- **Giữ tên nội bộ**: file `verification.py`, class `VerificationSession*`, bảng `verification_sessions` (không hiện ở Swagger, đổi sẽ kéo theo rename bảng + migration — không cần).
- ⚠️ **Phải restart uvicorn** thì Swagger mới cập nhật (OpenAPI build lúc app khởi động).

---

## 7. File tạo / xoá

**Tạo:** `tests/test_verification_api.py`; `app/data-collection/page.tsx` (bản gộp); `session_report_2026-06-23_sisfall_data_collection.md` (file này).
**Xoá:** BE `endpoints/data_collection.py`, `schemas/data_collection.py`; FE `app/data-collection/page.tsx` (bản train cũ), `components/features/data-collection/{ControlPanel,DeviceSelector}.tsx`, `app/verification/` (route trung gian).
**(Lưu ý:** model/migration/endpoint `verification*` đã có từ phiên trước; phiên này kiểm tra + viết test + gộp UI + rename.)

## 8. Doc đã đồng bộ
`architecture/`: `backend.md` (bảng + migration + endpoints + InfluxDB), `frontend.md` (page gộp + hooks + luồng), `db_schema.md` (bảng `verification_sessions` + Mermaid ERD + migrations 10 file), `DECISIONS.md` (**D-017**).

---

## 9. Còn lại (không chặn phiên này)

- **`verify_pipeline.py`** (eval) CÒN NỢ — plan §7 `verification_data_collection.md`: load `.txt` → `apply_preprocessing` (clip/8, /2000) → window 200/stride 100 → infer tflite v30 → confusion matrix. `fall_threshold = 0.25` (ngưỡng eval, KHÔNG dùng 0.6 runtime). **Đây là phần lõi còn thiếu để ra kết quả.**
- **Lưu trữ `.txt`**: hiện ghi đĩa server. Render đĩa ephemeral → mất khi redeploy. Mitigation rẻ: thu xong **export ZIP tải về ngay**, hoặc chạy backend **local** lúc thu. Future work: object storage (**Supabase Storage** ưu tiên vì DB đã ở Supabase; hoặc S3/R2/MinIO).
- **Vẽ lại `REPORT/.../Hinhve/erd.png`** từ Mermaid mới (đã thêm `verification_sessions`).
- Migration chain có 10 file (>5 như doc cũ) — chạy `alembic heads` kiểm tra multi-head trước khi deploy lại.
