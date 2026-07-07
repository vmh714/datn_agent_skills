# Plan — Hoàn thiện bộ slide bảo vệ DATN (phiên tiếp tục)

## Context

Bộ slide bảo vệ tốt nghiệp (Vũ Mạnh Hưng, đề tài IoT eldercare + fall detection + TinyML) đã **gần hoàn thiện nội dung**: deck ~55 slide (main 1–29 + PL0–PL12), build OK, mọi ảnh tham chiếu đều tồn tại (không placeholder), audit số hiện **sạch** (11,2 ms / 180× / 97,5% đúng khắp nơi). Toàn bộ slide sinh bằng script `datn_agent_skills/tools/build_slides.py` (python-pptx) — **KHÔNG sửa tay .pptx**.

Phiên này người dùng chốt 3 trọng tâm + 1 đính chính số liệu (đã điều tra & giải quyết dưới đây).

### Chốt vấn đề số latency (đã điều tra tận gốc — quan trọng, tránh regression lần 4)
Ba số latency đều có thật nhưng **khác điều kiện đo, TUYỆT ĐỐI KHÔNG trộn**:
| Số | Điều kiện | Bội số vs TCN | Nguồn |
|---|---|---|---|
| **11,20 ms** ✅ | 240 MHz, arena SRAM (benchmark) | **~180×** (÷2014 ms) | Báo cáo Ch5 `tab:mcu_arch_compare` — **canonical** |
| ~17 ms | 160 MHz (scale từ 11,2×240/160) | — | ước lượng |
| ~~56,7 ms~~ | PSRAM, trước tối ưu cache | ~~36×~~ | `tinyml_model.md` L66 — **cũ, BỎ** |

**Quyết định người dùng:** giữ **11,2 ms / 180×** trên slide (khớp báo cáo) + **chú thích "deploy @ f_cpu = 240 MHz"** cạnh số latency. Không dùng 17/56.
> ⚠️ Caveat đã báo user: firmware `sdkconfig` hiện `CONFIG_ESP_DEFAULT_CPU_FREQ_MHZ=160`; câu "deploy 240 MHz" chỉ đúng tuyệt đối nếu đổi config (việc firmware, ngoài phạm vi phiên slide này).

## File & workflow (bất biến)
- Script: `datn_agent_skills/tools/build_slides.py` · Output: `report/Do_an_tot_nghiep_Vu_Manh_Hung/DATN_VuManhHung_slides.pptx` · Ảnh: `.../Hinhve/`.
- Build: `cd /d/datn/datn_agent_skills/tools && PYTHONIOENCODING=utf-8 python build_slides.py`.
- Verify BẮT BUỘC bằng ảnh: PowerPoint COM export PNG (recipe guide §2) → Read PNG.
- Helper có sẵn: `title/bullets/image/images_row/img_slide/flow/table/note/_box`. Màu `HUST_BLUE/ACCENT/GREEN`.
- Gotchas: `RGBColor(r,g,b)` 3 tham số; kill `POWERPNT` trước build/export; không xoá slide template giữa chừng.

## Công việc

### 1. Chú thích f_cpu = 240 MHz cạnh số latency (nhỏ, làm trước)
Thêm cụm "(đo @ CPU 240 MHz)" hoặc tương đương vào các chỗ nêu 11,2 ms:
- Slide 23b `# --- 23b. Đánh đổi hiệu năng ---` (build_slides.py ~L476–481, bullet "11,2 ms « chu kỳ 500 ms").
- Slide 23a `# --- 23a. Ma trận nhầm lẫn ---` nếu có nêu latency.
- Cân nhắc slide 5 (đóng góp, L288) & slide bìa-signature `_box` L263 — chỉ thêm nếu không làm tràn chữ.
Chuẩn số vẫn theo báo cáo Ch5; chỉ thêm điều kiện đo, không đổi giá trị.

