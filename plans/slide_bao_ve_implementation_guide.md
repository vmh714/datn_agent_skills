# Implementation Guide — Slide bảo vệ DATN (cho model rẻ tiếp tục)

> Mục tiêu: một model/agent khác có thể **chỉnh/tiếp tục bộ slide bảo vệ** mà không phải dò lại context.
> Sinh viên: Vũ Mạnh Hưng · MSSV 20225198 · GVHD PGS.TS Nguyễn Hồng Quang · Đề tài: giám sát người già + phát hiện té ngã IoT + TinyML.
> Rule trình bày đầy đủ: memory `slide-presentation-rules`. Chiến lược tổng: `datn_agent_skills/plans/chien_luoc_nhat_hoi_dong_aiot03.md`.

> **📌 STATUS (cập nhật 2026-07-06, phiên audit+enrich):** Deck = **57 slide** (`.pptx` build OK, +4 section divider). Phiên này đã xong: (a) **4 section divider** nền xanh (Phần 1 Nghiên cứu / Phần 2 Thiết kế / Phần 3 Kết quả / Phụ lục) → tách CHÍNH↔PHỤ LỤC rõ; (b) **enrich slide 16 Depthwise** — render `fig:depthwise_separable` (TikZ) → `Hinhve/depthwise_separable.png`, layout ảnh-trên/bảng-dưới; (c) chú thích **f_cpu 240 MHz** cạnh latency (slide 23b); (d) sửa **double-bullet** slide Kết luận; (e) **AUDIT chính tả toàn deck: text slide SẠCH 0 lỗi**; (f) 🔴 **SỬA BUG ERD:** `erd.png` trước đây bị ghi đè nhầm bằng sơ đồ firmware → viết `tools/gen_erd.py` (matplotlib, từ `Hinhve/erd.mmd`) sinh lại ERD PostgreSQL 7 bảng đúng (ảnh hưởng CẢ báo cáo `fig:erd` — cần compile lại report). Backup cũ: `erd_OLD_firmware_diagram.bak.png`.
>
> **⚠️ SỐ LATENCY — CHỐT (user quyết cuối, 2026-07-06):** slide headline **17 ms @ 160 MHz** (cấu hình DEPLOY thực tế, `sdkconfig` = 160 MHz) + giữ **~180×** (tỷ số vs TCN, độc lập xung nhịp) + chú thích "benchmark 240 MHz đạt 11,2 ms" (khớp báo cáo Ch5 `tab:mcu_arch_compare`). Đã đổi ở slide 3/23b/28. **KHÔNG dùng 56,7 ms** (đo cũ PSRAM/pre-cache, lỗi thời). 3 số: 17 ms (deploy 160 MHz) · 11,2 ms (benchmark 240 MHz, báo cáo) · ~~56,7 ms~~ (bỏ). Chi tiết: `tinyml_model.md` §6.
> **📌 ERD:** `erd.png` giờ = **`erd_vip.png`** (user vẽ tay đẹp trên draw.io, crow's foot, **6 bảng — thiếu `verification_sessions`**). File `Hinhve/erd_full.mmd` = mermaid ĐỦ 7 bảng để import draw.io vẽ lại. `tools/gen_erd.py` (matplotlib) là bản backup sinh tự động nếu cần. Backup firmware-diagram cũ: `erd_OLD_firmware_diagram.bak.png`.
>
> **VIỆC CÒN LẠI:** (1) lỗi **bên trong ảnh draw.io/matplotlib** (regen ảnh nguồn, xem §13); (2) bấm giờ 12–15'; (3) slide Demo đã có ảnh thật, cân nhắc thêm video; (4) deploy backend tử tế; (5) **compile lại report** để cập nhật `fig:erd` mới. Xem §7 + §12 + §13.

## 0. Nguyên tắc BẤT BIẾN (đọc trước khi sửa)
- 🟢 **CONTENT-DRIVEN (mới, 2026-07-07):** NỘI DUNG slide nằm trong **`datn_agent_skills/tools/slides_content.md`** (nguồn duy nhất). `build_slides.py` giờ chỉ là **RENDERER** đọc file .md đó rồi dựng .pptx. → **Sửa nội dung** (tiêu đề, bullet, bảng, flow, caption, notes, thêm/bớt/đảo slide) **CHỈ sửa `slides_content.md`** rồi build lại. Chỉ đụng `build_slides.py` khi cần **kiểu layout mới** (thêm 1 `@block` type). Bản imperative cũ backup ở `build_slides_legacy_imperative.py.bak`. Cú pháp Markdown ghi ở đầu `slides_content.md`. Xem thêm `plans/slides_content_md_driven_build_plan.md`.
- **Toàn bộ slide sinh ra bằng script** `datn_agent_skills/tools/build_slides.py` (python-pptx). **KHÔNG sửa tay file .pptx** — mọi thay đổi phải sửa `slides_content.md` rồi build lại (build ghi đè cả file `.pptx`).
- **Visual-first:** MỌI slide phải có hình/sơ đồ/bảng. KHÔNG có slide toàn chữ. Ảnh TRÊN, chữ DƯỚI. Slide chỉ-ảnh thì chữ giải thích để trong **speaker notes** (`note(s, "...")`). Chữ là option.
- **KHÔNG bịa số.** Mọi số liệu model lấy từ **báo cáo Chương 5** (`report/Do_an_tot_nghiep_Vu_Manh_Hung/Chuong/5_Trien_khai_thuc_nghiem.tex`, bảng `tab:mcu_arch_compare` & `tab:model_comparison`). Số chuẩn: v30_optimize = **11,20 ms · acc 95,40% (firmware) / 95,33% (LSO float) · Fall recall 97,50% · F1-Trans 0,907 (kd2: 0,945) · arena 28,3KB · tflite 55,8KB**; TCN v30_tcn ≈ **2014 ms** → v30_optimize nhanh **~180×**; v30 baseline 5,1ms/F1-Trans 0,799.
- Shell: **Windows + PowerShell** (nối lệnh bằng `;`, không `&&`). Bash tool có sẵn cho POSIX.

## 1. File & vị trí
| Thứ | Đường dẫn |
|---|---|
| Script build | `datn_agent_skills/tools/build_slides.py` |
| Output .pptx | `report/Do_an_tot_nghiep_Vu_Manh_Hung/DATN_VuManhHung_slides.pptx` |
| Template HUST 4x3 | `report/Do_an_tot_nghiep_Vu_Manh_Hung/HUST_PPT_template_2022_blue_4x3.pptx` |
| Ảnh | `report/Do_an_tot_nghiep_Vu_Manh_Hung/Hinhve/*.png|jpg` |

## 2. Workflow build + verify (BẮT BUỘC verify bằng ảnh)
```bash
# 1) build (chạy ở thư mục tools; nếu PermissionError -> đóng file .pptx / kill POWERPNT trước)
cd /d/datn/datn_agent_skills/tools && python build_slides.py
```
```powershell
# 2) export .pptx -> PNG bằng PowerPoint COM để MẮT NGƯỜI xem (đừng đoán "hình có hiện không")
Get-Process POWERPNT -ErrorAction SilentlyContinue | Stop-Process -Force; Start-Sleep 2
$out="C:\Users\vuman\AppData\Local\Temp\claude\...\scratchpad\slides_png"  # thư mục scratchpad phiên
if (Test-Path $out){Remove-Item $out -Recurse -Force}; New-Item -ItemType Directory $out | Out-Null
$pp=New-Object -ComObject PowerPoint.Application
$pres=$pp.Presentations.Open("D:\datn\report\Do_an_tot_nghiep_Vu_Manh_Hung\DATN_VuManhHung_slides.pptx",$true,$false,$false)
$pres.Export($out,"PNG",1280,960); $pres.Close(); $pp.Quit()
# đổi tên ASCII (tên gốc "Bản chiếu N.PNG" có dấu -> Read tool lỗi)
Get-ChildItem $out -Filter *.PNG | %{ $n=$_.BaseName -replace '[^0-9]',''; Rename-Item $_.FullName ("s{0:D2}.png" -f [int]$n) }
```
Rồi dùng **Read tool** mở vài `s##.png` để kiểm tra bố cục/tràn chữ/ảnh.

## 3. GOTCHAS đã vấp (đừng lặp lại)
1. **RGBColor cần 3 tham số**: `RGBColor(0xDD,0xEC,0xD9)` — KHÔNG `RGBColor(0xDDECD9)` (crash).
2. **`_as_emu`/width**: `Inches(x)` là `Length` (không phải `Emu`) → dùng `isinstance(v, Length)` để nhận diện, nếu không `Inches(Inches(x))` cho width 5 triệu inch → **PowerPoint không mở được file** (python-pptx vẫn đọc). Đã có helper `_as_emu` đúng.
3. **Strip slide template**: giữ slide bìa (index 2 = slide #3 template có sẵn thiết kế). Muốn không trùng part `slide3.xml` (lỗi 0x80CB4404 khi PowerPoint mở): **KHÔNG xoá slide template lúc đầu**; build hết slide mới **rồi cuối script mới drop_rel + remove** 12 slide thừa và `insert(0)` đưa bìa lên đầu (xem cuối `build_slides.py`).
4. **Title**: dùng title placeholder của template (chữ **trắng** trong band xanh) — set `RGBColor(0xFF,0xFF,0xFF)`. Tự vẽ textbox tiêu đề sẽ đè band.
5. **Overlap footer**: bullet đặt `top` quá thấp (>5.6 với nhiều dòng) sẽ đè logo HUST/line đỏ. Với slide sơ đồ dày → để **ảnh lớn + chữ vào notes** (dùng `img_slide(...)`).
6. **Encoding**: in tiếng Việt ra console lỗi cp1252 → `PYTHONIOENCODING=utf-8` hoặc ghi ra file utf-8 rồi Read.
7. **Lock file**: PowerPoint COM hay giữ file → `Stop-Process POWERPNT -Force` trước khi build/ export lại.

## 4. Helper trong script (dùng lại, đừng viết mới)
> ⚠️ Các helper dưới đây là **cơ chế render**; khi SỬA NỘI DUNG bạn KHÔNG gọi trực tiếp mà khai báo qua block trong `slides_content.md`. Ánh xạ block → helper:
> `@bullets`→`bullets` · `@image`→`image` · `@images-row`→`images_row` · `@table`→`table` · `@flow`→`flow` · `@banner`→`_box` · `@notes`→`note` · `@heading`→`_heading` · slide `## divider`→`divider` · slide `## cover`→bìa template. Cú pháp & thuộc tính đầy đủ ở đầu `slides_content.md`.
- `title(s, text)` — tiêu đề (tự trắng-trong-band + dọn placeholder rỗng).
- `bullets(s, items, top=, size=, width=)` — bullet; item dạng `"text"` hoặc `("text", level)` (level 1 = sub-bullet). Chú ý `top` để không đè footer (giữ text kết thúc trước ~6.9").
- `image(s, name, left, top, max_w, max_h, caption=)` — chèn ảnh, tự fit + căn giữa.
- `images_row(s, [names], top=, height=, total_w=, left0=, captions=)` — hàng ảnh căn giữa (ảnh trên).
- `img_slide(title, name, img_h=, img_w=, left=, notes=, caption=)` — **slide ảnh lớn, chữ vào notes** (dùng cho sơ đồ hệ thống).
- `flow(s, [steps], top, box_h=, total_w=, horizontal=True/False, fills=[...])` — **sơ đồ khối** (pipeline ngang / funnel dọc) nối bằng mũi tên đỏ. Dùng cho slide khái niệm không có ảnh.
- `table(s, data, left, top, width, height, fs=)` — bảng native (header xanh).
- `note(s, text)` — ghi speaker notes.
- Màu: `HUST_BLUE`, `ACCENT` (đỏ), `GREEN`.

## 5. Cấu trúc slide (~38 slide, research-forward hybrid)
> ⚠️ **Nguồn chuẩn về cấu trúc = chính `build_slides.py`** (mỗi slide có comment `# --- N. Tên ---`). Danh sách dưới chỉ để định hướng; đừng tin tuyệt đối.

Khối thứ tự: **Bìa → Agenda → Thiết bị thương mại → Đặt vấn đề (flow Cloud✗/Edge✓) → 3 đóng góp** → **[NGHIÊN CỨU TinyML]** (SisFall+tiền xử lý flow · phân bố accel · phân bố gyro · windowing · nhãn 5 lớp bảng · mất cân bằng flow · các pha ngã · xác nhận 2 pha flow · chống báo giả 4 tầng funnel · bài toán TinyML · 3 thế hệ · depthwise bảng · v30_optimize · so sánh bảng · **confusion matrix** · **mcu_evolution** · KFold bảng) → **[HỆ THỐNG]** (kiến trúc tổng quan `arch` · MQTT `mqtt_architechture` · **firmware pkg `fw_pkg`** · FSM `fsm` · backend `erd` · hybrid alert `sync` · **dashboard** · **global_alert** · **device_vitals**) → **[KẾT QUẢ]** (thiết bị ảnh · **swagger API** · Demo · Thảo luận · Kết luận · Cảm ơn) → **[PHỤ LỤC]** (SisFall bảng · PPPoS).

## 6. ⚠️ RULE 1-ẢNH đã áp dụng (giữ khi thêm slide mới)
**Biểu đồ / ảnh UI web / ảnh API = MỖI SLIDE 1 ẢNH.** Đã tách: accel|gyro (2), arch|mqtt (2), dashboard|global_alert|device_vitals (3), confusion|mcu_evolution (2), device|swagger (2). **Ảnh minh hoạ** (sản phẩm thương mại, ESP32/MPU, ảnh đeo) → nhiều ảnh/slide OK.

## 7. Task còn lại (cho model rẻ)
1. **AUDIT SỐ (ưu tiên cao):** đã có **regression 3 lần** ghi sai "56 ms" & "~36×". Chạy `grep -nE "56 ?ms|36×|36 lần" build_slides.py` → phải là **11,2 ms** & **~180×** ở MỌI chỗ (khớp báo cáo Chương 5 & slide kết quả). Rà thêm mọi số khác so với `5_Trien_khai_thuc_nghiem.tex`.
2. **Chính tả:** mở lần lượt 38 PNG, soi kỹ (rule trường: tuyệt đối không lỗi chính tả). Chú ý dấu tiếng Việt.
3. **Slide Demo:** đang là ô placeholder `[ Demo Video / Live ]` → thay bằng ảnh/video thật khi có (hoặc ảnh chuỗi ngã→còi→dashboard).
4. **Bấm giờ:** trình thử 12–15 phút (nhiều slide ảnh/web lướt nhanh; slide nghiên cứu nói kỹ).
5. **(Tuỳ chọn) Thêm slide phụ lục backup cho Q&A:** bảng hyperparameters (LR/batch/optimizer), công thức metrics, cấu hình `fall_threshold`/`cooldown`/`confirm_window`, PCNT lấy mẫu, KD ablation. Mỗi cái 1 slide, để trong khối Phụ lục.
6. **Deploy backend tử tế** (rời Render free) — xem chiến lược `chien_luoc_nhat_hoi_dong_aiot03.md` §6. Chặn câu hỏi "chạy 24/7 ở đâu" của thầy app.
7. **Khi sửa 1 slide:** mở `slides_content.md` → tìm khối `## content | <Tên slide>` → sửa các block (`@bullets`/`@image`/…) → `python build_slides.py` → export PNG (§2) → Read kiểm tra. (KHÔNG sửa `build_slides.py` trừ khi cần layout/block type mới.)

## 8. Gotcha thêm (mới)
- **`gen_fw_pkg.py` đã đổi sang matplotlib** (tọa độ cố định) thay PlantUML/Graphviz — vì auto-route hay đè mũi tên. Cần `pip install matplotlib` (không cần mạng). Sửa vị trí hộp trong dict `boxes`, mũi tên qua hàm `arrow(a,b,label,color,rad,ldx,ldy)`. Chạy `python gen_fw_pkg.py` rồi Read `Hinhve/fw_pkg.png`.
- Build in tiếng Việt lỗi cp1252 → chạy `PYTHONIOENCODING=utf-8 python build_slides.py`.

## 9. Tài liệu SisFall (phục vụ Q&A / phụ lục)
- Readme dataset: `sis_fall_har_and_fall-detection_trainning/Readme.txt` (đối tượng, cảm biến ADXL345/MMA8451Q/ITG3200, D01–D19/F01–F15, 4.510 file).
- **Bài báo gốc**: `report/science_thesis_md/SisFall_A_Fall_and_Movement_Dataset_parsed.md`.
- Điểm nhấn Q&A (đã đưa vào slide phụ lục SisFall): chỉ **SE06** (chuyên Judo) mô phỏng ngã → dữ liệu ngã thiên lệch người trẻ; người già không làm D06/D13/D18/D19.

## 11. TODO — Bổ sung biểu đồ Phân tích/Thiết kế (SE) — user yêu cầu
Nguồn: tất cả là **TikZ trong `Chuong/4_1_Phan_tich_yeu_cau.tex`** (CHƯA có PNG trong `Hinhve/`).

**Phân bổ (theo ý user):**
| Biểu đồ | Anchor (fig label) | Đặt ở |
|---|---|---|
| **Use-case TỔNG QUÁT** (7 ca sử dụng + actors) | `fig:use_case_tongquat` | **SLIDE CHÍNH** (khối [Hệ thống], hợp chuẩn trường "Phân tích chức năng") |
| **Activity diagram — Luồng xử lý sự cố té ngã** | `fig:activity_fall` | **SLIDE CHÍNH (cân nhắc)** — user OK vì đây là quy trình nghiệp vụ (y tá nhận→tới hiện trường→Resolve), KHÁC với FSM xác nhận kỹ thuật & sync đã có. ⚠️ Kiểm tra tránh trùng lặp với slide "xác nhận ngã 2 pha (flow)" / "hybrid alert (sync)". Nếu thấy trùng → đẩy xuống phụ lục. |
| **4 Use-case PHÂN RÃ**: Giám sát realtime · Xử lý cảnh báo ngã · Gán thiết bị · Xem thống kê vận động | (4 figure liền sau trong 4_1) | **PHỤ LỤC** (mỗi cái 1 slide — theo rule 1-ảnh) |
| Các activity/sequence khác nếu có trong Ch4 | — | **PHỤ LỤC** |

**Cách lấy PNG (2 lựa chọn, ưu tiên (a) cho khớp báo cáo):**
- **(a) Render từ TikZ báo cáo:** style `usecase`/`ucsystem`/`ucactorpic` định nghĩa ở **preamble `20225198_VuManhHung.tex`**. Làm standalone wrapper (`\documentclass{standalone}` + copy các `\usetikzlibrary` + `\tikzset{usecase/...}` từ preamble + `\input` đoạn tikzpicture của figure) → `pdflatex` (TinyTeX ở `/c/TinyTex/TinyTeX/bin/windows/`) → PDF → `rungs -sDEVICE=png16m -r150` ra PNG → trim viền (PIL/ImageMagick). HOẶC compile cả report rồi rasterize đúng trang figure (recipe ở `architecture/report.md` §2).
- **(b) Vẽ lại bằng helper** `flow()`/`_box()` trong `build_slides.py`: các use-case phân rã là chuỗi oval dọc → `flow(..., horizontal=False)`; activity ngã là luồng có nhánh → dùng `_box` + mũi tên. Nhanh, không cần LaTeX, nhưng kém "khớp báo cáo".

**Chèn slide:** dùng `img_slide(title, "usecase_tongquat.png", img_h=5.7, notes=...)` cho slide chính; phụ lục tương tự. Đặt PNG mới vào `Hinhve/`. Nhớ **1 biểu đồ / slide**.

**✅ RECIPE RENDER TIKZ ĐÃ CHẠY OK (dùng cho use-case/activity):** đã render thành công `fig:svc_ai_fsm` → `Hinhve/svc_ai_fsm.png` (đã thay vào slide "xác nhận ngã 2 pha"). Cách:
1. Tạo file standalone `.tex`:
```latex
\documentclass[border=10pt]{standalone}
\usepackage[utf8]{vietnam}      % font tiếng Việt (giống report)
\usepackage{amsmath}\usepackage{tikz}
\usetikzlibrary{arrows.meta, positioning, calc, shapes.geometric, fit, backgrounds}
\begin{document}
<COPY nguyên block \begin{tikzpicture}...\end{tikzpicture} từ report, BỎ \resizebox>
\end{document}
```
2. Compile + rasterize (TinyTeX ở `/c/TinyTex/TinyTeX/bin/windows`):
```bash
export PATH="/c/TinyTex/TinyTeX/bin/windows:$PATH"
pdflatex -interaction=nonstopmode -halt-on-error fig.tex
rungs -sDEVICE=png16m -r220 -dNOPAUSE -dBATCH -o fig.png fig.pdf
cp fig.png <REPORT>/Hinhve/
```
- Nếu figure dùng style `usecase`/`ucsystem`/`ucactorpic` (use-case) → copy thêm phần `\tikzset{...}` định nghĩa các style đó từ **preamble `20225198_VuManhHung.tex`** vào file standalone (FSM thì không cần vì style khai báo inline).
- ⚠️ Chạy trong thư mục scratchpad; `cd` bị reset về `d:\datn` sau mỗi lệnh nên `cd <scratch> && ...` trong CÙNG lệnh.

## 12. KHO HÌNH BÁO CÁO — dùng được mà CHƯA vào slide (quét 2026-07-06)
> Kiểm tra trùng với deck hiện tại trước khi thêm (model rẻ đã thêm khá nhiều). Anchor = file `Chuong/*.tex`.

**A. TikZ cần RENDER (dùng recipe §9/§11):**
| Figure (label) | Vị trí | Đề xuất đặt |
|---|---|---|
| `fig:depthwise_separable` | 3_Phuong ~L167 | **CHÍNH** — enrich slide "Depthwise Separable" (đang chỉ có bảng) |
| `fig:use_case_tongquat` | 4_1 ~L47 | **CHÍNH** (Phân tích chức năng) |
| `fig:activity_fall` (Activity luồng xử lý ngã) | 4_1 ~L212 | **CHÍNH (cân nhắc)** — xem §11, tránh trùng FSM/sync |
| `fig:use_case_giam_sat / xu_ly / gan_thiet_bi / thong_ke` (4 use-case phân rã) | 4_1 | **PHỤ LỤC** (1/slide) |
| `fig:pedometer_pipeline` | 3_Phuong ~L413 | **PHỤ LỤC** (đếm bước HAR-gated) |
| `fig:transport_autodetect` (auto-detect WiFi/4G, D-026) | 3_Phuong ~L490 | **PHỤ LỤC** (firmware) |
| Fig "đối chiếu 2 tuyến truyền IMU 100Hz" | 3_Phuong ~L445 | PHỤ LỤC (nếu cần) |
| ✅ ĐÃ render: `fig:svc_ai_fsm` (svc_ai_fsm.png, đã vào slide) · `fig:v30opt_architecture` (v30opt_architecture.png) · fw_pkg (matplotlib) | — | — |

**B. PNG SẴN trong `Hinhve/` chưa/ít dùng (chèn thẳng, 1-ảnh/slide):**
- `dual_database.png` (report comment nhưng PNG có) → slide Backend dual-DB.
- `nextjs_architecture.png` (report comment nhưng PNG có) → slide Frontend/Web.
- UI screenshots: `device_history.png` · `device_manage.png` · `weares_manage.png` · `alert_history.png` · `data_collection.png` → **PHỤ LỤC**, mỗi cái 1 slide.
- `a7680c_front/back.jpeg` → minh hoạ module 4G (ảnh minh hoạ → nhiều/slide OK).

## 10. Định nghĩa "done"
- Build không lỗi (`Slides: N`), PowerPoint COM mở + export đủ PNG. **Deck hiện 57 slide** (4 divider tách CHÍNH↔PHỤ LỤC).
- Mọi slide có hình; **biểu đồ/UI/API 1-ảnh-1-slide**; không tràn chữ đè footer.
- Số khớp báo cáo (11,2 ms / ~180× / 97,5%); không lỗi chính tả; bìa giữ đúng MSSV 20225198.

## 13. LỖI BÊN TRONG ẢNH (audit 2026-07-06) — cần regen ẢNH NGUỒN (không sửa được từ build_slides.py)
> Text slide đã sạch 100%. Các lỗi dưới nằm TRONG file ảnh (draw.io export / matplotlib), phải sửa ở nguồn rồi thay PNG.
- ✅ **ĐÃ SỬA:** `erd.png` (là sơ đồ firmware, không phải ERD) → `tools/gen_erd.py` sinh lại từ `Hinhve/erd.mmd`. Nhớ **compile lại report** để `fig:erd` cập nhật.
- 🔲 `mqtt_architechture.png` (slide 18b): "**Pus:**"→"Pub:", "**RESTfull**"→"RESTful", "**Qos 0**"→"QoS 0" (lệch hoa/thường với "QoS 1"). Nguồn: draw.io.
- 🔲 `arch.png` (slide 18a): "**Subcribe**"→"Subscribe" (2 chỗ). Nguồn: draw.io.
- 🔲 `fsm.png` (slide 19): "**STATE_STREAMMING**" — nghi thừa M; ĐỐI CHIẾU enum firmware thật (`svc`/`sys_manager`) trước khi sửa (nếu code đúng tên này thì giữ, nhưng nên đổi cả code cho đúng English "STREAMING").
- 🔲 `mcu_evolution.png` (slide 23b): tiêu đề chart có artifact LaTeX "**\&**" ("Đánh đổi Hiệu năng \& Tiến hóa") → sửa ở script matplotlib sinh ảnh (bỏ `\&`, dùng "&").
- ℹ️ Charts `accel_distribution_2x2.png` / `gyro_distribution_2x2.png` / `har_windows.png`: nhãn tiếng Việt KHÔNG dấu (matplotlib thiếu font Việt) — chấp nhận được, muốn đẹp thì set font hỗ trợ Unicode khi regen.
