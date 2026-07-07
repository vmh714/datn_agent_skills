<!--
================================================================================
 NỘI DUNG SLIDE BẢO VỆ DATN — Vũ Mạnh Hưng  (SỬA FILE NÀY, KHÔNG SỬA .pptx)
================================================================================
 Sau khi sửa file này, chạy:
     cd /d/datn/datn_agent_skills/tools && python build_slides.py
 → sinh lại report/Do_an_tot_nghiep_Vu_Manh_Hung/DATN_VuManhHung_slides.pptx

 CÚ PHÁP
 -------
 • Mở 1 slide:  ## <kind> | <title> [| <subtitle>]
       kind = cover | divider | content
       - content : slide thường (tiêu đề + các block bên dưới)
       - divider : slide ngăn cách nền xanh (title + subtitle)
       - cover   : slide bìa (dùng template, chỉ có block @title / @subtitle)
       title rỗng  → slide không vẽ tiêu đề (vd slide Cảm ơn).

 • Block trong slide bắt đầu bằng:  ### @<type> key=val key="val có dấu cách"
       Nội dung block = các dòng NGAY DƯỚI cho tới block/slide kế tiếp.

 • Các @type và thuộc tính (thuộc tính là TUỲ CHỌN — bỏ trống dùng default):
   @bullets  top= size= left= width=        → mỗi dòng "- ..."; thụt 2 space = bullet cấp 2
   @image    name= left= top= w= h= caption=
   @images-row top= height= total_w= left0= gap=   → mỗi dòng "- ten.png | caption"
   @table    left= top= width= height= fs= colw=a,b  → mỗi dòng "| c1 | c2 |" (dòng đầu = header)
   @flow     top= box_h= total_w= left= horizontal=true/false box_w= fills=n1,n2
             → mỗi dòng "- bước" ; "\n" trong text = xuống dòng trong ô ; fills name: lightblue|green
   @banner   color=green|blue top= left= w= h= size=   → dòng text (băng bo góc, thường ở đáy)
   @notes    → speaker notes (không hiện trên slide) ; "\n" = xuống dòng
   @heading  top= size=   → 1 dòng chữ lớn căn giữa (dùng cho slide Cảm ơn)

 • SỐ LIỆU CHUẨN (khớp báo cáo Ch5): 17 ms @160MHz deploy · 11,2 ms benchmark 240MHz ·
   ~180× TCN · Fall recall 97,5% · Trans F1 0,907→0,945. KHÔNG dùng 56 ms / 36×.
 • RULE 1-ẢNH: biểu đồ / UI web / API = 1 ảnh/slide. Ảnh minh hoạ phần cứng thì nhiều/slide OK.
================================================================================
-->

# DATN — Slides content

## cover |
### @title
Nghiên cứu và xây dựng hệ thống giám sát hành vi người già và phát hiện té ngã ứng dụng IoT và TinyML
### @subtitle
- Sinh viên: Vũ Mạnh Hưng
- MSSV: 20225198
- GVHD: PGS. TS. Nguyễn Hồng Quang

## content | Nội dung trình bày
### @flow top=2.0 box_h=1.4 total_w=9.0 left=0.5
- Đặt vấn đề\n& mục tiêu
- Kiến trúc\ntổng quan
- Nghiên cứu\nTinyML
- Thiết kế\nhệ thống
- Kết quả\n& Demo
### @bullets top=4.1 size=16
- Nghiên cứu (trọng tâm): dữ liệu SisFall, chiến lược nhãn, các pha cú ngã, tối ưu kiến trúc TinyML cho ESP32-S3.
- Kỹ thuật hệ thống: firmware event-driven, MQTT/TLS, dual-DB, dashboard realtime.
- Kết quả thực nghiệm mô hình & hệ thống, Demo, Kết luận.

