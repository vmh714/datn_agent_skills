# TinyML Model Architecture

> **Cập nhật lần cuối:** 2026-06-20

Tài liệu này mô tả chi tiết về cấu trúc model, luồng dữ liệu (data pipeline) và quá trình lượng tử hóa/export dành cho hệ thống nhận diện ngã (Fall Detection) và nhận dạng hành động (HAR) trên nền tảng MCU (TinyML).

## 1. Tổng quan
- **Vị trí làm việc chính:** `sis_fall_har_and_fall-detection_trainning/`
- **Phiên bản Model hiện tại:** `train_v25` (LSTM/TCN) - Đang dùng làm baseline.
- **Phiên bản sắp triển khai (Upcoming):** `train_v30` (CNN / ResNet1D) - Tối ưu hóa đặc biệt cho tập lệnh `esp-nn` để chạy inference siêu nhẹ trên chip ESP.

## 2. Model Architecture & Pipeline

### Kiến trúc Model
- **Input Shape:** Typically `(200, 6)` hoặc điều chỉnh tương ứng với window size (Dữ liệu từ cảm biến Gia tốc + Con quay hồi chuyển).
- **Mục tiêu phiên bản mới (v30):** Tập trung phát triển các block `Conv1D`, `SeparableConv1D`, hoặc mô hình dạng ResNet1D. Lý do là phần cứng ESP-NN có thư viện hỗ trợ tăng tốc cho Conv1D tốt hơn so với RNN/LSTM.

### Data Pipeline
- Dữ liệu thô từ bộ dataset (ví dụ: `SisFall_dataset`) sẽ đi qua bước:
  1. **Tiền xử lý (Preprocessing):** Cân bằng trục, chuẩn hóa (Normalization).
  2. **Trích xuất cửa sổ (Windowing):** Phân mảnh dữ liệu theo thời gian.
  3. **Gắn nhãn (Labeling):** Gắn nhãn các hành động và ngã (Walk, Idle, Run, Fall, Trans...).
- Pipeline được quản lý bởi các class như `DataPreprocessor` hoặc `KFoldDataManager` trong các notebook huấn luyện.

### Compression & Export
- **Yêu cầu bắt buộc:** Để chạy trên MCU, model phải được nén về dạng INT8 (Quantization) bằng TFLite Converter.
- **Quá trình Export:**
  - Convert Keras model -> `model.tflite` (INT8, đảm bảo chỉ dùng các operation được TFLite Micro hỗ trợ).
  - Khởi tạo mảng C/C++ từ file `.tflite` (tạo `model_data.cc` và `model_data.h`) để nhúng cứng (embed) vào bộ nhớ Flash của Firmware.

## 3. Quy trình làm việc của Agent (Workflow)
- **Sửa file code (Notebook):** Tuyệt đối KHÔNG sửa tay cấu trúc JSON của file `.ipynb`. Bắt buộc phải sử dụng tool `manage_notebook_cells.py` ở thư mục gốc hoặc gọi qua Agent Skill `notebook_modification`.
- **Cập nhật Document:** Sau khi thay đổi kiến trúc mô hình, hyper-parameters hoặc quá trình deploy xuống Firmware thành công, vui lòng cập nhật lại file này để đảm bảo đồng bộ với code thực tế.
