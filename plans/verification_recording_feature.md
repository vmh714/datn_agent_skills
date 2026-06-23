# Plan: Verification Recording Feature (Backend + Frontend)

> **Mục tiêu:** Thêm tính năng thu data verification trực tiếp từ thiết bị đeo, lưu file .txt theo đúng format SisFall để verify model `v30_optimize`.
> **Ràng buộc quan trọng:** Backend chỉ lưu data khi thiết bị **đã assign cho người** (`device.current_wearer_id IS NOT NULL`).
> **Ngày tạo:** 2026-06-23

---

## 1. Tổng quan thiết kế

```
[Frontend verification page]
  → chọn: device (mounted only) + subject SV0X + activity D/F + trial R0X
  → start: gửi POST /verification/sessions → backend trả session_id
  → record: MQTT imu_stream → frontend buffer 100Hz (giống data-collection hiện tại)
  → stop: POST /verification/sessions/{id}/data  (samples[])
  → backend: validate device mounted → lưu .txt (SisFall format) + metadata Postgres
  → frontend: hiển thị session log + nút download .txt / download all zip
```

**Không thay đổi luồng MQTT, không thay đổi firmware.**  
Reuse `AccelChart`, `GyroChart`, IMU buffer mechanism từ `data-collection` page hiện tại.

---

## 2. Backend

### 2.1 Model mới — `verification_sessions` (SQLAlchemy)

File: `app/models/domain.py` — thêm class `VerificationSession`

```python
class VerificationSession(Base, TimestampMixin):
    __tablename__ = "verification_sessions"

    id            = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    device_id     = Column(String, ForeignKey("devices.device_id"), nullable=False)
    wearer_id     = Column(UUID(as_uuid=True), ForeignKey("wearers.id"), nullable=True)  # snapshot lúc thu
    subject_code  = Column(String(4), nullable=False)   # SV01–SV06
    activity_code = Column(String(3), nullable=False)   # D01, F06, ...
    trial_no      = Column(String(3), nullable=False)   # R01–R05
    sample_count  = Column(Integer, nullable=True)
    duration_s    = Column(Float, nullable=True)
    file_path     = Column(String, nullable=True)        # relative path đến .txt
    org_id        = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
```

### 2.2 Schema Pydantic

File: `app/schemas/verification.py` (file mới)

```python
class VerificationSessionCreate(BaseModel):
    device_id:     str
    subject_code:  str   # "SV01"
    activity_code: str   # "D01"
    trial_no:      str   # "R01"

class VerificationSessionData(BaseModel):
    session_id: UUID
    samples: list[list[float]]  # [[ax,ay,az,gx,gy,gz], ...] đơn vị g / deg/s

class VerificationSessionResponse(BaseModel):
    id:            UUID
    device_id:     str
    subject_code:  str
    activity_code: str
    trial_no:      str
    sample_count:  int | None
    duration_s:    float | None
    file_path:     str | None
    created_at:    datetime

    model_config = ConfigDict(from_attributes=True)
```

### 2.3 Endpoints mới

File: `app/api/api_v1/endpoints/verification.py` (file mới)

```
POST   /api/v1/verification/sessions
       → tạo session record (chưa có data)
       → validate: device.current_wearer_id IS NOT NULL (raise 400 nếu chưa mount)
       → trả về session_id

POST   /api/v1/verification/sessions/{session_id}/data
       → nhận samples[]
       → lưu file .txt SisFall format
       → cập nhật session (sample_count, duration_s, file_path)

GET    /api/v1/verification/sessions
       → list tất cả sessions của org (có filter theo subject_code, activity_code)

GET    /api/v1/verification/sessions/{session_id}/download
       → trả về file .txt (FileResponse)

GET    /api/v1/verification/export
       → zip toàn bộ .txt của org → StreamingResponse
```

#### Logic validate "mounted":

```python
# Trong POST /sessions
device = await db.get(Device, device_id)
if not device or device.current_wearer_id is None:
    raise HTTPException(
        status_code=400,
        detail="Device chưa được gán cho người dùng. Assign device trước khi thu data."
    )
if device.org_id != current_user.org_id:
    raise HTTPException(status_code=403, detail="Forbidden")
```

#### Format file .txt lưu ra:

```python
# verification_dataset/<subject_code>/<activity_code>_<subject_code>_<trial_no>.txt
# Mỗi dòng: ax,ay,az,gx,gy,gz  (float, 6 decimal places)
# Đơn vị: g và deg/s (đã scale, khớp input của apply_preprocessing)

import os, csv
from pathlib import Path

BASE_DIR = Path("verification_dataset")

def save_sisfall_txt(subject_code, activity_code, trial_no, samples) -> str:
    folder = BASE_DIR / subject_code
    folder.mkdir(parents=True, exist_ok=True)
    filename = f"{activity_code}_{subject_code}_{trial_no}.txt"
    path = folder / filename
    with open(path, "w") as f:
        for row in samples:
            f.write(",".join(f"{v:.6f}" for v in row) + "\n")
    return str(path)
```

