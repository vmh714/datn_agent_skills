## Quy Tắc Cập Nhật Toạ Độ Slide (PowerPoint)
Nếu người dùng muốn đồng bộ các thao tác kéo thả, tinh chỉnh toạ độ thủ công từ file bản thuyết trình (PPTX) vào lại code (ví dụ `build_slides.py`), hãy thực hiện các bước sau:
1. Yêu cầu người dùng lưu lại (Save) file PPTX sau khi đã kéo thả ưng ý.
2. Sử dụng file script `d:\datn\datn_agent_skills\tools\extract_pptx.py` (cần chạy với Python có cờ `-X utf8` để tránh lỗi font) để đọc và in ra toạ độ `left`, `top`, `width`, `height` mới nhất của toàn bộ các slide.
3. Đối chiếu toạ độ trích xuất được với các hàm `image()`, `bullets()`, `images_row()` tương ứng trong code và tiến hành cập nhật.
Lưu ý: Không viết script cập nhật tự động bằng Regex vì có rủi ro phá hỏng code. Hãy cập nhật file Python một cách an toàn thông qua thao tác thay thế từng cụm.
