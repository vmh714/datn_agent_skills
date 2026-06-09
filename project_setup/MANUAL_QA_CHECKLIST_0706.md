# Checklist Test Logic Thủ Công (Browser) — Săn Bug

> Mục tiêu: tự bấm trên trình duyệt để tìm lỗi **logic** (không phải unit test).
> Quy ước mỗi case: **Thao tác → Kết quả đúng → 🐞 Bug cần soi.**
> Tick `- [x]` khi đúng; nếu sai, ghi chú ngay dưới dòng đó.

## Chuẩn bị
- [ ] Chạy `cd fall-detection/fall-detection && npm run dev`, mở `http://localhost:3000`.
- [ ] Có **2 tài khoản thuộc 2 tổ chức (org) khác nhau** để test phân quyền (mục J).
- [ ] Biết cách giả lập "té ngã":
  - Bật mock: `NEXT_PUBLIC_MOCK_MQTT=true` trong `.env.local` (mock tự bắn fall alert ~mỗi 120s), **hoặc**
  - Publish MQTT topic `eldercare/<device_id>/alert/fall` với payload `{"message":"...","confidence":0.95,"timestamp":...}`.
- [ ] Mở DevTools: **Console** (lỗi JS), **Network** (poll 30s/60s + PATCH `/resolve`), **Application → Cookies** (`auth_token`).

---

## A. Xác thực & proxy (auth gate)
- [ ] **Login đúng:** nhập user/mật khẩu đúng → vào `/`. 🐞 Soi: có set cookie `auth_token` không.
- [ ] **Login sai:** sai mật khẩu / user không tồn tại → hiện lỗi đỏ, KHÔNG vào trong. 🐞 Soi: nút "Đăng nhập" có nhả lại trạng thái loading.
- [ ] **Chặn route:** đăng xuất / xoá cookie `auth_token` rồi gõ thẳng `/`, `/alerts`, `/devices` → **bị đá về `/login`**.
- [ ] **Đã login vào /login:** đang đăng nhập rồi mở `/login` → **tự về `/`**.
- [ ] **Logout (Sidebar):** bấm icon LogOut → về `/login` + cookie `auth_token` bị xoá.
- [ ] **Token hết hạn:** Application→Cookies đặt `auth_token` = một JWT `exp` quá khứ → mở `/` → **bị đá `/login` và cookie bị xoá**.
- [ ] **Giữ phiên:** đang đăng nhập, refresh (F5) → vẫn ở trong, không bị đá ra.
- [ ] 🐞 **Vòng lặp redirect:** không bị nhấp nháy login↔home; ảnh tĩnh `/public/*` (nếu có) vẫn tải được.

## B. Dashboard (`/`)
- [ ] Load lần đầu: thấy **skeleton 4 card** rồi mới ra dữ liệu.
- [ ] Không có thiết bị → hiện "Không có thiết bị nào được kết nối".
- [ ] Click 1 device card → mở **PatientProfile** bên phải; click device khác → đổi panel; click lại → đóng.
- [ ] Status badge đúng màu: ONLINE (xanh) / ALERT (đỏ) / LOW (cam, pin<20) / OFFLINE (xám).
- [ ] Thanh battery khớp % và đổi màu (xanh / cam<20 / đỏ khi alert).
- [ ] Link "View IMU Log" → `/data-collection`; "Activity History"/"Detailed Vitals"/"Edit Health Records" → `/device/{id}`.
- [ ] Dòng "X devices online" đếm **đúng số online thực tế**.

## C. Luồng té ngã (TRỌNG TÂM)
- [ ] Giả lập fall → **overlay đỏ full màn hình bật ngay**, hiện đúng device + message + thời gian.
- [ ] Chuông kêu khi **Settings → Âm thanh cảnh báo = bật**; tắt thì **không kêu**.
- [ ] "Bỏ qua tạm thời" → overlay ẩn; alert vẫn còn (chưa resolve).
- [ ] "Xác nhận cứu hộ" → overlay ẩn; trên `/alerts` dòng đó chuyển **"Đã xử lý"** trong ~1–2s.
- [ ] **CriticalAlertBanner** xuất hiện trên dashboard khi có fall chưa xử lý trong 24h; 3 nút (Resolve / Contact / Emergency) chạy đúng (toast).
- [ ] ⭐ **Không nhân đôi:** trên `/alerts` mỗi cú ngã chỉ **1 dòng** (không còn cặp "Cảnh báo..." + "confidence: %"). 🐞 Nếu thấy 2 dòng cùng giờ là regression.

