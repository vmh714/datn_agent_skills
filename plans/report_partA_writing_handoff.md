# Handoff cho model rẻ — Viết Phần A (bổ sung REPORT mô tả D-021/D-022)

> **Đối tượng thực thi:** model rẻ (Sonnet/Gemini) qua skill `/write_chapter` (Thesis Writer).
> **Vai trò file này:** brief đủ dữ kiện + neo chèn chính xác để chỉ việc SINH PROSE LaTeX tiếng Việt học thuật rồi chèn. KHÔNG phải tự đi đọc lại code.
> **Nguồn chuẩn dữ kiện:** `architecture/firmware.md`, `DECISIONS.md` D-021/D-022, `protocol.md`. Số liệu model lấy từ bảng §4.3 (đừng bịa).

## LUẬT CHUNG (đọc trước, áp cho mọi mục)
1. Văn phong: tiếng Việt học thuật, mỗi đoạn một ý, câu ngắn, KHÔNG từ cảm xúc ("tuyệt vời", "mạnh mẽ"). `\texttt{}` cho định danh code. (theo `report.md` §7.)
2. **KHÔNG bịa số.** Số liệu model/độ trễ chỉ trỏ về bảng §4.3 bằng `\ref{}`. Số false-positive/recall thực nghiệm của D-021 **để placeholder** `(\todo{số liệu chờ đo})` vì chưa thu data.
3. **Tránh sai lệch code (CRITICAL):**
   - Confirmation là **FSM phụ trong `\texttt{svc\_ai}`** (`FALL_FSM_NORMAL`/`CONFIRMING`). TUYỆT ĐỐI KHÔNG viết thêm system-state `STATE_FALL_CONFIRMING` vào FSM của `sys_manager`.
   - Cấu hình xuống thiết bị đi qua topic **`config/set` (payload gộp)** + echo `config/status`. KHÔNG có topic `config/rssi`.
   - `comms-critical` là **cờ runtime ở `sys_manager`** (monotonic expiry), KHÔNG phải cột DB.
   - Tham số mới: `\texttt{fall\_confirm\_window}` (giây, default 4, range 1–15), `\texttt{rssi\_interval}` (giây, default 300, 0=tắt).
4. Mỗi hình/bảng chèn phải có `\caption` + `\label` + được `\ref` trong text. Hình chưa có → để `\todo{hình ...}` thay vì `\includegraphics` lỗi.
5. Sau khi chèn: build kiểm tra `pdflatex -interaction=nonstopmode -halt-on-error 20225198_VuManhHung.tex` (chạy ở `report/Do_an_tot_nghiep_Vu_Manh_Hung/`), EXIT=0.

---

## A1 — Ch3: Cơ chế xác nhận ngã hai pha
- **File:** `report/Do_an_tot_nghiep_Vu_Manh_Hung/Chuong/3_Phuong_phap_de_xuat.tex`
- **Chèn:** thêm `\subsection{Cơ chế xác nhận ngã hai pha (Post-Impact Confirmation)}\label{subsec:fall_confirm}` ngay SAU mục `\section{...}\label{sec:3.2}` (Chiến lược thiết kế nhãn).
- **Nội dung cần sinh (outline → prose, ~3–4 đoạn):**
  1. **Vấn đề:** ngưỡng `θ=0.25` (ưu tiên Fall recall, xem `\ref{sec:3.2}`) rất nhạy ⇒ dương tính giả lẻ từ động tác giống va đập (ngồi phịch, nhảy, đặt mạnh thiết bị). Cooldown chỉ chống lặp, không chống sai.
  2. **Ý tưởng 2 pha:** giữ ML làm *bộ kích hoạt nhạy* (bảo toàn recall) nhưng KHÔNG báo ngay; chuyển sang pha *xác nhận hậu va chạm* quan sát tư thế trong `\texttt{fall\_confirm\_window}` giây.
  3. **Tín hiệu xác nhận:** đa số cửa sổ suy luận trong khoảng N giây có lớp = `Idle` VÀ góc ROLL ∈ vùng "nằm" (ngoài [60,90]∪[-90,-60] độ) ⇒ CONFIRMED → phát cảnh báo. Nếu đối tượng hồi phục (lớp Walk/Run + tư thế đứng) ⇒ ABORT (loại báo giả). Nêu lý do *post-impact đồng pha recall & precision*: người ngã thật nằm lại; người ngồi phịch đứng dậy ngay.
  4. **Bằng chứng vật lý bổ trợ:** detector per-sample trên SVM gia tốc thô (`\(SVM=\sqrt{a_x^2+a_y^2+a_z^2}\)`): free-fall khi SVM `< 0.6g`, impact khi SVM `> 2.5g`; dùng để *tăng độ tin cậy* (boost), KHÔNG phải điều kiện bắt buộc (để không cắt recall). Nhấn: dùng accel **thô** vì Kalman làm cùn đỉnh.
