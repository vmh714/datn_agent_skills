# Báo cáo luận văn (REPORT — LaTeX)

> **Cập nhật lần cuối:** 2026-06-22
> Canonical doc cho thư mục `REPORT/` (luận văn LaTeX). **Đọc trước khi viết/sửa báo cáo** để khỏi dò mò cấu trúc, build và quy ước hình.

## 1. Vị trí & cấu trúc
- Thư mục thật: **`REPORT/Do_an_tot_nghiep_Vu_Manh_Hung/`**. (Bản `REPORT/SOICT_DATN_Application_VIE_Template/` chỉ là **template trống** — KHÔNG sửa, chỉ tham khảo hướng dẫn từng mục.)
- File chính: **`DoAn.tex`** (preamble + thứ tự `\subfile` các chương). Ảnh: `Hinhve/`. Từ viết tắt: `Tu_viet_tat.tex`. Tài liệu tham khảo: `Danh_sach_tai_lieu_tham_khao.bib`.

| Chương | File |
|---|---|
| 1 — Giới thiệu (đặt vấn đề, mục tiêu, **câu hỏi & đóng góp nghiên cứu**, bố cục) | `Chuong/1_Gioi_thieu.tex` |
| 2 — Khảo sát & phân tích yêu cầu (use case, đặc tả) | `Chuong/2_Khao_sat.tex` |
| 3 — Nền tảng lý thuyết & công nghệ | `Chuong/3_Cong_nghe.tex` |
| 4 — Thiết kế · Triển khai · Kết quả & kiểm thử | `Chuong/4_Ket_qua_thuc_nghiem.tex` |
| 5 — Giải pháp & đóng góp (Bài toán→Giải pháp→Kết quả) | `Chuong/5_Giai_phap_dong_gop.tex` |
| 6 — Kết luận & hướng phát triển | `Chuong/6_Ket_luan.tex` |

## 2. Build & KIỂM TRA HÌNH tại máy ⚠️ (đừng đoán "hình có hiện không")
Máy có sẵn **TinyTeX** tại `/c/TinyTex/TinyTeX/bin/windows/` (`pdflatex`, `latexmk`) + ghostscript `rungs`.
- **Bắt lỗi cú pháp:** `pdflatex -interaction=nonstopmode -halt-on-error DoAn.tex` (chạy ở thư mục `Do_an_tot_nghiep_Vu_Manh_Hung/`). `EXIT=0` = qua hết mọi `tikzpicture`/figure.
- **Glossary & bibliography cần 2 lượt** `pdflatex` (hoặc `latexmk -pdf`) mới in đủ.
- **Xem trang/hình để verify (cực hữu ích cho TikZ & figure):** rasterize PDF → PNG rồi Read:
  `rungs -sDEVICE=png16m -r110 -dFirstPage=N -dLastPage=N -o ./_chk_p%d.png DoAn.pdf` → Read `_chk_p1.png`. **Xóa ảnh debug sau khi xem.**
  Lệch trang: front-matter ~12 trang ⇒ *PDF page ≈ trang in + 12*. Lấy tổng trang từ log: `Output written on DoAn.pdf (N pages`.

## 3. Glossary / Danh mục từ viết tắt
- Cơ chế **đang dùng**: định nghĩa `\newglossaryentry{label}{type=\acronymtype, name={ABBR}, description={Nghĩa VN (English)}}` trong `Tu_viet_tat.tex`; in bằng `\glsaddall` + `\printnoidxglossaries` (DoAn.tex ~dòng 259–264). Tự sắp ABC, 2 cột "Thuật ngữ | Ý nghĩa". **Thân bài KHÔNG cần `\gls{}`.**
- Longtable thủ công `Chuong/0_5_Danh_muc_viet_tat.tex` **đã bị comment** trong DoAn.tex — bỏ qua, đừng nhầm là nguồn.

## 4. Hình ảnh
- Đặt tại `Hinhve/`. Sơ đồ hiện có (`arch/fsm/erd/sync/pppos_stack/mqtt_architechture.png`) là draw.io/Mermaid — **ổn, không cần vẽ lại**.
- **Danh sách hình CÒN THIẾU** + phân loại (🖐️ vẽ tay / 📊 plot từ dữ liệu / 📷 screenshot): **`plans/report_missing_figures_plan.md`**.
- TikZ vẽ trực tiếp được (use case, activity, sơ đồ khối) — preamble đã nạp `tikz` + libs `shapes.geometric, positioning, fit, arrows.meta, backgrounds, calc` + style use case (`usecase`, `ucsystem`, `ucactorpic`).

## 5. Đồng bộ Overleaf (`ols`)
- User build bản chính trên **Overleaf** qua lệnh `ols`. Sau khi sửa, **đẩy ĐỦ mọi file đã đổi**.
- ⚠️ Gotcha hay quên: nếu thêm `\usepackage`/style vào **preamble `DoAn.tex`**, **phải đẩy luôn `DoAn.tex`** — chỉ đẩy file chương sẽ khiến Overleaf thiếu package → lỗi hoặc không ra hình.

## 6. Sở hữu chương (multi-agent) & quy ước viết
- Các mục **TinyML/AI** (kiến trúc model, huấn luyện, kết quả model ở §4.2–4.3, §5.2) thường do **agent phiên khác** viết → **tránh sửa song song cùng file** (`4_Ket_qua_thuc_nghiem.tex`) vì dễ đè nhau; nếu cần đụng thì thống nhất trước hoặc chỉ dùng edit phẫu thuật từng chuỗi unique.
- An toàn cho agent chính: **Web/Firmware**, cấu trúc/bố cục, hình, glossary, Kết luận.
- Quy ước: tiếng Việt học thuật; `\texttt{}` cho định danh code; **không bịa số** — số liệu model lấy từ **bảng kết quả §4.3** (nguồn chuẩn), các nơi khác trỏ về.
- Phân vai chương: §4.3 = **bằng chứng/số đo**; §5.x = **đóng góp/lập luận** (Bài toán→Giải pháp→Kết quả). Đừng kể đầy đủ một câu chuyện ở cả hai nơi.
