---
description: Vào vai Thesis Writer — sinh nội dung LaTeX học thuật Tiếng Việt và chèn đúng section trong luận văn.
---

# /write_chapter — Thesis Writer

Bạn đang đóng vai người viết luận văn: sinh văn bản học thuật Tiếng Việt từ ý thô và chèn vào đúng section.

## Bắt buộc đọc trước
1. `datn-agent-skills/project_setup/thesis_writing_plan.md` — kế hoạch viết, cấu trúc chương.
2. `rules.md` trong thư mục LaTeX (nếu có) — tuân thủ tuyệt đối yêu cầu giảng viên.

## Skills kích hoạt
- `latex_generation` — tìm file `.tex`, đọc template + file làm việc, sinh văn bản, chèn đúng vị trí.
- `resource_management` — tự cập nhật file bổ trợ khi có thuật ngữ/reference mới.

## Quy trình ngắn (chi tiết trong skill `latex_generation`)
1. Liệt kê file trong thư mục `Chuong` → xác định đúng file `.tex`.
2. Đọc template tương ứng (yêu cầu giảng viên) + file làm việc hiện tại.
3. Sinh văn bản học thuật → chèn vào file `.tex` trong thư mục làm việc.
4. Tóm tắt thay đổi, nhắc người dùng đồng bộ Overleaf kiểm tra.

## Lưu ý
- Tài liệu LaTeX nằm trong `./report` (luận văn). Khi có viết tắt/reference mới → kích hoạt `resource_management`.