### 2. Enrich slide 16 "Depthwise Separable" bằng sơ đồ (visual-first)
Slide 16 (`build_slides.py` L395–406) hiện chỉ có bảng + bullet, thiếu sơ đồ.
- **Render** `fig:depthwise_separable` (TikZ **inline style**, không cần usecase styles) tại `Chuong/3_*.tex` **dòng 135–166** → PNG, theo recipe guide §11:
  1. Standalone `.tex` (`\documentclass[border=10pt]{standalone}` + `vietnam`+`tikz`+libs `arrows.meta,positioning,calc,shapes.geometric,fit,backgrounds`) → copy nguyên block `\begin{tikzpicture}…\end{tikzpicture}` (bỏ `\resizebox` nếu có).
  2. `pdflatex` (TinyTeX `/c/TinyTex/TinyTeX/bin/windows`) → `rungs -sDEVICE=png16m -r220` → `depthwise_separable.png` → copy vào `Hinhve/`.
  3. Chạy trong scratchpad, `cd <scratch> && …` cùng lệnh (cwd reset về d:\datn).
- Sửa slide 16: đổi sang layout **ảnh TRÊN + bảng/bullet DƯỚI**, hoặc tách 2 slide nếu chật (rule 1-ảnh nếu sơ đồ to). Ưu tiên `image(s, "depthwise_separable.png", ...)` phía trên, giữ bảng tăng tốc ESP-NN phía dưới.

### 3. Audit chính tả + bố cục (lượt soi toàn deck)
- Build → export toàn bộ ~55 PNG (recipe §2) → **Read lần lượt** từng `s##.png`.
- Soi: lỗi chính tả/dấu tiếng Việt (rule trường: tuyệt đối 0 lỗi), tràn chữ đè footer/logo, ảnh bị bé/méo, tiêu đề trắng-trong-band đúng, số khớp báo cáo.
- Ghi list lỗi → sửa trong `build_slides.py` → rebuild → re-verify các slide đã sửa.

### 4. Tách CHÍNH vs PHỤ LỤC + section divider + bấm giờ
- Thêm helper/slide **divider** (dùng `_box`/`title` nền HUST_BLUE) mở đầu mỗi khối: `NGHIÊN CỨU TinyML` · `THIẾT KẾ HỆ THỐNG` · `KẾT QUẢ` · `PHỤ LỤC (backup Q&A)`.
- Rà thứ tự để **trình chính 18–22 slide** (⭐ bất khả xâm phạm: bìa, agenda, 3 đóng góp, các pha ngã, xác nhận 2 pha, v30_optimize, kiến trúc tổng quan, kết quả confusion+mcu_evolution, kết luận). Slide chi tiết/phụ → sau divider PHỤ LỤC.
- Divider PHỤ LỤC phải rõ ràng để lúc trình lướt/bỏ qua, chỉ mở khi thầy hỏi.
- (Không cần cắt xoá slide — chỉ cần **trật tự + divider** để bấm giờ 12–15').

## Verification
- **Build:** `PYTHONIOENCODING=utf-8 python build_slides.py` in `Slides: N` không lỗi; PowerPoint COM mở + export đủ N PNG (không lỗi 0x80CB4404).
- **Ảnh:** Read `depthwise_separable.png` (rõ nét, không tràn viền) + slide 16 sau khi chèn (ảnh trên/bảng dưới, không đè footer).
- **Số:** `grep -nE "56 ?ms|36×|17 ?ms" build_slides.py` → rỗng; 11,2 ms/180×/97,5% giữ nguyên; chú thích 240 MHz xuất hiện đúng chỗ.
- **Chính tả:** Read hết ~55 PNG, không còn lỗi.
- **Cấu trúc:** đếm slide trình-chính giữa các divider ≤ ~22.

## Sau khi duyệt (implementation)
- **Copy plan chính thức** về `datn_agent_skills/plans/slide_finalize_depthwise_audit_divider.md` (quy ước CLAUDE.md §5).
- Cập nhật memory `slide-bao-ve-project` + guide `slide_bao_ve_implementation_guide.md` §STATUS với: 3 số latency đã reconcile (11,2/17/56 — điều kiện đo), f_cpu note, trạng thái depthwise/divider.
- Sửa `tinyml_model.md` L66: annotate 56,7 ms là "PSRAM/pre-cache-opt, đã thay bằng 11,2 ms @240 MHz SRAM trong báo cáo Ch5" để không ai dùng lại số cũ.
