# Handoff cho model rẻ — Cập nhật USE CASE: Auto-provisioning thiết bị (D-020)

> **Đối tượng:** model rẻ qua `/write_chapter` (Thesis Writer). Brief tự-chứa, KHÔNG cần đọc lại code.
> **File sửa:** `report/Do_an_tot_nghiep_Vu_Manh_Hung/Chuong/4_1_Phan_tich_yeu_cau.tex`
> **Vì sao:** sau D-020, đăng ký thiết bị là **tự động (zero-touch)** — chương use case chưa phản ánh. Đây là điểm sáng cần khoe.

## LUẬT CHUNG
1. Văn phong học thuật tiếng Việt; `\texttt{}` cho định danh code; không bịa số.
2. **Dữ kiện D-020 (KHÔNG sai lệch):**
   - Thiết bị đọc **MAC từ eFuse** (`esp_read_mac`, 12 hex) → MAC = **khóa topic MQTT** `eldercare/<mac>/...`, ổn định qua erase-flash/OTA, không cần nhập tay.
   - Khi kết nối (4G/WiFi) thiết bị publish **`config/status`** (fire lúc connect/reconnect) gồm `mac` + `fw_version`.
   - Backend `mqtt_service` nhận MAC lạ → `_get_or_create_device_by_mac` → `_resolve_org_id` (org của deployment = `settings.ORG_ID` hoặc org duy nhất) → `_next_device_id` sinh **`device_id` ngữ nghĩa `esp32_eldercare_NN`** (tuần tự trong org) + lưu mac. `firmware_version` tự cập nhật từ `fw_version`.
   - **Người dùng KHÔNG nhập `device_id`/firmware**; cắm nguồn là thiết bị tự lên Dashboard; nhân viên y tế chỉ **gán wearer** sau đó.
   - Multi-tenancy = **per-org broker** (1 org/deployment).
3. **Tái dùng style TikZ có sẵn trong file** (đừng thêm package preamble): use-case dùng `usecase`/`ucsystem`/`ucactorpic`/`assoc`/`ucinc`; swimlane dùng khối style `act`/`actstart`/`flow` y như `\ref{fig:activity_fall}` (subsection 2.2.6).

---

## F1 — Sửa sơ đồ use case tổng quát (`fig:use_case_tongquat`)
- **Vị trí:** trong `tikzpicture` của `subsection:2.2.1` (dòng ~17–48).
- **Sửa:** hiện actor "Thiết bị giám sát" (`espp`) chỉ nối `uc5`,`uc6`. **Thêm 1 dòng** để thể hiện thiết bị tự đăng ký:
  ```latex
  \draw[assoc] (espp) -- (uc2.east);
  ```
  (uc2 = "Quản lý thiết bị".) Cập nhật 1 câu trong đoạn văn trên hình: nêu rõ thiết bị là tác nhân **tự đăng ký** vào use case Quản lý thiết bị.

## F2 — Thêm subsection mới: "Tự động đăng ký thiết bị (Auto-provisioning)"
- **Vị trí:** chèn `\subsection{...}\label{subsection:2.2.7}` NGAY SAU `subsection:2.2.6` (Activity Diagram), trước `\section{Đặc tả chức năng}\label{section:2.3}`.
- **Đoạn văn (sinh prose, ~1 đoạn):** giải thích cơ chế zero-touch theo dữ kiện §LUẬT CHUNG mục 2 — nhấn: loại bỏ thao tác nhập `device_id` thủ công (dễ trùng/sai), thiết bị tự nhận diện bằng MAC eFuse, backend sinh id ngữ nghĩa tuần tự; nhân viên chỉ gán wearer.
- **Hình 1 — Use case phân rã** (bubble, style như các 2.2.x): actor chính = **Thiết bị giám sát** (trái) + actor phụ = **Nhân viên y tế** (phải, làm bước gán sau). Các node usecase:
  - `Đọc MAC từ eFuse` · `Kết nối MQTT & publish config/status` · `Sinh device_id esp32_eldercare_NN` · `Lưu MAC + cập nhật firmware_version` · `Hiển thị trên Dashboard` · (phụ) `Gán wearer`.
  - `\caption{Biểu đồ use case phân rã "Tự động đăng ký thiết bị"}\label{fig:use_case_autoprovision}`.