## D. Trang cảnh báo (`/alerts`)
- [ ] Filter **Thiết bị** → chỉ hiện alert của device đó.
- [ ] Filter **Loại** (Té ngã / Pin yếu / Mất kết nối) → lọc đúng.
- [ ] Filter **Ngày** → chỉ hiện alert đúng ngày.
- [ ] "Xóa bộ lọc" → reset cả 3 filter.
- [ ] Nút "Xác nhận" trên 1 dòng → chuyển "Đã xử lý", nút biến mất; số "X chờ xử lý" giảm 1.
- [ ] Chart 7N/14N/30N: đổi nút → chart cập nhật; empty → hiện "chưa có dữ liệu".
- [ ] Bảng rỗng (filter không khớp) → "Không có cảnh báo nào phù hợp".

## E. Thiết bị (`/devices`)
- [ ] "Đăng ký thiết bị": để trống Device ID / Firmware → **báo lỗi đỏ**, không submit.
- [ ] Đăng ký device_id **đã tồn tại** → lỗi (400 "already registered").
- [ ] Đăng ký mới hợp lệ → xuất hiện trong bảng (status theo toggle).
- [ ] Sửa (Pencil): Device ID **bị khoá**, chỉ đổi Firmware/active → lưu OK.
- [ ] Xoá (Trash): bấm lần 1 → "Xác nhận xóa?"; bấm lần 2 → xoá; "Hủy" → không xoá.
- [ ] Dropdown người đeo: gán wearer / "Không gán" → cập nhật cột tương ứng ở cả `/devices` và `/wearers`.

## F. Bệnh nhân (`/wearers`)
- [ ] Thêm: tên < 2 ký tự → lỗi; chiều cao ngoài 100–250 → lỗi.
- [ ] Thêm hợp lệ → xuất hiện trong bảng.
- [ ] Sửa tên/chiều cao → lưu OK.
- [ ] Xoá (xác nhận 2 bước).
- [ ] Gán thiết bị từ phía wearer → đồng bộ với trang `/devices`.

## G. Chi tiết thiết bị (`/device/[id]`)
- [ ] Sửa Tên / Tần số lấy mẫu (50/100/200) / Ngưỡng té ngã (SVM) → "Lưu cấu hình" → lưu OK ("Đang lưu…").
- [ ] Lịch sử cảnh báo của đúng device hiển thị.
- [ ] Mở `/device/<id-không-tồn-tại>` → xử lý gọn (không crash trắng trang).

## H. Thu thập dữ liệu (`/data-collection`)
- [ ] Dropdown chỉ liệt kê **device online**; chọn device → badge MQTT "Live".
- [ ] "Bắt đầu ghi" → chart Accel/Gyro chạy realtime; "Số mẫu" + "Thời gian" tăng.
- [ ] Đổi nhãn (Đi bộ/Đứng yên/Chạy/Té ngã) — bị **khoá khi đang ghi**.
- [ ] "Dừng & Lưu CSV" → tải file CSV `{label}_{timestamp}.csv` + toast "Đã lưu X samples".
- [ ] Ghi >5 phút → **tự dừng** + toast giới hạn.
- [ ] 🐞 Rời trang khi đang ghi rồi quay lại → không kẹt trạng thái recording, không rò kết nối.

## I. Cài đặt (`/settings`)
- [ ] Sửa Broker URL / Username / Password → tự lưu (reload vẫn còn).
- [ ] Toggle hiện/ẩn mật khẩu (Eye) hoạt động.
- [ ] "Áp dụng & Kết nối lại" với broker **đúng** → badge "Kết nối thành công".
- [ ] Toggle "Âm thanh cảnh báo" → ảnh hưởng chuông ở mục C.

## J. Phân quyền đa tổ chức (2 tài khoản)
- [ ] Đăng nhập tài khoản **org A** → chỉ thấy device/wearer/alert của org A.
- [ ] Đăng nhập tài khoản **org B** → chỉ thấy của org B; **không** thấy dữ liệu org A.
- [ ] 🐞 Soi Network: response `/devices/`, `/history/alerts`, `/wearers/` không chứa id của org kia.

## K. Tổng quát / biên
- [ ] Thu nhỏ cửa sổ (mobile) → layout không vỡ; Sidebar toggle (hamburger) chạy.
- [ ] Mọi trang đều có loading skeleton + empty state hợp lý.
- [ ] Ngắt mạng tới broker → badge TopNav chuyển **"MQTT: Reconnecting..."**; nối lại → "Live".
- [ ] Console không có lỗi đỏ trong suốt quá trình.

