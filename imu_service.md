# Giải thích đoạn code `imu_service.c`

## 1. Bối cảnh

Đoạn code này là một phần trong firmware của **thiết bị đeo phát hiện té ngã và nhận diện hoạt động (HAR) cho người cao tuổi**, chạy trên vi điều khiển **ESP32-S3** với hệ điều hành thời gian thực **FreeRTOS** (framework ESP-IDF). Thiết bị đọc dữ liệu từ cảm biến gia tốc/con quay hồi chuyển 6 trục **MPU6050** ở tần số 100 Hz, tiền xử lý tín hiệu ngay trên thiết bị (edge), rồi đưa vào một mô hình **TinyML** (TensorFlow Lite Micro, lượng tử hóa INT8) để suy luận xem người dùng có bị ngã hay không.

File `imu_service.c` đảm nhiệm tầng **thu thập và tiền xử lý tín hiệu IMU** — mắt xích đầu tiên của toàn bộ pipeline. Đầu vào là dữ liệu thô từ cảm biến; đầu ra là một cửa sổ trượt (sliding window) dữ liệu đã được làm sạch và chuẩn hóa, sẵn sàng cho mô hình AI.

## 2. Vấn đề cần giải quyết

Việc đọc cảm biến 100 Hz trên một thiết bị đeo chạy pin đặt ra ba bài toán cùng lúc:

1. **Hạn chế phần cứng khiến việc gom mẫu trở nên khó:** Chân ngắt (INT) của MPU6050 chỉ hỗ trợ đúng hai chế độ — báo *có dữ liệu mới* (kích hoạt cho **từng mẫu**, tức 100 lần/giây) hoặc báo *FIFO bị tràn*. Cảm biến **không** có ngắt theo ngưỡng (FIFO watermark) để báo "đã đủ 50 mẫu". Tệ hơn, khối I2C của ESP32-S3 **không hỗ trợ DMA**, nên mỗi lần đọc FIFO đều bắt buộc phải có CPU tham gia, không thể giao cho phần cứng tự chuyển dữ liệu nền. Hệ quả: hoặc CPU phải thức dậy 100 lần/giây để xử lý từng ngắt "có dữ liệu mới", hoặc phải polling liên tục — cả hai đều rất hao pin và chiếm CPU.
2. **Chất lượng tín hiệu:** Tín hiệu IMU thô bị nhiễu mạnh; nếu đưa thẳng vào mô hình sẽ làm giảm độ chính xác nhận diện.
3. **Đồng nhất dữ liệu:** Dữ liệu dùng để huấn luyện mô hình và dữ liệu lúc suy luận phải đi qua cùng một quy trình tiền xử lý; nếu lệch nhau, mô hình sẽ hoạt động sai.

## 3. Cách giải quyết trong đoạn code

### 3.1. Tự "chế" ngắt theo ngưỡng bằng bộ đếm xung phần cứng (PCNT)

Vì MPU6050 không có ngắt báo "đủ 50 mẫu" và I2C của ESP32-S3 lại không có DMA, em giải quyết bằng cách **tận dụng ngoại vi PCNT (Pulse Counter)** của ESP32-S3 để tự tổng hợp ra loại ngắt mà phần cứng không sẵn có. Ý tưởng: vẫn để MPU6050 phát ngắt "có dữ liệu mới" cho từng mẫu như bình thường, nhưng thay vì nối chân INT đó vào CPU, em **nối nó vào đầu vào đếm xung của PCNT**. PCNT đếm các xung này hoàn toàn bằng phần cứng (CPU không can thiệp); chỉ khi đếm đủ một lô **`IMU_BATCH_SIZE` (50 mẫu ≈ 0.5 giây)**, watch-point của PCNT mới sinh đúng một ngắt, gọi hàm `pcnt_on_reach()`.

Nói cách khác, em đã biến chuỗi 50 ngắt "có dữ liệu mới" thành **một** ngắt "đã đủ một lô" — đúng thứ mà MPU6050 thiếu. Nhờ vậy CPU chỉ phải thức dậy **2 lần/giây** thay vì 100 lần/giây, ngủ được giữa các lô, và việc đọc FIFO (vốn bắt buộc dùng CPU do không có DMA) được dồn lại thành một lần đọc khối duy nhất mỗi 0.5 giây. Trong ngắt, hàm dùng `vTaskNotifyGiveFromISR()` để đánh thức task xử lý một cách an toàn (ISR-safe), giữ phần code trong ngắt càng ngắn càng tốt.