- **Hình 2 — Sơ đồ hoạt động swimlane** (A11; **sao chép khối `tikzpicture` của `fig:activity_fall`** rồi đổi):
  - **4 lane:** `Thiết bị (ESP32-S3)` | `MQTT Broker` | `Backend (mqtt_service)` | `Nhân viên y tế`.
  - **Chuỗi act + flow (theo thứ tự):**
    1. (Thiết bị) Boot → đọc MAC từ eFuse
    2. (Thiết bị) Kết nối 4G/WiFi + MQTT
    3. (Thiết bị) Publish `config/status` {mac, fw_version} —`qua MQTT Broker (QoS 1)`→
    4. (Backend) Tra cứu thiết bị theo MAC
    5. (Backend) **[quyết định]** MAC đã tồn tại? — **Chưa** → sinh `device_id` `esp32_eldercare_NN` + lưu MAC; **Rồi** → chỉ cập nhật `firmware_version`
    6. (Backend) Thiết bị xuất hiện trên Dashboard
    7. (Nhân viên y tế) Gán wearer cho thiết bị → kết thúc
  - Dùng node hình thoi cho bước quyết định (hoặc chú thích 2 nhánh nếu ngại vẽ diamond).
  - `\caption{Biểu đồ hoạt động luồng tự động đăng ký thiết bị (Auto-provisioning)}\label{fig:activity_autoprovision}`.
- Nhớ `\ref` cả 2 hình trong đoạn văn.

## F3 — Thêm bảng Đặc tả Use case (§2.3)
- **Vị trí:** trong `\section{Đặc tả chức năng}` (§2.3), thêm 1 `\subsection` + bảng theo đúng mẫu các bảng `tab:uc_*` đang có.
- **Nội dung bảng** (`\label{tab:uc_autoprovision}`):
  - Tên Use case: **Tự động đăng ký thiết bị (Auto-provisioning)**
  - Tác nhân: **Thiết bị giám sát (ESP32)** (chính); Nhân viên y tế (phụ — gán wearer)
  - Mô tả: thiết bị tự đăng ký vào hệ thống bằng MAC khi lần đầu kết nối, backend sinh `device_id` ngữ nghĩa.
  - Tiền điều kiện: tồn tại Organization + broker của deployment; thiết bị có SIM/mạng.
  - Luồng chính: (1) thiết bị đọc MAC eFuse; (2) kết nối MQTT, publish `config/status`; (3) backend gặp MAC lạ → sinh `esp32_eldercare_NN` + lưu MAC; (4) cập nhật `firmware_version` từ `fw_version`; (5) thiết bị hiện trên Dashboard.
  - Hậu điều kiện: thiết bị có `device_id` ngữ nghĩa, sẵn sàng để nhân viên gán wearer.

## F4 — Sửa lỗi nhỏ §2.2.4 (Gán thiết bị)
- Đoạn văn `subsection:2.2.4` (dòng ~113) và bảng `tab:uc_gan_thiet_bi` đang ghi *"nhập chiều cao bệnh nhân"* tại bước gán. **Sai** — chiều cao (`height_cm`) thuộc **hồ sơ wearer** (CRUD riêng, D-016), không nhập lúc gán.
- **Sửa:** đổi thành "hệ thống lấy chiều cao từ hồ sơ bệnh nhân đã chọn để tính sải bước/quãng đường". Bỏ node usecase `Nhập chiều cao bệnh nhân` (hoặc đổi thành `Lấy chiều cao từ hồ sơ wearer`).

---

## DEFINITION OF DONE
- [ ] F1 thêm liên kết actor Thiết bị ↔ uc2; F2 có 2 hình mới + đoạn văn; F3 có bảng đặc tả; F4 đã sửa.
- [ ] KHÔNG xuất hiện ý "người dùng nhập device_id thủ công"; nhất quán "MAC=khóa topic, device_id do backend sinh".
- [ ] Mọi `\label` mới được `\ref` trong text; không thêm `\usepackage` (tái dùng style sẵn có).
- [ ] Build `pdflatex -interaction=nonstopmode -halt-on-error 20225198_VuManhHung.tex` (×2) → EXIT=0; rasterize trang chứa 2 hình mới để mắt kiểm bố cục TikZ.
- [ ] Đẩy Overleaf bằng `ols`.

## Tham chiếu chéo
- Sơ đồ A11/A12 cũng được liệt kê trong `plans/report_missing_figures_plan.md` (mục A + F).
- Dữ kiện canonical: `architecture/DECISIONS.md` D-020, `architecture/backend.md` (mục MQTT Service / auto-provision), `architecture/overview.md` (MQTT topics).
