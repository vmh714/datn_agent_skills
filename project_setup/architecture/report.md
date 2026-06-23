# Báo cáo luận văn (REPORT — LaTeX)

> **Cập nhật lần cuối:** 2026-06-23
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
- Đặt tại `Hinhve/`. Sơ đồ hiện có (`arch/fsm/erd/sync/pppos_stack/mqtt_architechture.png`) là draw.io/Mermaid.
- **`erd.png`** có nguồn Mermaid `Hinhve/erd.mmd` (đồng bộ với `architecture/db_schema.md`). Regen sau khi đổi schema: `npx -y @mermaid-js/mermaid-cli -i erd.mmd -o erd.png -b white -s 3 -p <pptr-cfg>` (puppeteer cần Chrome — máy này có `C:/Program Files/Google/Chrome/Application/chrome.exe`, truyền qua `executablePath` trong pptr-cfg.json). Lần cập nhật gần nhất: 2026-06-23, thêm bảng `verification_sessions`.
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

<!-- TẠMTHỜI TẮT — bỏ comment khi muốn áp dụng lại
## 7. Quy chuẩn viết & định dạng học thuật
> Tổng hợp từ hướng dẫn Elsevier/ScienceDirect IoT Journal (2025) — chỉ giữ lại phần tương thích template SOICT ĐATN.

### 7.1 Văn phong học thuật (áp dụng toàn bộ luận văn)
- Mỗi đoạn văn **một ý chính duy nhất**; câu sau liên kết ngữ nghĩa với câu trước.
- Câu ngắn gọn, tối ưu: không thêm/bớt được từ mà không mất nghĩa hoặc dư nghĩa.
- **Cấm** từ cảm xúc/chủ quan: "tuyệt vời", "cực kỳ hữu ích", "rất mạnh mẽ"…
- Liệt kê ngắn: dùng ký hiệu La Mã **(i), (ii), (iii)** inline trong câu, không dùng bullet nếu không cần thiết.
- Abstract phải **tự đứng độc lập**: không dùng viết tắt chưa định nghĩa, tránh trích dẫn tài liệu.

### 7.2 Cấu trúc Abstract (Tóm tắt tiếng Việt + English)
Độ dài: **200–350 từ** (ĐATN rule — ưu tiên hơn giới hạn 250 của journal). Viết thành đoạn văn liên tục, **không bullet**. Nội dung theo thứ tự:
1. Giới thiệu vấn đề — hiện trạng, các hướng tiếp cận đã có, hạn chế còn tồn tại.
2. Hướng tiếp cận được chọn và lý do lựa chọn.
3. Tổng quan giải pháp đề xuất.
4. Đóng góp chính và kết quả đạt được.

### 7.3 Hình ảnh — chất lượng và caption
**Độ phân giải tối thiểu:**
- Ảnh màu/xám (screenshot, photo): **300 dpi** (PNG/TIFF/JPG).
- Sơ đồ, biểu đồ dạng đường (line drawing): **1000 dpi** hoặc xuất **PDF/EPS (vector)** — ưu tiên vector.
- Draw.io: xuất → PDF (vector, chọn "Fit page") thay vì PNG mặc định 96 dpi.
- Matplotlib/plot: dùng `plt.savefig("fig.pdf")` hoặc `dpi=300` khi xuất PNG.

**Caption hình:** `\caption{Tiêu đề ngắn. Mô tả đủ để hiểu hình mà không cần đọc thân bài.}` — caption đặt *dưới* hình (`\caption` sau `\includegraphics`). Không in tiêu đề trực tiếp lên hình.

**Bắt buộc:** Mọi hình phải được **trích dẫn và giải thích** trong text (`Hình~\ref{fig:xxx} minh họa...`).

### 7.4 Bảng biểu
- Tránh đường kẻ **dọc** và tô màu ô (ưu tiên bảng tối giản, dùng `\hline` ngang là đủ).
- Không để bảng trình bày lại số liệu **đã mô tả đầy đủ trong text** — bảng bổ sung, không trùng lặp.
- Caption bảng đặt **trên** bảng (`\caption` trước `\begin{tabular}`).
- Mọi bảng phải được **trích dẫn và bình luận** trong text.

### 7.5 Phương trình & đơn vị
- Biến số: tự động nghiêng trong `math mode` — đúng rồi, không cần làm thêm.
- Dùng **hệ SI** xuyên suốt; nếu dùng đơn vị khác (g-force, ms…) kèm giá trị SI tương đương lần đầu xuất hiện.
- Phương trình display: đánh số `\begin{equation}\label{...}` và **tham chiếu trong text** bằng `\eqref{}`.

### 7.6 Tài liệu tham khảo
- Thêm **DOI** khi có (trường `doi = {...}` trong BibTeX) — tăng chất lượng, không bị cấm.
- Tên tạp chí: viết tắt theo **LTWA** (List of Title Word Abbreviations) nếu biết (IEEE BibTeX style tự xử lý phần lớn).
- Website: ghi URL + ngày truy cập cuối (đã theo mẫu template trường).
- Không dùng Wikipedia, slide bài giảng, blog cá nhân làm tài liệu tham khảo.
-->
