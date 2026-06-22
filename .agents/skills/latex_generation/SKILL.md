---
name: latex_generation
description: Sinh nội dung LaTeX và chèn vào đúng mục (section) trong luận văn. Kích hoạt khi người dùng yêu cầu "Hãy viết cho tôi mục [Tên mục] dựa trên các ý sau".
---

# Kỹ năng: Sinh Nội Dung Section LaTeX

**Các bước thực thi của Agent:**
1. **Tìm file:** Liệt kê các file trong thư mục `Chuong` để xác định đúng tên file `.tex` cần thao tác.
2. **Đọc Template (Bắt buộc):** Đọc nội dung file `.tex` đó nằm trong thư mục `SOICT_DATN_Application_VIE_Template/Chuong` để xem hướng dẫn, nội dung mẫu và yêu cầu của giảng viên cho phần đó.
3. **Đọc File Làm Việc:** Đọc file `.tex` tương ứng nằm trong thư mục `Đồ_án_tốt_nghiệp___Vũ_Mạnh_Hưng/Chuong` để xem bối cảnh hiện tại.
4. **Sinh văn bản:** Phân tích dữ liệu thô được cung cấp, kết hợp với hướng dẫn từ Template, sinh ra đoạn văn bản học thuật Tiếng Việt. Tuân thủ tuyệt đối `rules.md`.
5. **Sửa file:** Dùng công cụ sửa file để chèn phần văn bản đã sinh vào đúng vị trí bên trong file `.tex` ở thư mục `Đồ_án_tốt_nghiệp___Vũ_Mạnh_Hưng/Chuong`.
5. **Báo cáo:** Trình bày tóm tắt cho người dùng những thay đổi đã thực hiện và nhắc người dùng dùng `ols` để đồng bộ lên Overleaf kiểm tra.