- **Thuật ngữ glossary cần (xem A7):** SVM, post-impact, free-fall.
- **Có thể thêm** 1 phương trình SVM (`\begin{equation}\label{eq:svm}`) và `\ref` nó.

## A2 — Ch4.2: Thiết kế (firmware + DB + giao thức)
- **File:** `Chuong/4_2_Thiet_ke.tex`
- **Chèn 3 chỗ:**
  1. **Kiến trúc phần mềm Firmware** (đoạn `svc_ai`/`svc_imu`/`sys_manager`): bổ sung 1 đoạn: `\texttt{svc\_ai}` có FSM phụ `NORMAL`/`CONFIRMING` (Post-Impact Confirmation, trỏ `\ref{subsec:fall_confirm}`); `\texttt{svc\_imu}` thêm bộ phát hiện impact/free-fall per-sample (getter `\texttt{imu\_service\_get\_last\_impact()}`); `\texttt{sys\_manager}` giữ cờ *comms-critical* để `\texttt{svc\_network}` không rớt liên kết MQTT lúc đang xác nhận/cảnh báo (D-022).
  2. **Bảng thiết kế CSDL `devices`:** thêm 2 dòng cột — `\texttt{fall\_confirm\_window}` (int, giây, mặc định 4: cửa sổ xác nhận hậu va chạm) và `\texttt{rssi\_interval}` (int, giây, mặc định 300, `0`=tắt: chu kỳ đo RSSI 4G). **KHÔNG thêm** `comms_critical_flag`.
  3. **Thiết kế giao thức truyền thông:** mô tả luồng cấu hình bền vững — Backend gói toàn bộ tham số vào **một** payload `config/set`, thiết bị áp + lưu NVS + echo `config/status` để Backend đồng bộ ngược DB. Liệt kê tham số: interval, fall_threshold, fall_cooldown, **fall_confirm_window, rssi_interval**, stream_timeout.
- **Hình:** ghi `\todo{cập nhật fsm.png: thêm nhánh CONFIRMING của svc\_ai}` (xem A6).

## A3 — Ch4.1: Yêu cầu phi chức năng + cấu hình từ xa
- **File:** `Chuong/4_1_Phan_tich_yeu_cau.tex`, mục `\section{...}\label{section:2.4}` (Yêu cầu phi chức năng).
- **Chèn:** 1 mục yêu cầu mới **"Độ tin cậy cảnh báo (Alert Reliability)"**: giảm tỉ lệ báo giả trong sinh hoạt thường ngày (ADL) trong khi giữ Fall recall ≥ ngưỡng KPI; chấp nhận độ trễ xác nhận ≈ `\texttt{fall\_confirm\_window}` giây như đánh đổi precision↔latency. (Đây là *căn cứ yêu cầu* cho A1.)
- **Thêm 1 câu** ở đặc tả: hệ thống cho phép **cấu hình thiết bị từ xa** các tham số vận hành (chu kỳ telemetry, ngưỡng ngã, cooldown, cửa sổ xác nhận, chu kỳ đo RSSI) qua dashboard, không cần nạp lại firmware.