## content | Đặt vấn đề & Mục tiêu nghiên cứu
### @banner color=green top=5.8 left=0.6 w=8.8 h=0.8 size=16
AI chạy thật trên chip (17 ms), không cần Cloud, mất mạng vẫn phát hiện ngã
### @images-row top=1.5 height=2.5 total_w=5.0 left0=2.5
- hovding.jpg | Hövding (thể thao)
- tangobelt.jpg | TangoBelt (người già)
### @bullets top=4.3 size=15
- Dân số già hoá; ngã là nguyên nhân thương vong hàng đầu ở người cao tuổi.
- Hạn chế thiết bị hiện tại: giải pháp Cloud-AI trễ cao, phụ thuộc mạng/smartphone; rủi ro riêng tư.
- Mục tiêu: Xây dựng hệ thống giám sát ngã on-device (Edge-AI) kết hợp Dashboard cảnh báo 24/7.

## content | Nghiên cứu liên quan & Research Gap
### @images-row top=1.5 height=2.5 total_w=5.0 left0=2.5
- hipair.jpg | Hip'Air
- alpinestars.jpg | Alpinestars
### @bullets top=4.3 size=15
- Airbag wearable thương mại đắt đỏ, thường bảo vệ một chiều (hông/cổ), không tích hợp Dashboard y tế.
- Cloud-AI (camera/wifi): không đảm bảo 24/7, tốn năng lượng truyền phát dữ liệu.
- Khoảng trống (Research Gap): TinyML xử lý nhãn động học (chuyển tư thế - Trans) còn kém → nhiều báo giả.

## content | Ba đóng góp chính của đồ án
### @flow top=1.7 box_h=1.5 total_w=9.0 left=0.5
- ① Sơ đồ nhãn 5 lớp\n(thêm Trans/Idle)
- ② Kiến trúc CNN\ntối ưu ESP-NN
- ③ Hệ thống IoT\nend-to-end production
### @bullets top=3.6 size=15
- ① Giải nhập nhằng chuyển tư thế người già → F1-Trans 0,799 → 0,945 (đo trên chip).
- ② Head giữ trục thời gian: nhanh ~180× teacher TCN mà Fall Recall 97,5% ≥ teacher; thắng từ kiến trúc, không phải KD.
- ③ Firmware C event-driven + FSM, MQTT/TLS, dual-DB (PostgreSQL + InfluxDB), multi-tenancy, OTA.

## divider | Phần 1 — Nghiên cứu TinyML | Dữ liệu · Nhãn · Các pha cú ngã · Tối ưu kiến trúc trên ESP32-S3

## content | Bộ dữ liệu SisFall & Quy trình tiền xử lý
### @flow top=1.7 box_h=1.2 total_w=9.0 left=0.5
- Raw SisFall\n200 Hz
- Downsample\n100 Hz
- Chuẩn hoá\n[-1, 1]
- Cửa sổ\n200 × 6
### @bullets top=3.5 size=16
- SisFall: gia tốc + con quay hồi chuyển; người trẻ (SA) và người già (SE).
- Giảm mẫu 200→100 Hz (thoả Nyquist) tiết kiệm tính toán; chuẩn hoá [-1,1] cho INT8.
- Chia dữ liệu độc-lập-đối-tượng (subject-independent) — không trộn mẫu cùng người.

## content | Phân tích phân bố gia tốc → chọn thang ±8 g
### @image name=accel_distribution_2x2.png left=1.3 top=1.4 w=7.4 h=4.3
### @bullets top=5.85 size=15
- Phân tích bách phân vị toàn tập SisFall để chọn ngưỡng không xén dữ liệu.
- P99,9 ≈ 5,2 g → chọn thang ±8 g: bao trọn xung va chạm mạnh nhất mà không bão hoà cảm biến.

## content | Phân tích phân bố vận tốc góc → chọn thang ±500 dps
### @image name=gyro_distribution_2x2.png left=1.3 top=1.4 w=7.4 h=4.3
### @bullets top=5.85 size=15
- P99,9 ≈ 463 dps → chọn thang ±500 dps: tối ưu độ phân giải INT8 (so với ±2000 dps).
- Bài học: sai đơn vị góc (rad/s vs deg/s) từng làm mô hình v25 'mù' chuyển động xoay.

## content | Cắt cửa sổ (Windowing) & Tăng cường dữ liệu
### @image name=har_windows.png left=1.0 top=1.4 w=8.0 h=3.2
### @bullets top=4.8 size=15
- Sinh hoạt (Walk/Run): trượt cửa sổ liên tục.
- Chuyển tiếp (Trans) / Cú ngã: cắt theo sự kiện (Event-based) khi RMS gyro > 20 dps → 1 cửa sổ căn đỉnh.
- Tăng cường (Augmentation): nhân biên độ lớp Trans ×0,9 và ×1,1 mô phỏng lực người trẻ ↔ người già.

