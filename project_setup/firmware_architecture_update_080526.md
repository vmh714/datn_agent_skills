# TÓM TẮT DỰ ÁN HAR & FALL DETECTION VỚI ESP32-S3

**1. Lựa chọn kiến trúc mô hình (AI Model Architecture):**
- **Kiến trúc Lai (Hybrid):** Kết hợp giữa **1D-CNN** và các biến thể của **RNN (GRU hoặc LSTM)**.
- **Lý do:** Lớp 1D-CNN đóng vai trò như một bộ trích xuất đặc trưng không gian (Spatial Feature Extractor) xuất sắc, giúp nhận diện các mẫu cục bộ đột ngột (ví dụ: khoảnh khắc va chạm mạnh - impact). Dữ liệu sau đó được đẩy qua RNN (GDR/LSTM) để học các chuỗi phụ thuộc thời gian dài hạn (Temporal Dependencies). RNN sẽ phân tích ngữ cảnh trước và sau va chạm (chuỗi hành động: Đứng -> Mất thăng bằng -> Ngã -> Nằm bất động), tránh tình trạng báo động giả do các hoạt động mạnh gây ra.
- *Lưu ý vi điều khiển:* Sự kết hợp này mang lại độ chính xác cực cao nhưng đòi hỏi tối ưu số lượng tham số (Filters và Hidden Units) để vừa vặn với vùng nhớ Tensor Arena (SRAM) của ESP32-S3.

**2. Kích thước cửa sổ dữ liệu (Window Size):**
- Tần số lấy mẫu: $f_s = 100$ Hz (1 giây = 100 samples).
- **Cập nhật:** Tăng kích thước cửa sổ lên mức **400 samples (4 giây)** hoặc **500 samples (5 giây)**.
- **Mục đích:** Kiến trúc mạng lai RNN/LSTM cần "tầm nhìn" quá khứ đủ dài để phát huy sức mạnh bộ nhớ. Việc mở rộng Window Size lên 4-5 giây giúp mô hình bao trọn vẹn sự biến thiên gia tốc của các pha ngã chậm phức tạp (ví dụ ngã trượt từ từ) hoặc trôi dạt tư thế, tránh tình trạng bị điểm mù khiến mô hình phân loại sai giữa Ngồi xuống nhanh và Ngã thực sự.

**3. Phương án lập trình Firmware (Sliding Window & Pipeline):**
- Chắc chắn sử dụng **Ring Buffer / Hàng đợi tĩnh (Static Queue)** để nạp liên tục dữ liệu cảm biến vào quy trình suy luận mà không lo tràn RAM.
- Kết hợp kỹ thuật **Cửa sổ trượt (Sliding Window)** (Ví dụ: Cửa sổ 400 mẫu, bước trượt 50 mẫu tương đương 0.5s). Phương án này đảm bảo hệ thống có thể liên tục cập nhật và dự đoán trạng thái theo thời gian thực (real-time inference) mà không bị đứt gãy mạch ngữ cảnh của RNN.