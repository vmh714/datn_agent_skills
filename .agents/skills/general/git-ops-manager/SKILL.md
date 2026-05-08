---
name: git-ops-manager
description: Quản lý các thao tác Git (Push, Pull, Branch, Commit) theo chuẩn dự án, hỗ trợ đa workspace và tự động hóa thông điệp commit kèm ngày tháng.
---

# Git Operations Manager (Skill)

Skill này giúp chuẩn hóa quy trình quản lý mã nguồn bằng Git cho toàn bộ các thành phần của hệ thống (Frontend, Backend, Firmware).

## 🛠 Khi nào sử dụng

- Khi cần đẩy code (Push) hoặc cập nhật code (Pull) cho bất kỳ workspace nào.
- Khi cần tạo nhánh mới (Branching) cho các tính năng hoặc cá nhân.
- Khi cần commit code với định dạng thông điệp (commit message) chuẩn của dự án.
- Khi cần kiểm tra trạng thái git trên nhiều thư mục khác nhau.

## 📋 Quy trình thực hiện (Hành động)

### 1. Kiểm tra trạng thái (Status Check)
Trước khi làm bất cứ việc gì, luôn phải kiểm tra trạng thái hiện tại:
- Lệnh: `git status`
- Mục tiêu: Xác định các file thay đổi, các file chưa track và nhánh hiện tại.

### 2. Quản lý Nhánh (Branching)
- **Tạo nhánh mới:** `git checkout -b <tên_nhánh>`
- **Chuyển nhánh:** `git checkout <tên_nhánh>`
- **Xóa nhánh:** `git branch -d <tên_nhánh>`

### 3. Quy trình Commit & Push (Standard Workflow)
Luôn tuân thủ định dạng thông điệp commit:
- **Định dạng:** `<type>: <description> <DDMMYY>`
- **Types:** `feat` (tính năng mới), `fix` (sửa lỗi), `refactor` (tối ưu code), `docs` (tài liệu), `chore` (cấu hình/build).
- **Ví dụ:** `feat: tích hợp màn hình quản lý bệnh nhân 070526`

**Các bước thực hiện:**
1. `git add .` (hoặc add cụ thể file).
2. `git commit -m "<thông_điệp_chuẩn>"`
3. `git push origin <tên_nhánh>`

### 4. Đồng bộ mã nguồn (Sync/Pull)
- `git pull origin <tên_nhánh>`
- Luôn ưu tiên xử lý Conflict (nếu có) bằng cách xem nội dung file và trao đổi với người dùng.

## 📂 Các Workspace hỗ trợ

- **Backend:** `d:\datn\backend`
- **Frontend:** `d:\datn\frontend`
- **Firmware:** `d:\datn\firmware`
- **Skills:** `d:\datn\datn_agent_skills`

## ⚠️ Lưu ý quan trọng

- Luôn kiểm tra `.gitignore` trước khi commit để tránh đẩy các file nhạy cảm như `.env` hoặc thư mục nặng như `node_modules`, `har_env`.
- Trên Windows (PowerShell), sử dụng `;` thay vì `&&` để kết hợp các lệnh git.
- Nếu gặp lỗi quyền truy cập hoặc SSH, hãy báo ngay cho người dùng để họ xác thực trên máy.
