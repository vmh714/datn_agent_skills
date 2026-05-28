---
description: "Workflow cho vai trò Backend: Phát triển API FastAPI, quản lý cơ sở dữ liệu Postgres/InfluxDB và xử lý logic nhận diện hành động (HAR) / phát hiện ngã."
---

# Backend Workflow

Sử dụng workflow này khi làm việc với API, xử lý dữ liệu cảm biến IMU, lưu trữ database hoặc tối ưu hóa hiệu năng máy chủ trong thư mục `d:\datn\backend`.

## ⚙️ Kỹ năng cốt lõi (Skills)

1. **FastAPI & Async Programming**:
   - Sử dụng các endpoint bất đồng bộ (`async def`) cho các tác vụ I/O bound (truy vấn DB, gọi API ngoài) để tránh block event loop.
   - Định nghĩa kiểu dữ liệu nghiêm ngặt sử dụng **Pydantic v2** schemas cho request/response.
   - Xử lý lỗi tập trung thông qua Custom Exception Handlers và trả về HTTP status code phù hợp.

2. **Database & Data Processing**:
   - Sử dụng SQLAlchemy / Tortoise ORM cho cơ sở dữ liệu quan hệ (Postgres) và InfluxDB Client cho dữ liệu chuỗi thời gian (cảm biến IMU).
   - Tối ưu hóa truy vấn DB (sử dụng indexing thích hợp, tránh N+1 query).
   - Xử lý mượt mà luồng dữ liệu thời gian thực (WebSockets) truyền tải tọa độ hoặc trạng thái ngã/HAR từ thiết bị IoT.

3. **Logging & Testing**:
   - Ghi log đầy đủ bằng module `logging` của Python để phục vụ việc debug khi vận hành thực tế.
   - Viết unit test và integration test bằng `pytest`.

## 📋 Hướng dẫn thực thi

1. **Xác định Yêu Cầu**: Xác định rõ API Endpoint cần viết, Schema dữ liệu đầu vào/đầu ra và các ràng buộc dữ liệu.
2. **Kiểm tra môi trường**: Làm việc hoàn toàn trong thư mục `d:\datn\backend`.
3. **Phát triển**: Tuân thủ PSR-8 (naming convention rõ ràng cho biến/hàm).
4. **Kiểm tra chất lượng**: Chạy kiểm tra cú pháp hoặc test suite trước khi bàn giao:
   ```bash
   pytest
   ```