## A4 — Ch5: Triển khai & thực nghiệm
- **File:** `Chuong/5_Trien_khai_thuc_nghiem.tex`
- **Chèn/sửa 4 việc:**
  1. **§5.4 (hoặc §5.x triển khai)** thêm `\subsubsection{Triển khai cơ chế xác nhận ngã hậu va chạm}`: pseudo-code/diễn giải vòng FSM trong `\texttt{svc\_ai}`: trên mỗi cửa sổ — nếu `NORMAL` và lớp=Fall → vào `CONFIRMING` (mốc thời gian, đọc impact gần nhất qua `\texttt{imu\_service\_get\_last\_impact()}`); trong `CONFIRMING` đếm hits (Idle+lying)/total, ABORT nếu Walk/Run+đứng; hết N giây nếu tỉ lệ ≥ 0.6 → phát `\texttt{AI\_EVT\_FALL\_DETECTED}`. Nêu detector SVM ở `\texttt{svc\_imu}`.
  2. **§5.5 Backend** + **§5.6 Frontend:** thêm `\texttt{fall\_confirm\_window}` và `\texttt{rssi\_interval}` vào mô tả luồng cấu hình: FE form (dropdown, `rssi_interval` có lựa chọn "Tắt") → `PUT /devices/{id}` → Backend publish `config/set` → thiết bị áp+NVS → echo `config/status` → Backend đồng bộ DB. Nêu thêm guard comms-critical của D-022 (không đo RSSI lúc đang xác nhận/cảnh báo).
  3. **SỬA find/replace:** cụm "cooldown 10-20s" (hoặc "10–20 giây") → **"15 giây"** cho khớp `\texttt{FALL\_COOLDOWN\_US}` mặc định.
  4. **§5.7 Kiểm thử tích hợp:** thêm bảng ma trận kịch bản (caption trên, `\label{tab:fall_confirm_test}`): cột [Kịch bản | Kỳ vọng FSM | Cảnh báo?]; hàng: *Ngã thật*→CONFIRMED→Có; *Ngồi phịch mạnh*→ABORT→Không; *Nhảy rồi đứng*→ABORT→Không; *Đo RSSI trong lúc xác nhận*→hoãn (guard)→link giữ. Cột số liệu thực để `\todo{chờ đo}`.

## A5 — Ch6: Kết luận & hướng phát triển
- **File:** `Chuong/6_Ket_luan.tex`
- **Chèn:** (i) thêm đóng góp: "Cơ chế phát hiện ngã hai pha (ML trigger + xác nhận hậu va chạm) giảm báo động giả mà không hi sinh Fall recall." (ii) Bổ sung *hướng phát triển*: CMUX để đo RSSI 4G không phải rớt liên kết (đã thử, chưa khả thi); bảo mật MQTT per-device (creds/ACL/mTLS); chế độ ngủ tiết kiệm điện; STATE_ERROR recovery.

## A6 — Hình
- `fsm.png`: vẽ lại thêm nhánh CONFIRMING của `svc_ai` (hoặc vẽ TikZ trực tiếp — preamble đã có tikz). Nếu chưa làm → để `\todo`.
- `erd.png`: regen từ Mermaid trong `architecture/db_schema.md` (đã có `fall_confirm_window`+`rssi_interval`). Lệnh trong `report.md` §4.
- Tham chiếu danh sách đầy đủ: `plans/report_missing_figures_plan.md`.

## A7 — Glossary
- **File:** `Tu_viet_tat.tex`, thêm `\newglossaryentry` (type acronym) nếu thuật ngữ xuất hiện trong thân bài: **SVM** (Signal Vector Magnitude — biên độ vector gia tốc), **RSSI** (Received Signal Strength Indicator), **ADL** (Activities of Daily Living — sinh hoạt thường ngày). "post-impact"/"free-fall"/"comms-critical" giải thích inline lần đầu, không cần acronym.

---

## DEFINITION OF DONE (cho model rẻ)
- [ ] A1–A5 đã chèn, văn phong học thuật, không bịa số (số thực nghiệm = `\todo`).
- [ ] Không xuất hiện `STATE_FALL_CONFIRMING`, không topic `config/rssi`, không cột `comms_critical_flag`.
- [ ] cooldown đã sửa thành 15s.
- [ ] Mọi `\ref`/`\label` khớp; hình chưa có để `\todo`, không `\includegraphics` file thiếu.
- [ ] `pdflatex ... 20225198_VuManhHung.tex` ×2 → EXIT=0.
- [ ] Đẩy Overleaf bằng `ols` (đẩy đủ file đã đổi; nếu sửa preamble phải đẩy cả `20225198_VuManhHung.tex`).

## Dữ kiện tham chiếu nhanh (để khỏi mở code)
- `fall_confirm_window`: NVS `fall_cf`, default 4000ms, range 1–15s. `svc_ai` FSM, majority ratio 0.6, window trượt 0.5s.
- `rssi_interval`: NVS `rssi_int`, default 300s, 0=tắt, clamp non-zero ≥60s. `svc_network` `cellular_rssi_update_task` (thoát PPP→AT+CSQ→ATO, mỗi lần đứt MQTT ~15-20s).
- comms-critical: `sys_manager_bump_comms_critical(ms)`/`is_comms_critical()`; svc_ai bump khi vào CONFIRMING, svc_cloud bump = fall_cooldown sau alert.
- SVM thresholds: free-fall <0.6g, impact >2.5g (svc_imu, accel thô).
- Cảnh báo giữ contract cũ: vẫn phát `AI_EVT_FALL_DETECTED` → `svc_cloud` publish `eldercare/{mac}/alert/fall` (cooldown 15s).
