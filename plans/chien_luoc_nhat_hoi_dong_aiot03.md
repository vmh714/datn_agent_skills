# Chiến lược "Đứng nhất Hội đồng AIoT 03" — Đề tài #1 (Fall Detection Eldercare IoT + TinyML)

> ⚠️ Khi được duyệt, **bước 0** thực thi: copy file này về `datn_agent_skills/plans/chien_luoc_nhat_hoi_dong_aiot03.md` (quy ước CLAUDE.md).

## Context — mục tiêu & scope đã chốt

Hội đồng AIoT 03: **3 thầy cân bằng eng↔research** (1 thầy vừa app vừa research = chủ tịch/quyết định, 1 thầy thuần app, 1 thầy thuần research). Bạn **trình đầu tiên**. Đề của bạn là đề **duy nhất mạnh cả research (TinyML on-MCU) lẫn sản phẩm production full-stack** → phải để cả hai lộ rõ trong 12-15 phút.

**Scope đã chốt (do thời gian có hạn):**
- ✅ Tập trung: **slide bảo vệ + vá docs/report + luyện phản biện** + **deploy backend tử tế**.
- ✅ Firmware: **chỉ thêm còi buzzer** (demo edge), đơn giản. **BỎ** nút silence + SMS fallback (edge-case, không đủ thời gian).
- Deliverable chính lần này = **bộ slide 15-18 trang** theo hướng dẫn trường + checklist phản biện.

---

## 1. Đối thủ & định vị (đã có intel thực địa)

| # | Đề | Đe dọa | Cách vượt |
|---|----|--------|-----------|
| **9** Robot giao hàng (bạn thân, robot xịn) | **CAO ở trục demo** | Robot = 1 cú demo wow nhưng **nhẹ research định lượng**. Đánh ở **research rigor (K-fold, ablation, on-chip metrics) + ý nghĩa cứu mạng người già**. Không đua độ "wow" cơ khí. |
| **8** Cháy — ESP32-CAM bắn ảnh qua WiFi, inference cloud | TRUNG (có thuốc trị) | **"Edge giả"**: tốn pin, phụ thuộc WiFi, AI trên cloud. Bạn thắng tuyệt đối ở **pin/offline/on-device**. Dùng làm phản-ví-dụ ngầm (device-class). |
| **4/6** Drone RF & định vị vệ tinh — **cùng lab thầy chủ tịch** | TRUNG (**chính trị**) | Thầy chủ tịch (người quyết định) có tình cảm mảng RF. **KHÔNG đua RF**. Thắng thầy bằng **độ hoàn chỉnh end-to-end + edge-AI rigor** (đúng gu dual-depth). Q&A đụng RF → tôn trọng, không gạt phăng. |
| **5** Không khí + dự báo · **11** bệnh cây · **3** ROV (làm nhóm) · **10/7/2/12** | THẤP-TRUNG | Thiếu 1-2 trục. #3 làm nhóm → đóng góp cá nhân loãng; bạn nhấn "one-man full-stack + firmware + ML". |

**Con đường thắng:** không đề nào **cùng lúc** phủ cả 3: (a) edge-AI thật trên MCU + (b) sản phẩm production full-stack + (c) research định lượng. #9 thiếu (a)(c); #8 thiếu (a); #4/#6 thiếu (b); #5 thiếu (a)(b). **Bạn phủ cả ba.**

