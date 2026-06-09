# 🚀 Eldercare Backend Service

> **Trạng thái**: Đang phát triển (Còn thiếu một số API quản lý User)

## 1. Tổng quan Kiến trúc
Backend được xây dựng bằng **FastAPI** (Python), đóng vai trò là cầu nối xử lý logic và định tuyến dữ liệu giữa phần cứng (Firmware ESP32) và ứng dụng người dùng (Next.js Frontend). 

Hệ thống sử dụng mô hình **Dual-Database**:
- **PostgreSQL**: Lưu trữ dữ liệu quan hệ (Metadata, User, Device, Wearer, Alert History).
- **InfluxDB**: Lưu trữ dữ liệu chuỗi thời gian (Telemetry số bước chân, IMU Raw Data).

## 2. Giao thức truyền thông
Hệ thống kết hợp 2 lớp giao thức:
- **MQTT (Real-time Layer)**: Lắng nghe các topic `eldercare/+/telemetry` và `eldercare/+/alert/fall` để đồng bộ dữ liệu viễn trắc và cảnh báo té ngã từ thiết bị với độ trễ thấp nhất.
- **HTTP REST API (Management Layer)**: Cung cấp các endpoints chuẩn bảo mật JWT cho Frontend (CRUD Devices, Wearers, truy vấn lịch sử).

## 3. Cấu trúc thư mục (Dự kiến / Recommended)
```text
backend/
├── app/
│   ├── api/          # Các Router/Endpoints FastAPI (v1)
│   ├── core/         # Config, Security, JWT auth
│   ├── models/       # SQLAlchemy Models (Postgres)
│   ├── schemas/      # Pydantic Schemas (Validation)
│   ├── services/     # Logic nghiệp vụ (MQTT Handler, InfluxDB Sync)
│   └── main.py       # Entry point
├── requirements.txt
└── .env
```

## 4. Các luồng xử lý nổi bật
- **Hybrid Alert Sync**: API giải quyết cảnh báo (`/resolve`) có khả năng nhận diện UUID tạm thời từ Frontend và tự động fallback tìm bản ghi chưa xử lý mới nhất của thiết bị trong DB.
- **Batching IMU**: Mở API nhận lô dữ liệu (Batch) Base64 chứa mảng IMU raw phục vụ thu thập dữ liệu TinyML (Phase 1).
