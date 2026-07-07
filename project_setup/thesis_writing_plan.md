# Kế hoạch Bổ sung Thông tin Báo cáo Khoa học cho Đồ án

Cấu trúc đồ án đã được chuẩn hóa, nhưng để đạt được "chất lượng" của một bài báo khoa học thực thụ, chúng ta cần rà soát và bổ sung nội dung cho từng chương theo các tiêu chuẩn khắt khe hơn (đặc biệt là việc nhấn mạnh *Khoảng trống nghiên cứu* và *Đóng góp khoa học*).

Dưới đây là kế hoạch chi tiết các phần cần bổ sung, được sắp xếp theo thứ tự ưu tiên:

## 1. Phần Front-matter (Ưu tiên Cao - Dễ làm)
- **Tóm tắt (Abstract) Tiếng Việt & Tiếng Anh (`0_3_Tom_tat_noi_dung.tex`, `0_4_...`)**
  - **Trạng thái:** Cần kiểm tra lại độ dài (đảm bảo 200-350 từ).
  - **Cần làm:** Phải viết thành một đoạn văn duy nhất (không gạch đầu dòng), chứa đủ 4 phần: *Bối cảnh $\to$ Hạn chế $\to$ Giải pháp đề xuất (TinyML/PCNT) $\to$ Kết quả định lượng (Ví dụ: F1-score đạt X%, suy luận Y ms).*

## 2. Chương 1: Giới thiệu đề tài (Ưu tiên Cao)
- **Trạng thái:** Đã chuyển phần "Nghiên cứu liên quan" (Đọc báo) từ Chương 2 vào đây.
- **Cần làm:** 
  - Cuối mục `2_2_Nghien_cuu_lien_quan.tex` (nằm trong Chương 1), cần bổ sung một đoạn kết luận chỉ rõ **"Khoảng trống nghiên cứu" (Research Gap)**. Ví dụ: *"Hầu hết các nghiên cứu trước đây dùng AI trên Cloud gây trễ, hoặc dùng TinyML nhưng xử lý nhãn động học chưa tốt. Đồ án này lấp đầy khoảng trống đó bằng..."*
  - Bổ sung một tiểu mục **"Các đóng góp chính của đề tài" (Main Contributions)**. Phần này bắt buộc phải liệt kê thành các gạch đầu dòng (thường là 3-4 ý chính: Đề xuất sơ đồ nhãn Trans/Idle, Tối ưu hóa kiến trúc CNN cho ESP32, Áp dụng PCNT). Đây là phần giáo viên sẽ đọc đầu tiên để đánh giá điểm.

## 3. Chương 2: Cơ sở lý thuyết (Ưu tiên Thấp)
- **Trạng thái:** Chỉ còn giữ lại lý thuyết nền tảng (`2_1_Nen_tang_ly_thuyet.tex`).
- **Cần làm:** Rà soát lại xem phần lý thuyết có bị đứt gãy mạch văn sau khi tách phần Khảo sát ra hay không.

## 4. Chương 3: Phương pháp & Giải pháp đề xuất (Ưu tiên Cao - Cốt lõi)
- **Trạng thái:** File `3_Phuong_phap_de_xuat.tex` chứa nội dung rất tốt về thuật toán và kiến trúc.
- **Cần làm:**
  - Bổ sung các phương trình toán học/lý thuyết nền tảng (nếu còn thiếu) khi giải thích về CNN hoặc hàm mất mát (Loss function) để tăng tính hàn lâm.
  - Vẽ thêm sơ đồ khối trực quan (Mermaid/Draw.io) mô tả luồng cắt cửa sổ trượt và gán nhãn, thay vì chỉ mô tả bằng chữ.

## 5. Chương 4: Phân tích & Thiết kế hệ thống (Ưu tiên Trung bình)
- **Trạng thái:** Đã chuyển phần Thiết kế (Mạng, DB, Firmware) vào đây (`4_1_Phan_tich_yeu_cau.tex`, `4_2_Thiet_ke.tex`).
- **Cần làm:**
  - Rà soát lại sơ đồ kiến trúc (System Architecture) để đảm bảo ngôn từ thống nhất với Chương 3 (sự kết nối giữa Edge - TinyML và Cloud - FastAPI).
  - Bổ sung thiết kế cơ chế cảnh báo hệ thống (System Alerts): Báo cáo cách thiết bị tự động theo dõi sức khỏe (Pin yếu < 20%, Lỗi phần cứng) và truyền tải qua MQTT `event` topic, kết hợp với giao diện Dashboard Real-time để tăng tính ổn định (Fault Tolerance).

## 6. Chương 5: Triển khai & Thực nghiệm (Ưu tiên Cao)
- **Trạng thái:** Đã có kết quả K-Fold, so sánh TCN và CNN (`5_Trien_khai_thuc_nghiem.tex`).
- **Cần làm:**
  - Định nghĩa rõ **Tham số cấu hình (Hyperparameters)** thành một bảng (Learning rate, Batch size, Optimizer).
  - Định nghĩa công thức toán học của các **Thang đo (Metrics)** được dùng (Accuracy, F1-Score, Recall) trước khi đưa ra biểu đồ.
  - Bổ sung phần **Thảo luận & Hạn chế (Discussion & Limitations)** ở cuối chương: Nhấn mạnh mô hình hoạt động kém ở trường hợp nào (ví dụ: người già chuyển tư thế quá chậm) để chứng minh tính khách quan khoa học.

## 7. Chương 6: Kết luận & Hướng phát triển (Ưu tiên Thấp)
- **Trạng thái:** `6_Ket_luan.tex`
- **Cần làm:** Viết lại kết luận bám sát vào các "Đóng góp chính" đã định nghĩa ở Chương 1, sử dụng các số liệu thực chứng từ Chương 5 để khẳng định thành công.
