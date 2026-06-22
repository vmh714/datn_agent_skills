---
name: resource_management
description: Tự động cập nhật các file bổ trợ khi có thuật ngữ mới hoặc reference mới. Kích hoạt khi dùng từ viết tắt mới hoặc người dùng yêu cầu thêm tài liệu tham khảo.
---

# Kỹ năng: Quản Lý Tài Liệu Tham Khảo và Từ Viết Tắt

**Các bước thực thi của Agent:**

**Đối với Từ Viết Tắt:**
1. Mở file `SOICT_DATN_Application_VIE_Template/Tu_viet_tat.tex`.
2. Kiểm tra xem từ viết tắt đã tồn tại chưa.
3. Nếu chưa, chèn thêm theo định dạng có sẵn trong file (ví dụ: dòng format table).

**Đối với Tài liệu Tham Khảo:**
1. Yêu cầu người dùng cung cấp thông tin bài báo (Link, tên bài báo, tác giả...) HOẶC chuỗi BibTeX.
2. Mở file `SOICT_DATN_Application_VIE_Template/Danh_sach_tai_lieu_tham_khao.bib`.
3. Chèn khối BibTeX vào cuối file. Đảm bảo `Cite Key` ngắn gọn, dễ nhớ (ví dụ: `nguyen2024ai`).
4. Báo cho người dùng biết `Cite Key` để sử dụng `\cite{...}` trong văn bản.
