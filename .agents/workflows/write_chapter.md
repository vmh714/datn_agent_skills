---
description: Quy trình 5 bước viết luận văn LaTeX (đối chiếu template, viết, cập nhật bib).
---

# Luồng Làm Việc (Workflow) Của Agent

Tài liệu này xác định các bước cụ thể mà AI Agent và User sẽ phối hợp để hoàn thiện từng phần của luận văn. Agent cần tuân thủ thứ tự này khi nhận lệnh.

## Bước 1: Tiếp Nhận Yêu Cầu và Dữ Liệu Thô
- User cung cấp cho Agent phần cần viết (ví dụ: Section 1.2) kèm theo các bullet point, số liệu, ý tưởng thô.
- **Hành động của Agent:** 
  1. Xác nhận yêu cầu.
  2. BẮT BUỘC tự động mở và đọc file `Chuong/X_Y.tex` tương ứng nằm ở thư mục Template (`SOICT_DATN_Application_VIE_Template/Chuong/...`) để xem các hướng dẫn, nội dung đề xuất, và skeleton của phần đó.
  3. Mở file `Chuong/X_Y.tex` tương ứng nằm ở thư mục Làm việc (`Đồ_án_tốt_nghiệp___Vũ_Mạnh_Hưng/Chuong/...`) để nắm bối cảnh đoạn hiện tại chuẩn bị viết vào.

## Bước 2: Viết Nội Dung (Drafting)
- Agent tiến hành viết nội dung bằng Tiếng Việt học thuật, chuyển đổi các bullet point thành đoạn văn mạch lạc.
- Agent chèn sẵn các thẻ định dạng LaTeX cần thiết (`\textbf`, `\cite`, `\ref`,...).
- **Hành động của Agent:** Viết nội dung nháp và hiển thị cho User xem HOẶC ghi đè trực tiếp vào file `.tex` ở vị trí User chỉ định thông qua công cụ sửa file.

## Bước 3: Cập Nhật Tài Nguyên Bổ Trợ
- Trong quá trình viết, nếu phát sinh từ viết tắt mới hoặc tài liệu tham khảo mới theo yêu cầu của User:
  - Agent mở file `Tu_viet_tat.tex` và thêm vào đúng format.
  - Agent mở file `Danh_sach_tai_lieu_tham_khao.bib` và thêm BibTeX.

## Bước 4: Chờ Phản Hồi và Verify
- Agent dừng lại và yêu cầu User đọc lại nội dung trong file.
- User có thể dùng `git diff` để xem thay đổi, dùng lệnh `ols` để push lên Overleaf và Recompile để xem PDF.
- Nếu User báo lỗi biên dịch, Agent phân tích log lỗi để sửa. 
  - **LƯU Ý QUAN TRỌNG:** Nếu lỗi báo "Option clash" hoặc "Failed to resolve references / Missing references", việc ĐẦU TIÊN là nhắc User dọn rác (Clean up auxiliary files). 
  - TUYỆT ĐỐI KHÔNG tự ý sửa file gốc `DoAn.tex` của template để fix lỗi trừ khi có lệnh trực tiếp từ User.

## Bước 5: Hoàn Tất
- Sau khi User xác nhận phần nội dung đó đã "Xong", Agent ghi chú vào checklist (task.md nếu có) và chờ yêu cầu cho phần (section) tiếp theo. Tuyệt đối không tự ý nhảy sang viết phần khác khi chưa có lệnh.
