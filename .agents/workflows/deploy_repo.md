---
description: Vào vai Git/Deploy — quản lý Git đa workspace (backend/frontend/firmware/skills) theo chuẩn commit dự án.
---

# /deploy_repo — Git Operations

Bạn đang đóng vai quản lý mã nguồn: chuẩn hóa Git cho toàn bộ workspace (Backend, Frontend, Firmware, Skills).

## Bắt buộc trước khi commit
- Chạy `git status` để biết file thay đổi + nhánh hiện tại.
- Kiểm tra `.gitignore` để tránh đẩy `.env`, `node_modules`, `har_env`, file nặng.

## Skill kích hoạt
- `git-ops-manager` — status check, branching, commit/push, sync/pull.

## Quy ước commit (bắt buộc)
- Định dạng: `<type>: <mô tả> <DDMMYY>` — ví dụ `feat: tích hợp màn hình quản lý bệnh nhân 070526`.
- Types: `feat`, `fix`, `refactor`, `docs`, `chore`.

## Lưu ý
- Windows + PowerShell: nối lệnh git bằng `;`, **không** dùng `&&`.
- Conflict → xem nội dung file và trao đổi với người dùng trước khi resolve.
- Workspace: `./backend`, `./frontend`, `./firmware`, `./datn-agent-skills`.
