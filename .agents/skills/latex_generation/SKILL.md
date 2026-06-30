---
name: latex_generation
description: Sinh nội dung LaTeX và chèn vào đúng mục (section) trong luận văn. Kích hoạt khi người dùng yêu cầu "Hãy viết cho tôi mục [Tên mục] dựa trên các ý sau".
---

# Kỹ năng: Sinh Nội Dung Section LaTeX

> **Đọc trước:** `project_setup/architecture/report.md` (cấu trúc chương, build & verify hình tại máy, glossary, `ols`, sở hữu chương multi-agent). Đường dẫn REPORT tương đối gốc workspace.

**Các bước thực thi của Agent:**
1. **Tìm file:** Xác định đúng file chương trong `REPORT/Do_an_tot_nghiep_Vu_Manh_Hung/Chuong/` (xem bảng map chương→file trong `report.md`).
2. **Đọc hướng dẫn template (tham khảo):** Đọc file `.tex` cùng tên trong các thư mục Template (`REPORT/SOICT_DATN_Application_VIE_Template/Chuong/` hoặc `REPORT/SOICT_DATN_Research_VIE_Template/Chuong/`) để biết yêu cầu/độ dài từng mục của giảng viên. (Template trống — chỉ đọc, KHÔNG sửa.)
3. **Đọc file làm việc:** Đọc file chương thật trong `REPORT/Do_an_tot_nghiep_Vu_Manh_Hung/Chuong/` để nắm bối cảnh hiện tại và văn phong.
4. **Sinh văn bản:** Sinh đoạn LaTeX học thuật tiếng Việt từ dữ liệu thô + hướng dẫn template. Quy ước (xem `report.md` §6): `\texttt{}` cho định danh code, **không bịa số** (số liệu model lấy từ bảng §5.1), giữ văn phong khớp file hiện có.
   <!-- TẠMTHỜI TẮT §7 — bỏ comment khi muốn áp dụng lại
   - §7.1: một ý/đoạn, câu súc tích, không từ cảm xúc, liệt kê dùng (i)(ii)(iii).
   - §7.2: nếu viết Abstract — 200–350 từ, 4 phần theo thứ tự, đoạn văn (không bullet), tự đứng độc lập.
   - §7.3: khi chèn `\includegraphics` — kiểm tra resolution file; ưu tiên PDF/EPS vector; caption đặt dưới hình, đủ mô tả.
   - §7.4: caption bảng đặt trên bảng; tránh đường kẻ dọc; không trùng lặp số liệu đã có trong text.
   - §7.5: dùng hệ SI; đánh số `\begin{equation}` và tham chiếu `\eqref{}` trong text.
   -->
5. **Sửa file:** Dùng Edit chèn nội dung vào đúng vị trí trong file chương thật. **Tránh sửa song song** các mục TinyML/AI nếu agent khác đang viết (`report.md` §6).
6. **Verify tại máy (nên làm):** Build `pdflatex ... DoAn.tex` (`EXIT=0`) và rasterize trang bằng `rungs` để tự xem hình/figure trước khi báo xong (chi tiết: `report.md` §2). Xóa ảnh debug sau.
7. **Báo cáo:** Tóm tắt thay đổi và nhắc người dùng dùng `ols` đồng bộ Overleaf (đẩy ĐỦ file đã đổi, kể cả `DoAn.tex` nếu sửa preamble).