### 3.2. Đọc khối (burst read) qua FIFO

Khi được đánh thức, `imu_processing_task()` đọc nguyên cả lô 50 mẫu từ bộ đệm **FIFO** của cảm biến bằng một lần đọc I2C duy nhất (`mpu6050_read_fifo`), thay vì 50 giao dịch I2C riêng lẻ. Điều này giảm tải bus và tăng hiệu năng.

### 3.3. Đổi hệ trục và lọc Kalman

Với mỗi mẫu, code thực hiện hai việc:

- **Đổi hệ trục cảm biến sang hệ trục thân (Forward-Left-Up):** do cảm biến gắn trên mạch theo một phương khác với phương cơ thể, cần ánh xạ lại để góc nghiêng có ý nghĩa vật lý.
- **Ước lượng góc `pitch` bằng bộ lọc Kalman 2 trạng thái:** kết hợp (fusion) góc tính từ gia tốc kế với tốc độ góc từ con quay hồi chuyển, cho ra góc nghiêng mượt và không bị trôi (drift). Góc này được dùng để **xác định tư thế** (nằm/ngồi/đứng).

Đồng thời, cả **6 trục** dữ liệu được lọc nhiễu riêng lẻ bằng **bộ lọc Kalman 1D** để loại bỏ nhiễu cao tần trước khi đưa vào mô hình.

### 3.4. Chuẩn hóa cho mô hình TinyML INT8

Sau khi lọc, mỗi trục được chia cho dải đo toàn thang (full-scale range) để **chuẩn hóa về khoảng `[-1, 1]`** — đúng định dạng đầu vào mà mô hình INT8 đã được huấn luyện. Dữ liệu được ghi vào một **bộ đệm vòng (circular buffer)** `imu_win` đóng vai trò cửa sổ trượt; sau mỗi lô, `svc_ai_process_window()` được gọi để mô hình suy luận trên cửa sổ mới nhất (bước trượt 0.5 giây).

### 3.5. Thu thập dữ liệu nhất quán cho việc huấn luyện

Khi hệ thống ở trạng thái `STATE_STREAMING` (chế độ thu thập dataset), code lưu lại **chính dữ liệu đã qua tiền xử lý** (đổi trục, lọc, chuẩn hóa — chỉ khác là scale sang `int16`) rồi đẩy lên cloud qua callback. Điểm mấu chốt ở đây là dữ liệu thu thập để huấn luyện **trùng khớp tuyệt đối** với dữ liệu mà mô hình thấy lúc suy luận, tránh sai lệch phân phối (train/serve skew) — một lỗi rất phổ biến và khó phát hiện trong các hệ thống ML nhúng.

## 4. Những điểm em tâm đắc

Đoạn code này gói gọn được nhiều quyết định kỹ thuật mà em thấy thú vị trong lập trình nhúng:

- **Vượt giới hạn phần cứng bằng một ngoại vi khác:** khi MPU6050 không có ngắt theo ngưỡng và I2C của ESP32-S3 không có DMA, em đã "mượn" PCNT để tự tổng hợp ra ngắt gom-lô mà cảm biến thiếu, thay vì chấp nhận thức CPU 100 lần/giây. Đây là phần em tâm đắc nhất — giải quyết bài toán bằng cách hiểu rõ và phối hợp các ngoại vi sẵn có trên chip.
- **Tách bạch tầng (layered architecture):** file này chỉ lo thu thập + tiền xử lý, giao tiếp với tầng AI và tầng cloud qua callback/event, không gọi trực tiếp — dễ kiểm thử và bảo trì.
- **Ngắt gọn, xử lý nặng đẩy ra task:** phần code trong ISR chỉ phát tín hiệu đánh thức, toàn bộ tính toán nằm trong task — đúng nguyên tắc lập trình thời gian thực.
- **Tư duy đồng nhất pipeline dữ liệu:** đảm bảo tiền xử lý lúc huấn luyện và lúc suy luận là một, để mô hình AI hoạt động đúng như khi train.
