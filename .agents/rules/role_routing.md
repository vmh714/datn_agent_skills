---
description: "Quy tắc định tuyến (Routing) theo các vai trò (Roles) trong dự án để giảm thiểu Context Switch và tiết kiệm Token."
---

# Role Routing Rules

Bạn đang hoạt động trong dự án chia thành 4 vai trò (roles) chính: **Brainstorm**, **Frontend**, **Backend**, **Firmware**.
Để đảm bảo tiết kiệm token và giữ cho context switch (chuyển đổi ngữ cảnh) ở mức tối thiểu:

1. **Nhận diện vai trò**: Trước khi thực hiện bất kỳ task nào, hãy xác định task đó thuộc vai trò nào trong 4 vai trò trên.
2. **Gọi đúng Workflow**:
   - Đối với **Brainstorm**: Gọi `/brainstorm` (kiến trúc, CSDL, thiết kế chung).
   - Đối với **Firmware**: Gọi `/firmware` (lập trình nhúng, C/C++, ESP-IDF, FSM, WiFi/BLE).
   - Đối với **Frontend**: Tự giới hạn ngữ cảnh vào thư mục `d:\datn\frontend` và chỉ tập trung vào UI/UX (hoặc gọi workflow tương ứng nếu có).
   - Đối với **Backend**: Tự giới hạn ngữ cảnh vào thư mục `d:\datn\backend` và chỉ tập trung vào API/Logic (hoặc gọi workflow tương ứng nếu có).
3. **Giữ Context Nhỏ (Small Context Switch)**:
   - Chỉ mở, đọc (`view_file`, `list_dir`) và tìm kiếm (`grep_search`) trong thư mục tương ứng với vai trò hiện tại. 
   - Tuyệt đối không đọc file của Frontend nếu đang làm task Backend hoặc Firmware, trừ khi thật sự cần xem xét hợp đồng API.
   - Giải quyết xong nhiệm vụ của một role rồi mới chuyển sang role khác. Không trộn lẫn code của 2 roles trong cùng một prompt phản hồi.