**⭐ Lợi thế NGƯỜI ĐẦU TIÊN — cắm thước đo:** đi đầu = đặt tiêu chuẩn "edge xịn" cho cả buổi; mọi đề WiFi-cloud sau bạn (nhất #8) tự bị so kém mà bạn không cần chê ai. Ba đòn khắc sâu:
1. **Câu chữ ký lặp 3 lần** (mở–giữa–kết): *"AI chạy thật trên chip 56ms, không cần Cloud, mất mạng vẫn phát hiện ngã."*
2. **Khoảnh khắc còi:** demo giả ngã → **còi hú tại thiết bị** (§4) → âm thanh khắc vào trí nhớ, pre-empt mọi đề phụ thuộc mạng.
3. **1 slide device-class yardstick** (MCU vs Camera→Cloud vs Pi/Jetson) — không nêu tên ai.

## 2. Thông điệp lõi & 3 đóng góp (thầy research đọc đầu tiên)

- **One-liner:** "Fall detection **chạy on-device trên ESP32-S3 (56ms, INT8, không cần Cloud)**, tích hợp full-stack tới dashboard cảnh báo realtime — 24/7, mất mạng vẫn báo."
- **3 đóng góp (đặt thành 1 slide bullet):**
  1. **Sơ đồ nhãn Trans/Idle** giải nhập nhằng chuyển tư thế người già (Trans F1 0.799→**0.945** trên chip).
  2. **Kiến trúc CNN tối ưu ESP-NN (head giữ-trục-thời-gian):** nhanh **~36×** teacher TCN mà **Fall recall 97.5% ≥ teacher**; chứng minh **KD không giúp** — thắng lợi từ *kiến trúc*, không phải distillation (điểm khách quan khoa học).
  3. **Hệ thống IoT end-to-end production:** firmware C event-driven+FSM, MQTT/TLS, dual-DB (Postgres+InfluxDB), multi-tenancy, OTA.

## 3. ⭐ BỘ SLIDE — deliverable chính (~28 trang core + phụ lục)

Template **HUST 4x3 blue** (`report/Do_an_tot_nghiep_Vu_Manh_Hung/HUST_PPT_template_2022_blue_4x3.pptx` — user tải về). **Không copy văn báo cáo; không theo chương hồi; mỗi slide 1 ý + hình/biểu đồ + số liệu.** User đồng ý "nướng tới ~30 slide" để đủ chỗ đào sâu **nhãn + các pha cú ngã**. Ảnh lấy từ `Hinhve/` (đã kiểm kê, tên thật bên dưới). Cân đối research (slide 6-17,23-24) ↔ app (18-22,25) đúng yêu cầu "khối lượng tương đương".

**Thông tin cá nhân (từ `Bia.tex`):** Vũ Mạnh Hưng · hung.vm225198@sis.hust.edu.vn · GVHD **PGS. TS. Nguyễn Hồng Quang** · Khoa/Trường: Kỹ thuật máy tính — Trường CNTT&TT, ĐHBK Hà Nội · 06/2026.

| # | Slide | Nội dung cốt lõi | Hình (`Hinhve/`) |
|---|-------|------------------|------------------|
| 1 | **Bìa** (gen) | Tên đề tài + thông tin cá nhân ở trên | logo |
| 2 | **Nội dung trình bày** | Agenda 6 mục | — |
| 3 | **Đặt vấn đề & mục tiêu** | Dân số già, ngã nguy hiểm; hạn chế Cloud (trễ/mất mạng/riêng tư) → wearable edge-AI. **Cắm câu chữ ký.** | `hovding.jpg`,`tangobelt.jpg` (thị trường) |
| 4 | **Nghiên cứu liên quan → Research Gap** | Airbag wearable đắt/1 chiều; Cloud-AI trễ; TinyML xử lý nhãn động (Trans) kém → gap | `hipair.jpg`,`alpinestars.jpg` |
| 5 | **3 Đóng góp chính** | §2 bullet | icon |
| — | *— KHỐI DỮ LIỆU & NHÃN (research) —* | | |
| 6 | **SisFall & tiền xử lý** | Downsample 200→100Hz (Nyquist), chuẩn hóa [-1,1] cho INT8 | — |
| 7 | **Phân tích phân bố → chọn thang đo** | Percentile → ±8g (P99.9≈5.2g) & **±500dps** (bug gyro rad/s làm "mù" con quay ở v25) | `accel_distribution_2x2.png`,`gyro_distribution_2x2.png` |
| 8 | **Cắt cửa sổ & tăng cường** | Event-based windowing (RMS gyro>20dps) vs sliding (Walk/Run); augment Trans ×0.9/1.1 | `har_windows.png` |
| 9 | **⭐ Chiến lược 5 nhãn** | 4 nhãn→báo giả khi chuyển tư thế → thêm **Trans**; thử 6 nhãn→gộp Idle. Bảng ánh xạ Walk/Run/Idle/Trans/Fall | bảng ánh xạ nhãn |
| 10 | **Xử lý mất cân bằng** | class_weight balanced ×3 Fall, label smoothing 0.1, **threshold θ=0.25** (ưu tiên Recall) | — |
| — | *— KHỐI CÁC PHA CÚ NGÃ (research, user nhấn mạnh) —* | | |
| 11 | **⭐ Các pha của cú ngã** | Pre-impact → free-fall (SVM<0.6g) → **impact (SVM>2.5g)** → post-impact nằm → recovery | **`fall_phases.png`** + eq. SVM |
| 12 | **⭐ Xác nhận ngã 2 pha (Post-Impact Confirmation FSM)** | ML = trigger nhạy (giữ Recall) → CONFIRMING quan sát Idle+Roll nằm trong `fall_confirm_window` → CONFIRMED/ABORT | sơ đồ FSM `svc_ai` |
| 13 | **Chống báo giả 4 tầng** | (1) Pre-impact posture gating → (2) fall_threshold → (3) Post-impact FSM → (4) cooldown; cả 3 tham số cấu hình từ xa | sơ đồ tầng |
| — | *— KHỐI MÔ HÌNH TINYML (research) —* | | |
| 14 | **Bài toán TinyML** | 2 ràng buộc đối nghịch (biểu đạt ↔ tài nguyên INT8); LSTM lượng tử hóa kém | — |
| 15 | **3 thế hệ kiến trúc** | CNN-LSTM → TCN (v8-22, acc cao nhưng >2s) → CNN thuần ESP-NN (<20ms) | `model_evolution.png` |
| 16 | **Depthwise Separable + ESP-NN** | Tách depthwise+pointwise 1×1; bảng tăng tốc: SepConv 6.3×, pointwise 14.2×, relu6 11.5× | sơ đồ separable + bảng |
| 17 | **⭐ Kiến trúc v30_optimize** | Head **GAP+GMP+Flatten giữ trục thời gian** (26.629 params); KD ablation → thắng từ *kiến trúc* không phải distillation | sơ đồ khối v30_optimize |
| — | *— KHỐI THIẾT KẾ HỆ THỐNG (app) —* | | |
| 18 | **Kiến trúc tổng quan** | Edge(ESP32-S3)→MQTT/TLS→Backend(FastAPI dual-DB)→Dashboard(Next.js) + giao thức | `arch.png`,`mqtt_architechture.png` |
| 19 | **Firmware event-driven + FSM** | Kiến trúc phân lớp, FSM hệ thống, PCNT lấy mẫu 100Hz jitter<1µs | `fsm.png` |
| 20 | **Backend & CSDL** | Dual-DB (Postgres metadata + InfluxDB time-series), MQTT bridge, multi-tenant, JWT+MQTTS | `erd.png` |
| 21 | **Đồng bộ cảnh báo lai** | Hybrid alert sync (MQTT tức thời + DB bền vững + fallback resolve) | `sync.png` |
| 22 | **Dashboard realtime + Use-case** | Use-case tổng quan + ảnh UI giám sát/cảnh báo/timeline | `dashboard.png`,`global_fall_alert.png`,`device_vitals.png` |
| — | *— KHỐI KẾT QUẢ —* | | |
| 23 | **⭐ Kết quả model (bảng vàng)** | TCN vs CNN v30_optimize/kd2 **INT8 trên chip**: acc 95.4%, **Fall recall 97.5%**, Trans F1 0.907→**0.945**, **11.2ms**, arena 28.3KB | `confusion_matrix_v30_opt_espnn_ON_sram_firmware.png`,`mcu_evolution.png` |
| 24 | **Kiểm định chéo dân số (KFold v6)** | 5 kịch bản Leave-Subjects-Out; S5 acc 96.3%/Trans F1 0.92/Fall recall 99.5%; giới hạn data Fall người già | bảng KFold |
| 25 | **Kết quả thử nghiệm hệ thống** | Kịch bản: ngã→cảnh báo <2s; edge chạy offline; OTA. Thiết bị thật | `hardware_picture.jpg`,`device_weared.jpg`,`fastapi_swagger.png` |
| — | *— PHẦN CUỐI —* | | |
| 26 | **Demo** | Video/live: ngã→**còi hú**→dashboard đỏ; rút mạng còi vẫn hú | video (§4) |
| 27 | **Thảo luận & hạn chế** | S1 thiếu data Fall người già; S4 precision 74.6%; Light-Sleep/pin chưa xong | — |
| 28 | **Kết luận & hướng phát triển** | Bám 3 đóng góp + số liệu | — |
| 29 | **Cảm ơn** | Cảm ơn hội đồng | — |
| PL | **Phụ lục** | Hyperparameters, công thức metrics, pedometer HAR-gated, PPPoS, class diagram | `pppos_stack.png`, sơ đồ pedometer |

> ⚠️ 28 slide > 18 trang trường khuyến nghị → khi bấm giờ nếu quá 15': gộp/cắt các slide có dấu thường (6,10,13,14,16,19,21,24) vào Phụ lục, giữ 18 slide "xương sống" (đánh ⭐ + bìa/agenda/đóng góp/kiến trúc/kết quả/kết luận). Slide ⭐ là bất khả xâm phạm.

## 3b. Cách build file .pptx (kỹ thuật)

- **Công cụ:** `python-pptx` (thao tác trực tiếp file .pptx, giữ nguyên master/layout HUST). **Prereq 1:** `pip install python-pptx` (chưa cài — cần chạy khi thực thi). **Prereq 2:** user **tải template** về đúng path trên.
- **Cách làm:** mở template bằng `Presentation(template_path)`, dùng các **slide layout** có sẵn của template (Title, Title+Content...) để `add_slide`, đổ text (title/bullet) + chèn ảnh từ `Hinhve/` (`add_picture`), giữ brand xanh HUST. Script build đặt ở `datn_agent_skills/tools/build_slides.py`, ảnh tham chiếu tương đối tới `Hinhve/`.
- **Một số hình chưa có ảnh PNG rời** (sơ đồ FSM `svc_ai`, sơ đồ khối v30_optimize, separable conv, bảng ESP-NN) hiện là **TikZ trong report** → hoặc (a) render riêng từng hình ra PNG bằng `pdflatex`+`rungs` (đã có TinyTeX) rồi chèn, hoặc (b) vẽ lại bằng shapes trong pptx. **Ưu tiên (a)** để khớp báo cáo.
- **Output:** `report/Do_an_tot_nghiep_Vu_Manh_Hung/DATN_VuManhHung_slides.pptx`. Sau khi gen, mình rasterize vài slide ra PNG để bạn xem nhanh (như cách verify hình LaTeX).

## 4. Demo — chỉ còi buzzer (đơn giản, chắc kèo)

- **Còi active** (KY-012) trên **GPIO2/D1**: hook `AI_EVT_FALL_DETECTED` ([svc_ai.c:242](firmware/components/svc_ai/svc_ai.c#L242), bắn độc lập mạng) → `drv_buzzer_alarm_start()` + `esp_timer` tự tắt sau ~10s. Component `drv_buzzer/` + init ở [app_main.c:47](firmware/main/app_main.c#L47), handler ở `sys_manager`. (Chi tiết đủ để code khi bắt tay.)
- **Kịch bản demo:** đeo → giả ngã → **còi hú + dashboard đỏ <2s**; nếu tiện, **rút mạng rồi giả ngã → còi VẪN hú** (chứng minh edge độc lập Cloud).
- **Chống sập bắt buộc:** **video quay sẵn** toàn luồng; giữ ấm backend trước 5'; `tools/fake_device.py` để bơm dữ liệu nếu thiết bị lỗi.
- Q&A pin: còi chỉ hút dòng lúc báo động (hiếm) → không ảnh hưởng pin.

## 5. Q&A phản biện theo từng thầy

**Thầy research:** *LSTM/Transformer?* → ESP-NN không tăng tốc LSTM/dilated → 2000ms, không realtime; đã thử TCN teacher 2058ms không deploy nổi. · *Đóng góp vs SisFall gốc?* → nhãn Trans/Idle + eval subject-independent + Fall recall **trên chip** 97.5%. · *KD có tác dụng?* → trung thực: **không thắng baseline**, ablation α=0.3/0.5/1.0 → thắng nhờ *kiến trúc*. · *fall_threshold 0.25?* → ưu tiên recall (bỏ sót ngã > báo nhầm).

**Thầy app:** *Deploy ở đâu, chạy 24/7?* → **câu nguy hiểm** (đang tạm bợ Render) → phải vá trước (§6): trả lời "chạy trên [domain] có HTTPS, DB managed". · *Bảo mật dữ liệu y tế?* → MQTTS 8883 + JWT + device auth + multi-tenant org_id. · *Pin bao lâu?* → số đo duty cycle (infer ~5-6%). · *Khác gì Apple Watch?* → độc lập Cloud, chi phí thấp, multi-tenant cho viện dưỡng lão.

**Thầy chủ tịch (app+research, lab RF):** *Điểm nghẽn hệ thống, scale 100 thiết bị?* → MQTT broker + InfluxDB time-series + backend async; thành thật giới hạn + hướng scale. · Nếu hỏi *sensor fusion/Kalman kiểu định vị?* → thừa nhận hướng hay, giải thích ràng buộc ESP-NN/realtime khiến chọn CNN.

## 6. Vá docs/report + deploy (song song slide)

- **Deploy tử tế (ưu tiên — chặn câu hỏi thầy app):** rời Render free (cold-start/ngủ đông) → VPS (Oracle free/DO) chạy Docker compose (FastAPI+Postgres+InfluxDB+broker) **+ domain + HTTPS**, hoặc tối thiểu Render paid giữ ấm. Dùng skill `iot-testing-deployment` (Dockerize). Mục tiêu: hôm bảo vệ mở URL lên <2s.
- **Report (theo `thesis_writing_plan.md`):** Abstract VI+EN 200-350 từ có số định lượng; Chương 1 thêm **"Đóng góp chính"** + chốt **Research Gap**; Chương 5 thêm bảng **Hyperparameters** + công thức **Metrics** + mục **Thảo luận & Hạn chế**. Mọi số trỏ về bảng §4.3 — **không bịa số**.

## 7. Ưu tiên & Verify

**Ưu tiên:** (1) Deploy tử tế → (2) Slide 16 trang (§3) → (3) Còi + video demo → (4) Luyện Q&A (§5) → (5) Vá report (§6).

**Verify trước hội đồng:**
- **Slide:** trình thử ≤15', bấm giờ, nhờ người đóng 3 thầy hỏi bộ §5; rà **không lỗi chính tả**, hiểu mọi hình/thuật ngữ; số khớp `tinyml_model.md` §6 (0.953 / 97.5% / 0.945 / 56.7ms / 28.3KB).
- **Deploy:** mở URL từ máy khác (4G) → dashboard <2s, login + realtime chạy.
- **Demo:** diễn 3 lần liên tục ngã→còi→cảnh báo <2s; test rút mạng còi vẫn hú.
- **Report:** `pdflatex -halt-on-error` EXIT=0 (2 lượt glossary/bib).