## content | ★ Chiến lược thiết kế nhãn 5 lớp
### @bullets top=1.4 size=15
- 4 nhãn (gộp mọi tư thế vào Static/ADL) → xung chuyển tư thế giống cú ngã → BÁO GIẢ.
- Thêm nhãn Trans tách hẳn chuyển tư thế; thử 6 nhãn (Lie/StandSit) → gộp lại Idle.
### @table left=1.0 top=3.0 width=8.0 height=3.2 fs=15
| Nhãn | Mã SisFall | Cách xác định |
| Walk | D01,D02,D05,D06 | Đi bộ, lên/xuống cầu thang |
| Run | D03,D04 | Chạy bộ chậm/nhanh |
| Idle | D07–D16 (tĩnh) | Gyro RMS ≤ 20 dps |
| Trans | D07–D16 (động) | Gyro RMS > 20 dps, cửa sổ căn đỉnh |
| Fall | F01–F15 | Toàn bộ sự kiện ngã |

## content | Xử lý mất cân bằng & ngưỡng quyết định
### @flow top=1.7 box_h=1.25 total_w=9.0 left=0.5 fills=lightblue,lightblue,green
- class_weight\n×3 lớp Fall
- Label Smoothing\nε = 0,1
- Ngưỡng Fall\nθ = 0,25
### @bullets top=3.5 size=17
- Bù tỷ lệ mẫu Fall thấp; Label Smoothing giảm quá tự tin, cải thiện hiệu chỉnh xác suất.
- Hạ θ = 0,25 (thay 0,5) → ưu tiên tối đa Recall: bỏ sót một cú ngã nguy hiểm hơn một cảnh báo nhầm.

## content | ★ Các pha động học của một cú ngã
### @image name=fall_phases.png left=0.5 top=1.4 w=9.0 h=5.7
### @notes
Pre-impact → Free-fall → Impact → Post-impact (nằm) → Recovery.\nFree-fall SVM < 0,6 g • Impact SVM > 2,5 g (dùng gia tốc THÔ để không cùn đỉnh xung).

## content | ★ Cơ chế xác nhận ngã hai pha (Post-Impact Confirmation)
### @image name=svc_ai_fsm.png left=0.4 top=1.5 w=9.2 h=3.5
### @bullets top=5.05 size=15
- Giữ ML là bộ kích hoạt NHẠY (bảo toàn Recall) nhưng KHÔNG báo ngay; FSM phụ trong svc_ai bù lại Precision.
- ≥60% cửa sổ là Idle + Roll ở tư thế nằm trong fall_confirm_window → CONFIRMED (báo); phục hồi (Walk/Run + đứng) → ABORT.

## content | Chiến lược chống báo giả 4 tầng
### @flow top=1.6 box_h=0.85 total_w=8.2 left=0.9 horizontal=false box_w=8.2
- Tầng 1 — Pre-Impact Posture Gating (loại nhiễu khi không đeo)
- Tầng 2 — fall_threshold θ (kiểm soát độ nhạy vào pha xác nhận)
- Tầng 3 — FSM xác nhận hậu va chạm (lọc theo tư thế nằm)
- Tầng 4 — fall_cooldown (giới hạn tần suất cảnh báo)
### @bullets top=6.4 size=14
- Cả 3 tham số (θ, cooldown, confirm_window) cấu hình từ xa qua Dashboard — không cần nạp lại firmware.

## content | Bài toán TinyML: hai ràng buộc đối nghịch
### @images-row top=1.5 height=2.6 total_w=6.0 left0=2.0
- esp32s3_front.png | XIAO ESP32-S3
- mpu6050.jpg | IMU MPU-6050
### @bullets top=4.4 size=16
- Ràng buộc 1: Cần đủ khả năng biểu đạt để xử lý chuỗi IMU 6 chiều × 200 mẫu.
- Ràng buộc 2: Phải phù hợp tài nguyên ESP32-S3 và hỗ trợ lượng tử hoá INT8 tốt.
- LSTM lượng tử hoá kém, suy luận chậm; CNN (Conv1D) được tăng tốc ESP-NN hỗ trợ tối đa.

