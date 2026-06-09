---
name: format_latex
description: Quy trình các bước chuyển đổi và định dạng nội dung thô thành mã nguồn LaTeX chuẩn.
---

# Workflow: Format LaTeX

Workflow này được kích hoạt khi người dùng yêu cầu chuyển đổi văn bản, dữ liệu thô sang định dạng LaTeX chuẩn hoặc rà soát lại file LaTeX để sửa lỗi định dạng.

## Bước 1: Phân tích nội dung
- Đọc kỹ yêu cầu và nội dung mà người dùng muốn chuyển sang LaTeX.
- Xác định các thành phần cần định dạng như: Từ in đậm, in nghiêng, trích dẫn, danh sách liệt kê, hình ảnh, bảng biểu.

## Bước 2: Xử lý ký tự đặc biệt
- Rà soát các ký tự đặc biệt có khả năng gây lỗi biên dịch LaTeX như: `%`, `&`, `$`, `_` và thêm `\` đằng trước chúng (ngoại trừ khi trong môi trường toán học).
- Đặc biệt lưu ý việc đổi `&` thành `\&`.

## Bước 3: Cấu trúc văn bản và Danh sách
- Áp dụng `\textbf{}` cho in đậm và `\textit{}` cho in nghiêng.
- Nếu có danh sách liệt kê, bắt buộc đưa vào môi trường `\begin{itemize}` (cho gạch đầu dòng) hoặc `\begin{enumerate}` (cho số thứ tự) với các thẻ `\item` ở đầu. TUYỆT ĐỐI KHÔNG dùng gạch đầu dòng thô.

## Bước 4: Xử lý Hình ảnh & Bảng biểu (nếu có)
- Tạo môi trường `\begin{figure}` hoặc `\begin{table}` một cách chuẩn chỉ.
- BẮT BUỘC thêm `\caption{}` và `\label{}` cho tất cả hình ảnh/bảng biểu. (Chú thích hình ảnh phải đặt dưới hình vẽ).

## Bước 5: Tham chiếu và Trích dẫn
- Đảm bảo hình ảnh/bảng biểu được tham chiếu trong nội dung chữ ít nhất 1 lần bằng lệnh `\ref{}`.
- Cập nhật trích dẫn chuẩn bằng `\cite{}` đối chiếu với file `Danh_sach_tai_lieu_tham_khao.bib`.
- Cập nhật các từ viết tắt nếu có.

## Bước 6: Trả về kết quả
- Cung cấp đoạn mã LaTeX cuối cùng hoàn chỉnh và giải thích ngắn gọn về các thay đổi (nếu cần thiết).
