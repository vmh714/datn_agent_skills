---
description: "Workflow cho vai trò Frontend: Phát triển giao diện React/Next.js 16 (App Router) kết hợp Turbopack và UI/UX Sleek/Premium."
---

# Frontend Workflow

Sử dụng workflow này khi thực hiện các tác vụ phát triển giao diện, cập nhật trang, cấu hình định tuyến, hoặc tối ưu hóa trải nghiệm người dùng trong thư mục `d:\datn\frontend`.

## 🎨 Kỹ năng cốt lõi (Skills)

1. **Next.js conventions (App Router)**:
   - Sử dụng mô hình Server Components mặc định cho các thành phần tĩnh để tối ưu hóa hiệu năng tải trang.
   - Chỉ dùng `'use client'` cho các component cần tương tác động (state, hook, event listener).
   - Tổ chức cấu trúc thư mục dạng `app/` chặt chẽ, tối ưu hóa dynamic routing và loading/error states.

2. **Aesthetics & Premium UI/UX**:
   - Sử dụng hệ màu sắc hài hòa (curated palette), hỗ trợ cả Sleek Dark Mode.
   - Thiết kế giao diện responsive linh hoạt (Mobile-first hoặc Desktop-first tùy theo yêu cầu của trang dashboard).
   - Tích hợp các hiệu ứng hover nhẹ nhàng, micro-animations và transitions mượt mà để tăng trải nghiệm người dùng.
   - Không sử dụng ảnh giả (placeholder). Thay vào đó, sử dụng các icon trực quan (như Lucide React) hoặc tạo asset thực tế.

3. **API Integration**:
   - Thực hiện fetch dữ liệu qua các API Service đã được định nghĩa trong `services/`.
   - Xử lý tốt các trạng thái: Loading (skeleton loader), Error (thông báo thân thiện), Empty (giao diện trống đẹp mắt).

## 📋 Hướng dẫn thực thi

1. **Xác định Yêu Cầu**: Đọc kỹ thiết kế giao diện hoặc API contract cần tích hợp.
2. **Kiểm tra môi trường**: Làm việc hoàn toàn trong thư mục `d:\datn\frontend`.
3. **Phát triển & Tối ưu**:
   - Tạo/cập nhật CSS toàn cục trong `index.css` hoặc sử dụng CSS Modules/Tailwind nếu được cấu hình.
   - Thiết kế các reusable components trước khi lắp ghép vào page hoàn chỉnh.
4. **Kiểm tra**: Chạy build nhanh để đảm bảo Next.js biên dịch thành công mà không có lỗi TypeScript/ESLint:
   ```bash
   npm run build
   ```