## content | Ba thế hệ tối ưu kiến trúc mô hình
### @image name=model_evolution.png left=0.5 top=1.4 w=9.0 h=5.7
### @notes
CNN-LSTM → TCN (chính xác nhưng > 2 s) → CNN thuần ESP-NN (< 20 ms).

## content | Depthwise Separable Conv & ESP-NN
### @image name=depthwise_separable.png left=0.7 top=1.3 w=8.6 h=3.85
### @table left=2.7 top=5.35 width=4.6 height=1.4 fs=13
| Kỹ thuật (ESP-NN) | Tăng tốc |
| SeparableConv1D | 6,3× |
| Pointwise Conv 1×1 | 14,2× |
| Hàm kích hoạt relu6 | 11,5× |
### @notes
Tách tích chập: Depthwise (lọc không gian từng kênh) + Pointwise 1×1 (trộn kênh). Giảm tính toán ~ (1/C_out + 1/K); mọi toán tử đều được ESP-NN tăng tốc → suy luận < 20 ms.

## content | ★ Kiến trúc đề xuất: v30_optimize (26.629 tham số)
### @image name=v30opt_architecture.png left=0.5 top=1.4 w=9.0 h=5.7
### @notes
Head GAP+GMP+Flatten giữ trục thời gian. KD ablation chứng minh thắng lợi từ kiến trúc.

## divider | Phần 2 — Thiết kế hệ thống | Kiến trúc Edge → Cloud → Web · Firmware · Backend dual-DB · Dashboard

## content | Phân tích chức năng: Use case tổng quát
### @image name=use_case_tongquat.png left=0.5 top=1.4 w=9.0 h=5.7
### @notes
Hệ thống có 2 tác nhân chính: Nhân viên y tế (người dùng) và Thiết bị giám sát (tác nhân hệ thống).

## content | Quy trình nghiệp vụ: Luồng xử lý sự cố té ngã
### @image name=activity_fall.png left=0.5 top=1.4 w=9.0 h=5.7
### @notes
Quy trình y tá nhận cảnh báo trên Dashboard -> tới hiện trường -> sơ cứu -> bấm Resolve (Đã xử lý).

## content | Kiến trúc tổng quan hệ thống (Edge → Cloud → Web)
### @image name=arch.png left=0.5 top=1.4 w=9.0 h=5.6
### @notes
Edge(ESP32-S3) → MQTT/TLS → Backend(FastAPI dual-DB) → Dashboard(Next.js). Firmware phát telemetry/alert; backend cầu nối MQTT→DB; frontend nhận realtime qua MQTT WebSocket.

## content | Giao thức truyền thông MQTT & cấu trúc Topic
### @image name=mqtt_architechture.png left=0.5 top=1.4 w=9.0 h=5.6
### @notes
Topic phân cấp [org]/[device]/[type]; bảo mật TLS 8883 (MQTTS) + JWT HS256; các topic chính: telemetry, alert, config/OTA.

## content | Kiến trúc phần mềm Firmware (phân lớp drv/svc/lib/sys)
### @image name=fw_pkg.png left=0.5 top=1.4 w=9.0 h=5.7
### @notes
4 tầng: drv_ (điều khiển phần cứng), svc_ (dịch vụ/task), lib_ (thuật toán), sys_ (điều phối FSM). Luồng đỏ: svc_ai phát Sự kiện Ngã → sys_manager → svc_cloud phát Cảnh báo SOS.

## content | Firmware: Event-driven & Máy trạng thái (FSM)
### @image name=fsm.png left=2.0 top=1.4 w=6.0 h=3.8
### @bullets top=5.5 size=15
- Kiến trúc phân lớp; FSM điều phối thiết bị: INIT → CONNECTING → NORMAL → OTA/ERROR.
- Lấy mẫu 100 Hz bằng ngắt phần cứng PCNT → jitter < 1 µs, độc lập tải CPU.

