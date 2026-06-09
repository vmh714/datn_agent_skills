# 🖥️ Eldercare Monitoring Dashboard (Frontend)

> **Trạng thái**: Đang phát triển (UI hòm hòm, đang tích hợp MQTT/API)

## 1. Tổng quan Kiến trúc
Ứng dụng Web dành cho nhân viên y tế giám sát hệ thống thiết bị chống té ngã trong thời gian thực.
- **Framework**: Next.js 16 (App Router) + Turbopack
- **Styling**: Tailwind CSS 4 + Shadcn UI (Radix UI)
- **State Management**: TanStack Query v5 (Server State) + Zustand (Local/Real-time State).

## 2. Các luồng dữ liệu chính
- **REST API (Fetch/Axios)**: Giao tiếp với Backend FastAPI để lấy danh sách thiết bị, lịch sử cảnh báo và cấu hình. *(Lưu ý: Không gọi trực tiếp DB)*.
- **MQTT.js (WebSockets)**: Kết nối trực tiếp tới Broker (Topic `eldercare/+/alert/fall`) để hiển thị cảnh báo đỏ toàn màn hình (Overlay) và phát chuông báo động với độ trễ dưới 1s.

## 3. Các Route cốt lõi
- `/` (Dashboard): Lưới thiết bị (Device Grid) hiển thị trạng thái Online/Offline/Pin và Overlay cảnh báo tức thời.
- `/wearers`: Quản lý hồ sơ bệnh nhân và gán thiết bị (Yêu cầu nhập chiều cao để tính quãng đường).
- `/alerts`: Lịch sử cảnh báo và biểu đồ phân tích hoạt động (Recharts).
- `/settings`: Cấu hình MQTT Broker và thông báo.

## 4. Cấu trúc thư mục (Dự kiến / Recommended)
```text
frontend/
├── src/
│   ├── app/          # Next.js 16 App Router (page.tsx, layout.tsx)
│   ├── components/   # UI Components (Shadcn UI, Recharts, DeviceGrid)
│   ├── hooks/        # Custom Hooks (useMqtt.ts, useDevices.ts)
│   ├── store/        # Zustand Store (Quản lý trạng thái Alert Overlay)
│   ├── services/     # API Client (Axios/Fetch gọi FastAPI)
│   └── proxy.ts      # Middleware/Proxy xử lý logic JWT và bảo mật Routes
├── package.json
└── tailwind.config.js
```

## 5. Quy chuẩn UI/UX
- Cảnh báo té ngã dùng màu đỏ `Red-600` nhấp nháy (Framer Motion).
- Trạng thái an toàn dùng màu xanh `Emerald-500`.
- Thiết kế tương thích (Responsive) tối ưu cho máy tính bảng (y tá cầm tay) và màn hình desktop lớn.
