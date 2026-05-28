---
description: Tự động chạy test/build, đóng gói thay đổi, tạo commit message chuẩn và push code của thư mục được chỉ định lên kho lưu trữ (Git repository).
---

1. Xác định thư mục/workspace mà người dùng muốn deploy (Tự động nhận diện dựa trên file thay đổi hoặc hỏi trực tiếp người dùng giữa các thư mục: backend, firmware, frontend, datn_agent_skills).
2. Kiểm tra trạng thái Git hiện tại của thư mục đó để xác định các file đã chỉnh sửa, thêm mới hoặc bị xóa:
   ```bash
   git status
   ```
3. Chạy kiểm tra chất lượng code hoặc biên dịch thử để đảm bảo code không bị lỗi trước khi đẩy lên repo:
   - Nếu là `backend`: Chạy `pytest` hoặc kiểm tra cú pháp Python.
   - Nếu là `frontend`: Chạy kiểm tra build nhanh.
   - Nếu là `firmware`: Chạy kiểm tra biên dịch thử nếu môi trường sẵn sàng.
4. Kích hoạt kỹ năng `git-ops-manager` để tự động soạn thảo một thông điệp commit (Commit Message) chuẩn chỉnh, mô tả chính xác những thay đổi kèm theo mốc thời gian và định dạng nghiệp vụ.
5. Thực hiện việc thêm tất cả thay đổi vào khu vực chờ (Staging Area):
   ```bash
   git add .
   ```
6. Tiến hành tạo Commit với thông điệp đã soạn thảo ở bước 4 (thay thế `<thông_điệp_soạn_ở_bước_4>` bằng nội dung cụ thể):
   ```bash
   git commit -m "<thông_điệp_soạn_ở_bước_4>"
   ```
7. Thực hiện đẩy nhánh code hiện tại lên GitHub/GitLab:
   ```bash
   git push origin HEAD
   ```
8. Báo cáo lại kết quả Deploy thành công cho người dùng kèm danh sách các file đã được đẩy lên repo.
