# 📘 FRONTEND IMPLEMENTATION ROADMAP (v2.0)

## 1. KIẾN TRÚC TỔNG THỂ (Core Architecture)

### 🛠️ Tech Stack Cố Định
- **Framework**: Next.js 16 (App Router) + Turbopack.
- **Styling**: Tailwind CSS 4 + Lucide Icons.
- **Components**: Shadcn UI (Radix UI).
- **State Management**: 
    - `Zustand`: Quản lý trạng thái UI (Sidebar, Theme) và Real-time Alerts.
    - `TanStack Query (v5)`: Đồng bộ dữ liệu với Backend FastAPI.
- **Giao tiếp**: 
    - `MQTT.js`: Kết nối WSS tới Broker để nhận cảnh báo tức thời (< 1s).
    - `Fetch/Axios`: Giao tiếp RESTful API với Backend (không gọi thẳng Supabase DB).

---

## 2. LỘ TRÌNH TRIỂN KHAI CÁC ROUTE (Route Implementation)

### 🏠 Route: `/` (Dashboard - Monitoring Hub)
*Mục tiêu: Giám sát tập trung 100+ thiết bị.*
- [ ] **Component: DeviceGrid**: Hiển thị danh sách thiết bị dạng Card.
    - Trạng thái: Online (Xanh), Offline (Xám), Alarm (Đỏ nháy).
- [ ] **Component: FallDetectionOverlay**: 
    - Tự động bật khi nhận message `fall_detected` từ MQTT.
    - Hiển thị Overlay đỏ toàn màn hình + Nút "Xác nhận cứu hộ".
    - **Audio**: Phát tiếng chuông cảnh báo (báo động).
- [ ] **Hook: useDevices**: Cấu hình `refetchInterval: 60000` (1 phút) để cập nhật Battery & Online Status.

### 👥 Route: `/wearers` (Patient Management)
*Mục tiêu: Quản lý hồ sơ người già.*
- [ ] **Feature: CRUD Patient**: Form thêm/sửa thông tin (Tên, Tuổi, Giới tính).
- [ ] **Field: height_cm**: Bắt buộc (Validation) để Backend tính toán độ dài bước chân.
- [ ] **Feature: Assign Device**: Giao diện kéo thả hoặc Select để gán Device ID cho Patient.

### 🔔 Route: `/alerts` (Alert History & Analytics)
*Mục tiêu: Truy vết và phân tích dữ liệu lịch sử.*
- [ ] **Table: AlertHistory**: Danh sách các vụ té ngã đã xảy ra, thời gian xử lý.
- [ ] **Chart: ActivityChart (Recharts)**:
    - Biểu đồ Bar/Area thống kê số bước chân (`walk_steps`, `run_steps`) theo ngày.
    - Biểu đồ Line thống kê Quãng đường di chuyển (km).

### ⚙️ Route: `/settings` (System Config)
- [ ] **Form: MQTT Config**: Cấu hình địa chỉ Broker, Username/Password.
- [ ] **Feature: Notification Settings**: Bật/tắt âm thanh cảnh báo.

---

## 3. CHUẨN HOÁ DỮ LIỆU (Data Handling)

### 🔄 API Layer (`/services/api.ts`)
Phải refactor để chuyển từ gọi Supabase sang gọi Backend FastAPI:
- `GET /api/v1/devices`: Lấy danh sách thiết bị kèm thông tin Patient.
- `GET /api/v1/history/steps`: Lấy dữ liệu chuỗi thời gian từ InfluxDB (thông qua BE).
- `POST /api/v1/auth/login`: Xác thực hệ thống (Đã xong).

### 📡 Real-time Logic (`/hooks/useMqtt.ts`)
- Topic đăng ký: `eldercare/+/alert/fall` và `eldercare/+/telemetry`.
- Khi có tin nhắn té ngã: Đẩy vào Zustand Store -> Kích hoạt Overlay -> Phát Sound.

---

## 4. QUY TẮC UX/UI (Design System)
- **Màu sắc**: 
    - Cảnh báo: `Red-600` (Hex: #DC2626).
    - An toàn/Online: `Emerald-500`.
- **Micro-animations**: Sử dụng `framer-motion` cho các thông báo trượt và hiệu ứng nhấp nháy của thiết bị đang báo động.
- **Responsive**: Ưu tiên hiển thị tốt trên máy tính bảng (cho y tá trực) và desktop (cho quản lý).