---

## 🔴 BUG NGHI NGỜ — SOI KỸ (ưu tiên cao, suy ra từ code)

> Đây là các chỗ logic dễ sai nhất. Repro đúng các bước để lộ bug.

- [ ] **1. Ack NHẦM alert (HIGH).** Tạo **≥2 alert chưa xử lý** (vd 2 cú ngã liên tiếp). Bấm "Xác nhận" trên **alert CŨ** (overlay/banner/bảng).
  🐞 Vì alert live mang `id = crypto.randomUUID()` không khớp DB → backend `/resolve` rơi vào fallback "resolve cái **mới nhất**". Dấu hiệu sai: alert vừa bấm vẫn "Chờ xử lý", còn alert **khác** lại thành "Đã xử lý".
- [ ] **2. Ack rồi nhưng DB chưa resolve (HIGH).** Bấm "Xác nhận cứu hộ" trên overlay → overlay tắt. Throttle mạng / để PATCH lỗi → **reload trang**.
  🐞 Nếu overlay/alert hiện lại = ack chỉ ăn ở local store, DB chưa resolve. Soi Network: `PATCH /api/v1/history/alerts/<uuid>/resolve` trả gì.
- [ ] **3. Status sai theo timezone / mốc 24h (MEDIUM).** Có 1 fall alert ~23–25h trước. Đổi **timezone máy** (vd UTC+12) → reload dashboard.
  🐞 DeviceCard tính `hoursSince` bằng `Date.now() - new Date(timestamp)`; soi xem badge ALERT bật/tắt có đúng quanh mốc 24h.
- [ ] **4. Battery bị ghi đè khi pin 0 / telemetry cũ (MEDIUM).** Cho MQTT gửi `battery_pct: 0`.
  🐞 Card hiển thị 0% (đúng) hay quay về giá trị API cũ? Chuyển qua device khác rồi quay lại — giá trị MQTT vs API có lệch/đứng yên sai không.
- [ ] **5. Lọc ngày lệch timezone (MEDIUM).** Tạo alert gần **ranh giới nửa đêm UTC↔giờ VN** (vd 00:30 UTC). Vào `/alerts` chọn date filter theo **ngày local**.
  🐞 `a.timestamp.startsWith("YYYY-MM-DD")` so trên ISO-UTC → alert có thể **biến mất** khỏi ngày mà người dùng nghĩ nó thuộc về.
- [ ] **6. Reconfigure broker không báo lỗi (MEDIUM).** Settings → đổi Broker URL thành **sai** → "Áp dụng & Kết nối lại".
  🐞 Có hiện badge "Kết nối thất bại" không? Badge TopNav có **kẹt "Reconnecting..." mãi** mà không phản hồi lỗi không.
- [ ] **7. Mốc online 60s (MEDIUM).** Để device gửi telemetry thưa (>60s) hoặc throttle mạng.
  🐞 Badge có **nhấp nháy offline** dù thiết bị vẫn sống (do `last_online` quá 60s + poll 60s trễ).
- [ ] **8. Settings stale từ localStorage (LOW).** Đổi `.env` broker rồi rebuild.
  🐞 Settings vẫn hiển thị URL **cũ** (do `persist` localStorage `vitalsguard-settings` đè giá trị `.env`).
- [ ] **9. Ref-count MQTT khi điều hướng (LOW).** Dashboard → Data-collection → quay lại nhiều lần; thử Fast Refresh (sửa file khi đang ở data-collection).
  🐞 Badge MQTT có rớt lâu / data realtime có mất hẳn không (kết nối bị teardown sớm).
- [ ] **10. Chart toàn 0 (LOW).** Khoảng thời gian mà mọi ngày = 0 bước/0 km.
  🐞 Chart vẽ đường ở mức 0 thay vì hiện "chưa có dữ liệu" → gây hiểu nhầm "đã cập nhật, đứng yên".

---

### Ghi chú
- Bug #1 và #2 cùng gốc: **alert live (id client) ≠ alert DB (id server)**. Đây là hạn chế đã biết, chưa sửa — nếu muốn chuẩn cần đồng bộ id live↔DB (hoặc ack theo `(device_id, timestamp)`).
- Phần nhân đôi alert (mục C ⭐) đã được fix; checklist này dùng để **xác nhận không tái phát**.