## content | Backend & Cơ sở dữ liệu kép (PostgreSQL + InfluxDB)
### @image name=erd.png left=0.3 top=1.4 w=9.4 h=5.7
### @notes
Sơ đồ ERD PostgreSQL (7 bảng, đa khách thuê qua org_id). InfluxDB lưu time-series telemetry. Multi-tenant, JWT+MQTTS.

## content | Cơ chế đồng bộ cảnh báo lai (Hybrid Alert Sync)
### @image name=sync.png left=1.75 top=1.4 w=6.5 h=5.5
### @notes
MQTT báo tức thời + UUID tạm; DB ghi bền vững + ID thực; fallback resolve.

## content | Web App — Dashboard giám sát realtime
### @image name=dashboard.png left=0.5 top=1.4 w=9.0 h=5.6 caption=Giám sát trạng thái toàn bộ người bệnh tại trạm điều dưỡng; cấu hình thông số MCU từ xa

## content | Web App — Cảnh báo khẩn cấp toàn cục
### @image name=global_fall_alert.png left=0.5 top=1.4 w=9.0 h=5.6 caption=Popup đỏ nổi tức thời trên mọi màn hình khi phát hiện té ngã

## content | Web App — Lịch sử & chi tiết thiết bị
### @image name=device_vitals.png left=0.5 top=1.4 w=9.0 h=5.6 caption=Truy xuất chuỗi thời gian sức khoẻ (InfluxDB); cấu hình ngưỡng cảnh báo từ xa (OTA)

## divider | Phần 3 — Kết quả & Kết luận | Kết quả mô hình trên chip · Thử nghiệm hệ thống · Demo · Kết luận

## content | ★ Kết quả mô hình: Ma trận nhầm lẫn (INT8 trên chip)
### @image name=confusion_matrix_v30_opt_espnn_ON_sram_firmware.png left=2.6 top=1.4 w=4.8 h=4.4
### @bullets top=5.95 size=14
- Acc 95,40% · Fall recall 97,50% · Trans F1 0,907 → 0,945 (kd2).
- Lượng tử hoá INT8 gần như không suy giảm; nhầm lẫn còn lại tập trung ở cặp Idle/Trans.

## content | ★ Đánh đổi hiệu năng các kiến trúc trên ESP32-S3
### @image name=mcu_evolution.png left=1.0 top=1.4 w=8.0 h=4.4
### @bullets top=5.85 size=15
- v30_optimize đạt Acc ~ TCN nhưng nhanh ~180× teacher TCN; 17 ms « chu kỳ 500 ms; Arena 28,3 KB.
  Đo trên bản deploy ESP32-S3 @ CPU 160 MHz, INT8, ESP-NN (benchmark 240 MHz đạt 11,2 ms).

## content | Kiểm định chéo dân số (KFold v6, LSO)
### @table left=1.2 top=1.5 width=7.6 height=3.0 fs=15
| Kịch bản | Acc. | Trans F1 | Fall Recall |
| S1 Chỉ người già (SE) | 89,1% | 0,83 | † |
| S2 Chỉ người trẻ (SA) | 96,8% | 0,91 | 99,6% |
| S3 Già → Trẻ | 94,6% | 0,83 | 95,3% |
| S4 Trẻ → Già | 92,8% | 0,87 | 98,7% |
| S5 Hỗn hợp | 96,3% | 0,92 | 99,5% |
### @bullets top=4.8 size=15
- S5 (hỗn hợp) tiệm cận phân chia chuẩn → khái quát hoá tốt.
- S1: Giới hạn do SisFall thiếu dữ liệu Fall người già.

## content | Kết quả thử nghiệm: Thiết bị đeo phần cứng
### @images-row top=1.5 height=4.0 total_w=8.0 left0=1.0
- hardware_picture.jpg | Thiết bị hoàn thiện
- device_weared.jpg | Thử nghiệm đeo trên người
### @bullets top=5.85 size=15
- Kịch bản: Ngã → cảnh báo < 2 s; Edge chạy offline hoàn toàn; hỗ trợ OTA.
- Thiết bị gọn nhẹ, không sinh cảnh báo giả trong sinh hoạt bình thường.

## content | Kết quả thử nghiệm: REST API & tích hợp Backend
### @image name=fastapi_swagger.png left=0.5 top=1.4 w=9.0 h=5.6 caption=Bộ REST API (FastAPI/Swagger) quản lý thiết bị, người bệnh, cảnh báo

