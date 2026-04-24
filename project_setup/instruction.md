# [MASTER SPECIFICATION] HỆ THỐNG GIÁM SÁT NGƯỜI GIÀ & PHÁT HIỆN TÉ NGÃ (v2.0)

## 1. TỔNG QUAN DỰ ÁN
Hệ thống IoT đeo người (vị trí thắt lưng phía trước) giúp giám sát hành vi và phát hiện té ngã dựa trên cảm biến IMU. Hệ thống sử dụng kết nối 4G LTE ổn định, truyền dữ liệu về Cloud để quản lý tập trung và đưa ra cảnh báo thời gian thực trên Web Dashboard.

## 2. CHẾ ĐỘ HOẠT ĐỘNG (PROJECT PHASES)
- **PHASE 1: Data Collection & Training**: Firmware thu thập raw IMU (100Hz) chuyển về Backend để lưu trữ CSV và huấn luyện model TinyML.
- **PHASE 2: Edge Inference**: Deploy model TinyML lên ESP32S3. Thiết bị tự động nhận diện hành vi (HAR) và phát hiện té ngã (Post-impact fall detection) rồi gửi kết quả về Dashboard.

## 3. KIẾN TRÚC HỆ THỐNG (SYSTEM ARCHITECTURE)
```mermaid
graph TD
    subgraph "Edge Layer (ESP32S3 + MPU6050)"
        IMU[MPU6050 100Hz] --> FSM[System FSM]
        FSM --> HAR[TinyML Inference]
        FSM --> PDM[Pedometer Logic]
    end
    
    subgraph "Connectivity Layer"
        LTE[A7680C 4G LTE]
    end

    subgraph "Cloud Layer (FastAPI + DBs)"
        Broker[Private MQTT Broker]
        BE[FastAPI Server]
        Postgres[(PostgreSQL: Metadata)]
        Influx[(InfluxDB: Time-Series)]
    end

    subgraph "Application Layer (Next.js)"
        Dash[Web Dashboard]
    end

    FSM <--> LTE
    LTE <--> Broker
    Broker <--> BE
    BE <--> Postgres
    BE <--> Influx
    BE <--> Dash
    Broker <--> Dash
```

## 4. TECH STACK BẮT BUỘC
- **Front-end**: Next.js (App Router), Tailwind CSS, Shadcn UI, Zustand, Recharts, TanStack Query.
- **Back-end**: FastAPI, PostgreSQL, InfluxDB.
- **Firmware**: ESP-IDF (C), MPU6050 (I2C 100Hz), A7680C (4G LTE over AT Commands), TF Lite for MCU.

## 5. ĐẶC TẢ CHI TIẾT CÁC MODULE

### A. Firmware (Edge Logic)
- **Vị trí đeo**: Thắt lưng phía trước.
- **Phát hiện té ngã (Post-impact)**: 
    - Trigger khi phát hiện va chạm (High G peak).
    - Phân tích dữ liệu sau va chạm (Orientation check) để xác nhận trạng thái nằm bất động.
    - Thời gian phản hồi: < 1s.
- **Đếm bước chân (Pedometer)**:
    - Thuật toán nhận diện bước chân dựa trên dữ liệu Gia tốc.
    - Phân loại và đếm riêng biệt: `walk_steps` và `run_steps`.
    - Firmware KHÔNG tính quãng đường để tiết kiệm tài nguyên.
- **Xác thực & Metadata**: 
    - MQTT Auth qua tài khoản/mật khẩu lĩnh.
    - Nhận và lưu trữ `user_name` từ Cloud để nhúng vào tin nhắn cảnh báo.

### B. MQTT Communication (Schema chuẩn)
... (Chi tiết tại protocol.md)

### C. Backend (Data Management)
- **Phân quyền**: Vai trò `Manager` (Quản lý nhiều thiết bị). Thiết kế linh hoạt để mở rộng sang vai trò `Relative` (Người thân).
- **Xử lý dữ liệu**: 
    - Tính toán quãng đường: `Distance = (walk_steps * L_walk) + (run_steps * L_run)`. Trong đó các hệ số bước đi/chạy dựa trên chiều cao người dùng lưu trong PostgreSQL.
    - Lưu Telemetry và kết quả tính toán vào InfluxDB để vẽ lịch sử.

### D. Frontend (Dashboard)
- **Dashboard**: Giám sát 100 thiết bị đồng thời (hiển thị Grid/Table).
- **Alert System**: Overlay đỏ toàn màn hình + Âm thanh khi có tín hiệu té ngã. Stable 24/24.
- **History View**: Hiển thị số bước chân và quãng đường trong ngày hiện tại.

## 6. QUY CÁCH PHÁT TRIỂN
1. **Modularity**: Code Firmware và Backend phải chia module rõ ràng (VD: module nút nhấn dự phòng, module giao tiếp LTE tách biệt).
2. **Event-driven**: Sử dụng Event Loop và FSM để quản lý luồng xử lý, tránh blocking code.
3. **Strict Scope**: Không thêm tính năng ngoài Đặc tả (ví dụ: GPS, Bluetooth) để đảm bảo ổn định 4G LTE.