#### Scale samples trước khi lưu (nếu frontend gửi raw int16):

Frontend hiện tại đã parse và scale trong `imu-parser.ts`:
- `accel_g = raw / 4096` (±8g)
- `gyro_dps = raw / 16.4` (±2000dps)

→ Backend nhận `samples` đã ở đơn vị g/deg/s → lưu thẳng, không scale lại.  
→ Pipeline verify: `apply_preprocessing` trong `ml_pipeline.py` sẽ clip(-8,8)/8 và /2000 khi load.

### 2.4 Alembic migration

```python
# alembic/versions/<hash>_add_verification_sessions.py
def upgrade():
    op.create_table(
        "verification_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("device_id", sa.String(), sa.ForeignKey("devices.device_id"), nullable=False),
        sa.Column("wearer_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("wearers.id"), nullable=True),
        sa.Column("subject_code", sa.String(4), nullable=False),
        sa.Column("activity_code", sa.String(3), nullable=False),
        sa.Column("trial_no", sa.String(3), nullable=False),
        sa.Column("sample_count", sa.Integer(), nullable=True),
        sa.Column("duration_s", sa.Float(), nullable=True),
        sa.Column("file_path", sa.String(), nullable=True),
        sa.Column("org_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), onupdate=sa.func.now()),
    )
    op.create_index("ix_verification_sessions_org_id", "verification_sessions", ["org_id"])
    op.create_index("ix_verification_sessions_device_id", "verification_sessions", ["device_id"])
```

### 2.5 Cập nhật router

File: `app/api/api_v1/api.py` — thêm:
```python
from .endpoints import verification
router.include_router(verification.router, prefix="/verification", tags=["verification"])
```

---

## 3. Frontend

### 3.1 Page mới: `app/verification/page.tsx`

Layout gồm 2 panel:

**Panel trái — Session Setup:**
```
[Device selector]     ← chỉ hiện device có current_wearer_id (mounted)
[Subject]             ← SV01 / SV02 / ... / SV06  (Select hoặc Input)
[Activity]            ← dropdown nhóm ADL / Falls
[Trial]               ← R01..R05 (auto-increment từ session log)
[Duration estimate]   ← hiển thị theo activity (60s / 20s / 15s...)

[▶ Start Recording]   ← disabled nếu device chưa mount
[■ Stop Recording]
```

**Panel phải — Live Preview:**
```
[AccelChart]    ← reuse từ data-collection (ax/ay/az/SVM)
[GyroChart]     ← reuse từ data-collection (gx/gy/gz)
[Sample count]  ← đếm realtime
```

**Panel dưới — Session Log (bảng):**
```
| Subject | Activity | Trial | Samples | Duration | Status | Download |
|---------|----------|-------|---------|----------|--------|----------|
| SV01    | D01      | R01   | 6000    | 60.0s    | ✓      | [↓]      |
```

### 3.2 Activity dropdown — nhóm theo loại

```typescript
const ACTIVITY_OPTIONS = {
  "ADL — Walk": ["D01", "D02", "D05"],
  "ADL — Run":  ["D03"],
  "ADL — Trans/Idle": ["D07", "D12", "D15", "D00"],
  "Falls — Đứng/Đi":  ["F01", "F02", "F03", "F06"],
  "Falls — Đứng dậy": ["F08", "F09"],
  "Falls — Ngồi xuống": ["F10", "F11"],
  "Falls — Đang ngồi":  ["F13", "F15"],
}

// Nhãn model mapping (hiển thị để người thu biết)
const LABEL_MAP: Record<string, string> = {
  D00:"Idle", D01:"Walk", D02:"Walk", D03:"Run", D05:"Walk",
  D07:"Trans+Idle", D12:"Trans+Idle", D15:"Trans",
  F01:"Fall", F02:"Fall", F03:"Fall", F06:"Fall",
  F08:"Fall", F09:"Fall", F10:"Fall", F11:"Fall",
  F13:"Fall", F15:"Fall",
}

// Duration gợi ý (giây) — hiển thị countdown
const DURATION_HINT: Record<string, number> = {
  D00:30, D01:60, D02:60, D03:60, D05:20,
  D07:12, D12:15, D15:12,
  F01:15, F02:15, F03:15, F06:15, F08:15, F09:15,
  F10:15, F11:15, F13:15, F15:15,
}
```