## content | Demo hệ thống
### @bullets top=1.4 size=18
- 1. Đeo thiết bị → Giả ngã → CÒI HÚ tại thiết bị + Dashboard ĐỎ (< 2 s).
- 2. Rút mạng → Giả ngã → CÒI VẪN HÚ (Edge-AI offline).
### @images-row top=3.0 height=3.5 total_w=8.0 left0=1.0
- device_weared.jpg | Giả ngã
- global_fall_alert.png | Cảnh báo khẩn cấp (Dashboard)

## content | Thảo luận & Hạn chế
### @bullets top=2.0 size=18
- S1 thiếu dữ liệu Fall người già.
- S4 (trẻ → già): người già chuyển tư thế rất chậm → mô hình dễ hiểu nhầm thành Fall (Precision 74,6%).
- Chế độ tiết kiệm pin (Light-Sleep) đang trong quá trình thử nghiệm.

## content | Kết luận & Hướng phát triển
### @bullets top=1.8 size=17
- Kết luận:
  Hoàn thành hệ thống Fall Detection on-device (17 ms @160 MHz, INT8, không cần Cloud).
  Tích hợp full-stack tới dashboard realtime, dual-DB, MQTT/TLS.
  Đóng góp về sơ đồ nhãn và kiến trúc CNN giữ trục thời gian.
- Hướng phát triển:
  Tối ưu Light-Sleep tiết kiệm pin.
  Thu thập thêm dữ liệu ngã thực tế từ người già.

## content |
### @image name=device_weared.jpg left=3.7 top=1.4 w=2.6 h=3.0
### @heading top=4.7 size=28
Trân trọng cảm ơn Hội đồng đã lắng nghe!

## divider | Phụ lục | Tài liệu backup phục vụ hỏi đáp — SisFall · Hyperparameters · Metrics · Use case

## content | Phụ lục — Bộ dữ liệu SisFall
### @table left=0.5 top=1.5 width=9.0 height=3.7 fs=12
| Thuộc tính | Giá trị |
| Nguồn | Công khai — Sucerquia et al., Univ. Antioquia (2017) |
| Đối tượng | 38 người: 23 trẻ SA (19–30 tuổi) + 15 già SE (60–75 tuổi) |
| Hoạt động ADL | 19 loại (D01–D19): đi, chạy, cầu thang, ngồi/đứng, nằm, cúi… |
| Té ngã | 15 kiểu (F01–F15): ngã trước/sau/ngang, khi ngồi, ngất xỉu… |
| Số file | 4.510 file (mỗi file 1 hoạt động) |
| Cảm biến (9 cột) | 2 gia tốc kế ADXL345 (±16g) + MMA8451Q (±8g); 1 con quay ITG3200 (±2000°/s) |
| Tần số | 200 Hz gốc → đồ án hạ 100 Hz, dùng 6 kênh (accel + gyro) |
### @bullets top=5.35 size=12
- ⚠ Điểm thầy hay hỏi — thiên lệch dữ liệu: người già GẦN NHƯ chỉ mô phỏng ADL; chỉ DUY NHẤT SE06 (chuyên Judo) thực hiện ngã → toàn bộ dữ liệu NGÃ gần như của người trẻ.
- → Hạn chế khái quát hoá cho người già (KFold: S1 thiếu mẫu Fall-SE; S4 Precision 74,6%). Đồ án bù bằng split subject-independent + kế hoạch thu dữ liệu cá nhân trên thiết bị thật.

