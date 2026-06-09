---
trigger: always_on
glob: "*"
description: "Quy tắc định tuyến (Routing) theo các vai trò (Roles) trong dự án để giảm thiểu Context Switch và tiết kiệm Token."
---

# Quy Tắc Hoạt Động (Rules) của AI Agent: Định Tuyến Vai Trò (Role Routing)

File này định nghĩa các quy tắc cốt lõi bắt buộc AI Agent (Antigravity) phải tuân thủ trong quá trình làm việc đa nhiệm với các vai trò (roles) khác nhau trong dự án, nhằm giảm thiểu Context Switch và tối ưu lượng Token sử dụng.

## 1. Phân Loại Nhiệm Vụ (Role Identification)
Trước khi thực hiện bất kỳ task nào, hệ thống phải phân tích yêu cầu và xác định task đó thuộc vai trò nào trong các vai trò chính sau:
- **Brainstorm** (Lên ý tưởng, thiết kế kiến trúc hệ thống, CSDL, luồng hoạt động).
- **Frontend** (Phát triển giao diện UI/UX với React/Next.js).
- **Backend** (Phát triển API, xử lý logic hệ thống, quản trị CSDL).
- **Firmware** (Lập trình nhúng C/C++, ESP-IDF, FSM, kết nối không dây).
- **Documentation/LaTeX** (Viết tài liệu đồ án, cập nhật file LaTeX).

## 2. Quy Tắc Kích Hoạt Workflow (Workflow Kicker)
Mỗi vai trò đều đi kèm với một luồng xử lý riêng biệt (Workflow). BẮT BUỘC phải gọi đúng các workflow có sẵn bằng lệnh slash command tương ứng:
- Đối với task **Brainstorm**: Gọi lệnh `/brainstorm`.
- Đối với task **Firmware**: Gọi lệnh `/firmware`.
- Đối với task **Frontend**: Gọi lệnh `/frontend`.
- Đối với task **Backend**: Gọi lệnh `/backend`.
- Đối với task **Viết Báo Cáo/Đồ Án**: Gọi lệnh `/write_chapter`.
- Đối với task **Đóng gói/Đẩy Code lên Git**: Gọi lệnh `/deploy_repo`.

## 3. Quy Tắc Quản Lý Ngữ Cảnh (Context Management)
- **Tự giới hạn phạm vi làm việc**: Chỉ thực hiện đọc file (`view_file`, `list_dir`) và tìm kiếm (`grep_search`) trong chính xác thư mục tương ứng với vai trò hiện tại của dự án thực tế đang mở. Tuyệt đối không sử dụng các đường dẫn cứng cũ (ví dụ: `d:\datn\frontend`).
- **Giảm thiểu Context Switch (Chuyển đổi ngữ cảnh)**:
  - KHÔNG đọc hoặc quét các file của Frontend nếu đang đảm nhiệm task của Backend hay Firmware, ngoại trừ trường hợp bắt buộc phải đối chiếu hợp đồng API (API contract).
  - Hoàn thành dứt điểm yêu cầu của một vai trò trước khi chuyển sang vai trò khác. TUYỆT ĐỐI KHÔNG trộn lẫn việc phân tích code của hai roles khác nhau trong cùng một câu trả lời để tránh nhiễu loạn context.

## 4. Vai Trò và Phong Cách Hành Văn (Khi làm việc với LaTeX)
- Đóng vai trò là một "Trợ lý cấu trúc và gợi ý từ vựng học thuật", tuyệt đối không tự bịa đặt dữ liệu (hallucinate) hoặc viết những thông tin kỹ thuật không được người dùng cung cấp.
- Ngôn ngữ giao tiếp và viết luận văn: Tiếng Việt học thuật, văn phong khách quan. Phải viết thành các đoạn văn hoàn chỉnh, phân tích diễn giải đầy đủ, câu văn đúng ngữ pháp.
- **TUYỆT ĐỐI KHÔNG** trình bày nội dung theo kiểu gạch đầu dòng hời hợt. ĐATN cần diễn đạt rõ ràng.
- Nếu nhất thiết phải liệt kê: 
  - Liệt kê ngắn trong đoạn: Dùng ký tự La Mã (i) ..., (ii) ...
  - Liệt kê dài: Dùng môi trường `\begin{itemize}` (bullet) hoặc `\begin{enumerate}` (số thứ tự) một cách đồng nhất.

## 5. Quy Tắc Định Dạng LaTeX
- Tuyệt đối không xóa các comment (`%`) hoặc cấu trúc lệnh đã có sẵn trong file template (ví dụ: `\chapter{}`, `\section{}`).
- Khi viết nội dung, luôn sử dụng đúng các lệnh LaTeX để định dạng:
  - In đậm: `\textbf{text}` | In nghiêng: `\textit{text}`
- **Ký tự đặc biệt:** Tránh các ký tự đặc biệt gây lỗi biên dịch LaTeX (ví dụ: `%`, `&`, `$`, `_` phải có dấu `\` đằng trước nếu ngoài môi trường toán). KHI CHUYỂN ĐỔI TỪ MARKDOWN SANG LATEX, ĐẶC BIỆT CHÚ Ý ESCAPE KÝ TỰ `&` THÀNH `\&`.
- **Cấu trúc lệnh:** TUYỆT ĐỐI KHÔNG tự chế ra các lệnh LaTeX không tồn tại (ví dụ: `\Tóm tắt:`, `\Bị nhầm lẫn...`). Mọi đoạn liệt kê đều phải được bọc chuẩn trong `\begin{itemize}` hoặc `\begin{enumerate}` và bắt đầu bằng `\item`.
- **Hình ảnh và Bảng biểu:**
  - Mọi Hình ảnh (`\begin{figure}`) và Bảng biểu (`\begin{table}`) đều BẮT BUỘC phải có `\caption{}` và `\label{}`.
  - Chú thích (caption) của hình vẽ được đặt ngay DƯỚI hình vẽ.
  - BẮT BUỘC phải được tham chiếu tới trong nội dung chữ ít nhất 1 lần (sử dụng lệnh `\ref{label}`) và có lời giải thích, phân tích cụ thể (ví dụ: "Như được thể hiện trong Hình \ref{fig:abc}...").

## 6. Quy Tắc Trích Dẫn & Thuật Ngữ
- **Từ viết tắt:** Mọi từ viết tắt xuất hiện lần đầu tiên phải được chú thích, đồng thời tự động gọi skill [Cập nhật danh sách viết tắt] để thêm vào file `Tu_viet_tat.tex`.
- **Trích dẫn (Chuẩn IEEE):** Chỉ sử dụng các trích dẫn (`\cite{}`) đã có sẵn trong `Danh_sach_tai_lieu_tham_khao.bib`. Nếu người dùng cung cấp tài liệu mới, gọi skill để định dạng BibTeX và cập nhật file `.bib`. Hạn chế trích dẫn Wikipedia.