### 3.3 Auto-increment trial_no

```typescript
// Tự tính trial tiếp theo từ session log
function nextTrialNo(sessions: VerificationSession[], subject: string, activity: string): string {
  const count = sessions.filter(
    s => s.subject_code === subject && s.activity_code === activity
  ).length
  return `R${String(count + 1).padStart(2, "0")}`
}
```

### 3.4 Recording flow

```typescript
// 1. User click Start → POST /verification/sessions → nhận session_id
// 2. Subscribe MQTT imu_stream (đã có từ useMqtt hook)
// 3. Buffer 100Hz vào useRef (reuse pattern từ data-collection)
// 4. Countdown timer theo DURATION_HINT (không bắt buộc stop lúc hết, chỉ gợi ý)
// 5. User click Stop → POST /verification/sessions/{id}/data ({samples})
// 6. Refetch session log
```

### 3.5 Hooks mới

File: `hooks/useVerification.ts`

```typescript
export function useVerificationSessions(filters?: {subject?: string, activity?: string}) {
  return useQuery({
    queryKey: ["verification-sessions", filters],
    queryFn: () => api.getVerificationSessions(filters),
    staleTime: 10_000,
  })
}

export function useCreateVerificationSession() {
  return useMutation({
    mutationFn: api.createVerificationSession,
  })
}

export function useSubmitVerificationData() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: api.submitVerificationData,
    onSuccess: () => qc.invalidateQueries({queryKey: ["verification-sessions"]}),
  })
}
```

### 3.6 API calls mới (`services/api.ts`)

```typescript
api.getVerificationSessions(filters?)        // GET /verification/sessions
api.createVerificationSession(body)          // POST /verification/sessions
api.submitVerificationData(id, samples)      // POST /verification/sessions/{id}/data
api.downloadVerificationFile(id)             // GET /verification/sessions/{id}/download
api.exportAllVerification()                  // GET /verification/export (zip)
```

### 3.7 Types mới (`types/index.d.ts`)

```typescript
interface VerificationSession {
  id:            string
  device_id:     string
  subject_code:  string   // "SV01"
  activity_code: string   // "D01"
  trial_no:      string   // "R01"
  sample_count:  number | null
  duration_s:    number | null
  file_path:     string | null
  created_at:    string
}
```

### 3.8 Sidebar navigation

File: `components/layout/Sidebar.tsx` — thêm link:
```
[📋 Thu Data Verify]  → /verification
```

---

## 4. Thứ tự implement

### Backend (làm trước)
- [ ] `app/schemas/verification.py` — Pydantic schemas
- [ ] `app/models/domain.py` — thêm `VerificationSession` model
- [ ] Migration Alembic — `add_verification_sessions`
- [ ] `app/api/api_v1/endpoints/verification.py` — 5 endpoints
- [ ] `app/api/api_v1/api.py` — đăng ký router
- [ ] Test: POST session với device chưa mount → 400; device đã mount → 200

### Frontend (làm sau khi backend xong)
- [ ] `types/index.d.ts` — thêm `VerificationSession`
- [ ] `services/api.ts` — thêm 5 api calls
- [ ] `hooks/useVerification.ts` — 3 hooks
- [ ] `app/verification/page.tsx` — page chính
- [ ] `components/layout/Sidebar.tsx` — thêm nav link

---

## 5. Edge cases cần xử lý

| Case | Xử lý |
|------|-------|
| Device bị unassign trong lúc đang record | Frontend: session_id đã tạo, POST data vẫn thành công (validate chỉ lúc tạo session) |
| File đã tồn tại (cùng subject+activity+trial) | Backend overwrite + log warning |
| Samples = [] (stop ngay lập tức) | Backend: lưu file rỗng + sample_count=0, FE show warning |
| Nhiều người dùng thu cùng lúc | org_id isolation, không conflict |
| Disk storage | Mỗi file 15s × 100Hz × 6 col × 7bytes ≈ 63KB. 6 người × 18 activities × 5 trials = 540 files ≈ 34MB — nhỏ |

---

## 6. Ghi chú verify pipeline

Sau khi thu xong, trên server chạy:

```python
# verify_pipeline.py (SisFall-PreProcessing/)
# Load file từ verification_dataset/ → apply_preprocessing → extract_windows
# → tflite inference → confusion matrix
# Xem plan verification_data_collection.md §7 để biết chi tiết script
```

Mapping nhãn khi evaluate:
```
Walk  ← D01, D02, D05
Run   ← D03
Idle  ← D00 + đoạn tĩnh D07/D12
Trans ← đoạn peak D07, D12, D15
Fall  ← F01, F02, F03, F06, F08, F09, F10, F11, F13, F15
```