## content | Phụ lục — Chi tiết hoạt động sinh hoạt (ADL, D01–D19)
### @table left=1.0 top=1.35 width=8.0 height=5.5 fs=10 colw=1.0,7.0
| Mã | Mô tả hoạt động |
| D01 | Đi bộ chậm |
| D02 | Đi bộ nhanh |
| D03 | Chạy bộ chậm |
| D04 | Chạy bộ nhanh |
| D05 | Lên/xuống cầu thang chậm |
| D06 | Lên/xuống cầu thang nhanh |
| D07 | Ngồi chậm xuống ghế nửa cao, chờ, đứng lên chậm |
| D08 | Ngồi nhanh xuống ghế nửa cao, chờ, đứng lên nhanh |
| D09 | Ngồi chậm xuống ghế thấp, chờ, đứng lên chậm |
| D10 | Ngồi nhanh xuống ghế thấp, chờ, đứng lên nhanh |
| D11 | Đang ngồi, cố đứng lên rồi ngồi sụp lại ghế |
| D12 | Đang ngồi, nằm xuống chậm, chờ, rồi ngồi lại |
| D13 | Đang ngồi, nằm xuống nhanh, chờ, rồi ngồi lại |
| D14 | Nằm ngửa → xoay nghiêng → xoay lại ngửa |
| D15 | Đứng, khuỵu gối chậm, rồi đứng dậy |
| D16 | Đứng, cúi người (không khuỵu gối), rồi đứng dậy |
| D17 | Đứng, lên ô tô, ngồi yên, rồi xuống xe |
| D18 | Vấp khi đang đi (không ngã) |
| D19 | Nhảy nhẹ không ngã (với lấy vật trên cao) |

## content | Phụ lục — Chi tiết các kiểu té ngã (Fall, F01–F15)
### @table left=1.0 top=1.5 width=8.0 height=4.9 fs=11 colw=1.0,7.0
| Mã | Mô tả kiểu té ngã |
| F01 | Ngã trước khi đang đi, do trượt |
| F02 | Ngã sau khi đang đi, do trượt |
| F03 | Ngã ngang khi đang đi, do trượt |
| F04 | Ngã trước khi đang đi, do vấp |
| F05 | Ngã trước khi đang chạy, do vấp |
| F06 | Ngã thẳng đứng khi đang đi, do ngất |
| F07 | Ngã khi đang đi, chống tay lên bàn giảm chấn, do ngất |
| F08 | Ngã trước khi cố đứng lên |
| F09 | Ngã ngang khi cố đứng lên |
| F10 | Ngã trước khi cố ngồi xuống |
| F11 | Ngã sau khi cố ngồi xuống |
| F12 | Ngã ngang khi cố ngồi xuống |
| F13 | Ngã trước khi đang ngồi, do ngất/ngủ gật |
| F14 | Ngã sau khi đang ngồi, do ngất/ngủ gật |
| F15 | Ngã ngang khi đang ngồi, do ngất/ngủ gật |
### @bullets top=6.6 size=11
- Mỗi hoạt động lặp nhiều lần (Trials) trên nhiều đối tượng → tổng 4.510 file tín hiệu @ 200 Hz.

## content | Phụ lục — Ngăn xếp mạng 4G & Pedometer
### @image name=pppos_stack.png left=5.3 top=1.5 w=4.2 h=3.6
### @bullets top=1.5 size=15 width=4.7
- Mạng di động 4G thông qua PPPoS/LwIP.
- Module A7680C kết nối UART với ESP32-S3.
- Pedometer: đếm bước chân HAR-gated (band-pass 0,5–3,5 Hz).

## content | Phụ lục — Siêu tham số & Môi trường huấn luyện
### @table left=1.0 top=1.5 width=8.0 height=3.5 fs=15
| Tham số | Cấu hình |
| Optimizer | Adam (lr=0.001, beta_1=0.9, beta_2=0.999) |
| Loss function | Categorical Cross-entropy với Label Smoothing ε = 0,1 |
| Batch size | 64 |
| Epochs | 100 (EarlyStopping patience=15) |
| Class weights | Walk/Run/Idle/Trans = 1.0; Fall = 3.0 |
### @bullets top=5.2 size=15
- Huấn luyện trên TensorFlow/Keras 2.15, tối ưu cho quantization-aware training (QAT).

## content | Phụ lục — Các chỉ số đánh giá (Metrics)
### @bullets top=1.5 size=16
- 1. Accuracy: Tỷ lệ dự đoán đúng trên toàn bộ tập dữ liệu.
- 2. Precision: Tỷ lệ mẫu thực sự dương tính trong các dự đoán dương tính.
- 3. Recall (Sensitivity): Tỷ lệ mẫu thực sự dương tính được phát hiện (ĐẶC BIỆT QUAN TRỌNG VỚI NGÃ).
- 4. F1-Score: Trung bình điều hoà của Precision và Recall.
- 5. Macro-F1: Trung bình F1-Score của tất cả các nhãn (bình đẳng mọi lớp).

