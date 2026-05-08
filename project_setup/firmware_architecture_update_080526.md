# TÓM TẮT DỰ ÁN HAR & FALL DETECTION VỚI ESP32-S3

**1. Lựa chọn kiến trúc mô hình:**
- Ưu tiên sử dụng mạng **GRU** (hoặc cấu trúc lai 1D-CNN + GRU) thay vì LSTM.
- **Lý do:** Dữ liệu IMU 6 trục không đòi hỏi bộ nhớ tách biệt phức tạp như ngôn ngữ tự nhiên. GRU có cấu trúc rút gọn (chỉ 2 cổng) giúp giảm ~25% tham số và phép toán. Điều này tối ưu tốc độ suy luận và tiết kiệm đáng kể vùng nhớ cấp phát tĩnh (Tensor Arena) trong SRAM nội của ESP32-S3.

**2. Kích thước cửa sổ dữ liệu (Window Size):**
- Tần số lấy mẫu: $f_s = 100$ Hz (1 giây = 100 samples).
- Chuyển hướng từ 200 samples lên cân nhắc giữa **300 samples (3 giây)** hoặc **400 samples (4 giây)**. 
- **Mục đích:** Nới rộng "tầm nhìn" của mô hình để bao trọn vẹn sự biến thiên gia tốc của các pha ngã chậm phức tạp hoặc trôi dạt tư thế (chuỗi hành động: Đứng -> Ngồi -> Nằm), tránh tình trạng bị điểm mù khiến mô hình phân loại sai.

**3. Phương án lập trình firmware (Chốt hạ):**
- Chắc chắn sử dụng **Queue (Hàng đợi / Buffer vòng)** để nạp dữ liệu cảm biến vào quy trình suy luận.
- Kết hợp với kỹ thuật **Cửa sổ trượt (Sliding Window)**, phương án này đảm bảo hệ thống có thể liên tục cập nhật và dự đoán trạng thái theo thời gian thực (real-time inference) mà không bị đứt gãy mạch ngữ cảnh.