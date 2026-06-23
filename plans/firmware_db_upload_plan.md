# Plan: Firmware Storage + Upload Endpoint (DB-backed OTA)

> **Ngày tạo:** 2026-06-23  
> **Trạng thái:** ✅ Đã implement xong  
> **Liên quan:** `datn-agent-skills/plans/ota_test_checklist.md`, `datn-agent-skills/plans/firmware_upload_test_checklist.md`

## Context

Thay thế mock data hardcode trong `firmware.py` bằng:
- Bảng DB `firmware_releases` lưu metadata từng version
- Endpoint upload `.bin` (ADMIN only) qua Swagger hoặc UI
- `download_url` dynamic theo `request.base_url` (quan trọng cho 4G/ngrok)
- Frontend hiển thị nút upload chỉ khi user là ADMIN

User model đã có `role: UserRole` (ADMIN | MANAGER). Đã thêm `get_admin_user` dependency và endpoint `/me` để frontend biết role.

---

## Backend (6 files đã thay đổi)

### 1. Alembic migration — tạo bảng `firmware_releases`
File: `alembic/versions/b2e9f4a1c3d7_add_firmware_releases.py`

```python
op.create_table('firmware_releases',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('version', sa.String(20), nullable=False, unique=True),
    sa.Column('release_date', sa.Date(), nullable=False),
    sa.Column('changelog', sa.Text(), nullable=False),
    sa.Column('is_stable', sa.Boolean(), server_default='true'),
    sa.Column('is_latest', sa.Boolean(), server_default='false'),
    sa.Column('bin_filename', sa.String(200), nullable=False),
    sa.Column('bin_size', sa.Integer(), nullable=False),
    sa.Column('sha256', sa.String(64), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('version'),
)
```
**Lưu ý:** Chạy `alembic upgrade head` trước khi start backend.

### 2. `app/models/domain.py` — model `FirmwareRelease`
Thêm class `FirmwareRelease` cuối file. Import thêm `Text`, `Date` từ sqlalchemy.

### 3. `app/api/deps.py` — `get_admin_user`
```python
async def get_admin_user(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Yêu cầu quyền ADMIN")
    return current_user
```

### 4. `app/main.py` — mount StaticFiles
```python
os.makedirs("static/firmware", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")
```
Đặt TRƯỚC `include_router` để path không bị conflict.

### 5. `app/api/api_v1/endpoints/firmware.py` — rewrite hoàn toàn

3 endpoints:
- `GET  /api/v1/firmware/versions` — đọc DB, build `download_url` từ `request.base_url`
- `POST /api/v1/firmware/upload` — ADMIN only, multipart, tính SHA256, rotate `is_latest`
- `POST /api/v1/firmware/{device_id}/update` — validate version tồn tại trong DB trước khi publish MQTT

### 6. `app/api/api_v1/endpoints/auth.py` — `GET /me`
```python
@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user)):
    return {"id": str(current_user.id), "username": current_user.username, "role": current_user.role}
```

---

## Frontend (4 files đã thay đổi)

### 1. `lib/apiClient.ts` — `postFormData()`
Không set Content-Type (browser tự gắn multipart/form-data + boundary).

### 2. `services/api.ts`
- Thêm `CurrentUser` interface
- Thêm `api.uploadFirmware()` — gọi `postFormData`
- Thêm `api.getCurrentUser()` — GET `/api/v1/auth/me`
- `FirmwareVersion` bổ sung `bin_size` và `sha256`

### 3. `hooks/useDeviceData.ts`
- `useCurrentUser()` — staleTime 10 phút
- `useUploadFirmware()` — invalidate `['firmware', 'versions']` on success

### 4. `app/settings/page.tsx`
Section upload firmware, chỉ render khi `currentUser?.role === 'ADMIN'`:
- Input file `.bin`, version, ngày phát hành, changelog, is_stable toggle
- Toast success/error sau upload

---

## Thứ tự thực hiện (đã hoàn thành)

1. ✅ Migration + model `FirmwareRelease`
2. ✅ `deps.py` → `get_admin_user`
3. ✅ `main.py` → mount StaticFiles
4. ✅ Rewrite `firmware.py`
5. ✅ `auth.py` → `/me` endpoint
6. ✅ Frontend: apiClient → api.ts → hooks → settings page

---

## Verification

Xem chi tiết trong `datn-agent-skills/plans/firmware_upload_test_checklist.md`.
