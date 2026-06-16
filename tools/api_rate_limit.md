# API Rate Limits và Danh sách Mô hình

Dưới đây là thống kê các mô hình khả dụng cùng với giới hạn tương ứng của chúng. Các thông số bao gồm **RPM** (Requests Per Minute), **TPM** (Tokens Per Minute), và **RPD** (Requests Per Day). 

| Tên Mô Hình (Model) | Danh Mục (Category) | RPM | TPM | RPD |
| :--- | :--- | :--- | :--- | :--- |
| **Gemini 3.1 Flash Lite** | Text-out models | 15 | 250K | 500 |
| **Gemini 2.5 Flash Lite** | Text-out models | 10 | 250K | 20 |
| **Gemini 2.5 Flash** | Text-out models | 5 | 250K | 20 |
| **Gemini 3.5 Flash** | Text-out models | 5 | 250K | 20 |
| **Gemini 3 Flash** | Text-out models | 5 | 250K | 20 |
| Gemini 2.5 Pro | Text-out models | 0 | 0 | 0 |
| Gemini 2 Flash | Text-out models | 0 | 0 | 0 |
| Gemini 2 Flash Lite | Text-out models | 0 | 0 | 0 |
| Gemini 3.1 Pro | Text-out models | 0 | 0 | 0 |

### Phân tích và Đề xuất sử dụng
1. **Gemini 3.1 Flash Lite**: Là mô hình có rate limit cao nhất (15 request/phút, 500 request/ngày), cực kỳ thích hợp cho các tác vụ cần chạy lặp lại nhiều lần, crawl data, hay phân tích log liên tục.
2. **Gemini 2.5 Flash Lite**: Mô hình có giới hạn request/phút tốt thứ hai (10 RPM), phù hợp với các tác vụ trung bình.
3. **Các mô hình dòng Flash khác** (2.5 Flash, 3 Flash, 3.5 Flash): Giới hạn ở mức 5 RPM và 20 RPD. Chỉ nên dùng cho các tác vụ đặc thù yêu cầu khả năng suy luận nhanh nhưng không gọi API liên tục.
4. **Các mô hình Pro/Flash cũ (Giới hạn bằng 0)**: Hiện tại chưa có quota, không sử dụng0