## content | Phụ lục — Tham số bộ lọc chống báo giả (Cấu hình OTA)
### @table left=0.5 top=1.5 width=9.0 height=2.5 fs=15
| Tham số | Giá trị mặc định | Ý nghĩa |
| fall_threshold | 0.25 (25%) | Ngưỡng kích hoạt pha xác nhận. Ưu tiên Recall. |
| fall_confirm_window | 200 (2 giây) | Khoảng thời gian nằm quan sát (Idle/Roll) sau khi ngã. |
| fall_cooldown | 500 (5 giây) | Thời gian bỏ qua cảnh báo mới sau khi đã báo. |
### @bullets top=4.5 size=15
- Cả 3 tham số có thể cập nhật Real-time từ xa qua MQTT (topic config), không cần nạp lại Firmware.

## content | Phụ lục — Lấy mẫu định thời bằng PCNT (Pulse Counter)
### @bullets top=1.5 size=16
- Vấn đề: vTaskDelay/FreeRTOS timer có độ rung (jitter) từ 1–3 ms, làm sai lệch phân tích tần số.
- Giải pháp đồ án: Sử dụng bộ đếm xung phần cứng (PCNT) của ESP32-S3 kết nối nội bộ với tín hiệu PWM 100 Hz.
- Hiệu quả: Kích hoạt ngắt chính xác tuyệt đối (Jitter < 1 µs), hoàn toàn độc lập với tải CPU.

## content | Phụ lục — Knowledge Distillation Ablation Study
### @table left=1.0 top=1.5 width=8.0 height=2.5 fs=15
| Cấu hình KD | F1-Fall | F1-Trans | Macro-F1 |
| Không KD (Gốc) | 0.9826 | 0.9071 | 0.9524 |
| KD α=0.3 | 0.9859 | 0.8920 | 0.9504 |
| KD α=0.5 | 0.9856 | 0.9015 | 0.9507 |
| KD α=1.0 | 0.9841 | 0.9071 | 0.9515 |
### @bullets top=4.5 size=15
- Kết luận: Bản TẮT KD ngang hoặc nhỉnh hơn các bản có KD ở nhãn Trans và Macro-F1.
- → Cải tiến hiệu năng của v30_optimize đến từ KIẾN TRÚC giữ trục thời gian, không phụ thuộc teacher.

## content | Phụ lục — Use case: Giám sát thời gian thực
### @image name=use_case_giam_sat.png left=0.5 top=1.4 w=9.0 h=5.7
### @notes
Nhân viên y tế xem trạng thái thiết bị và nhận cảnh báo hybrid alert sync.

## content | Phụ lục — Use case: Xử lý cảnh báo té ngã
### @image name=use_case_xu_ly.png left=0.5 top=1.4 w=9.0 h=5.7
### @notes
Đến hiện trường hỗ trợ bệnh nhân và nhấn Đã xử lý (Resolve) trên hệ thống.

## content | Phụ lục — Use case: Gán thiết bị cho bệnh nhân
### @image name=use_case_gan_thiet_bi.png left=0.5 top=1.4 w=9.0 h=5.7
### @notes
Liên kết MAC thiết bị với hồ sơ bệnh nhân, tính toán quãng đường dựa trên chiều cao.

## content | Phụ lục — Use case: Xem thống kê vận động
### @image name=use_case_thong_ke.png left=0.5 top=1.4 w=9.0 h=5.7
### @notes
Truy xuất time-series từ InfluxDB để vẽ biểu đồ bước chân, quãng đường.

## content | Phụ lục — Tự động đăng ký thiết bị (Auto-provisioning)
### @image name=use_case_autoprovision.png left=0.5 top=1.4 w=9.0 h=5.7
### @notes
Thiết bị tự động đăng ký vào hệ thống bằng MAC eFuse qua MQTT config/status.

## content | Phụ lục — Luồng hoạt động: Tự động đăng ký thiết bị
### @image name=activity_autoprovision.png left=0.5 top=1.4 w=9.0 h=5.7
### @notes
Chi tiết luồng auto-provisioning từ eFuse qua MQTT tới Backend MQTT Service.
