# Project Memory — datn (IoT Eldercare Monitoring monorepo)

> File này là lớp tương thích cho **Claude Code**, chạy song song với bộ governance Antigravity ở `.agents/`.
> Nội dung gốc (rules, skills, workflows) được quản lý bằng git trong `datn-agent-skills/` và dùng chung qua **junction/hard link** (xem `datn-agent-skills/.claude/setup.ps1`). Máy này không bật Developer Mode nên không tạo được symlink — junction (thư mục) và hard link (file) đạt cùng mục tiêu single-source mà không cần quyền admin.

## Rules gốc (single source of truth)

@../.agents/rules/role_routing.md
@../.agents/rules/codebase_context.md
@../.agents/rules/api_rate_limit.md

> **CẢNH BÁO QUAN TRỌNG TRƯỚC KHI LÀM TASK (ĐẶC BIẾT LÀ FIRMWARE):**
> Claude bắt buộc phải gọi công cụ đọc nội dung các file sau trước khi thảo luận hay code chức năng:
> 1. `datn-agent-skills/project_setup/architecture/overview.md`
> 2. `datn-agent-skills/project_setup/protocol.md`
> 3. `datn-agent-skills/project_setup/architecture/backend.md`
> 4. `datn-agent-skills/project_setup/architecture/frontend.md`
> 5. `datn-agent-skills/project_setup/architecture/firmware.md`
> 6. Code schema trong `backend/app/schemas/`
> Tuyệt đối không đoán mò cấu trúc. Phải đọc trước để đồng bộ tư duy!

---

## Adapter cho Claude Code

Phần dưới đây diễn giải lại các quy ước Antigravity sang đúng cách Claude Code vận hành. Khi rules/skills/workflows nhắc tới khái niệm Antigravity, ánh xạ như sau:

### 1. Ánh xạ công cụ (tool mapping)
- `view_file` / `list_dir` → dùng **Read** / **Glob**.
- `grep_search` → dùng **Grep**.
- "Kích hoạt kỹ năng `<X>`" / "gọi skill `<X>`" → gọi skill `<X>` qua **Skill tool** (skills đã được expose ở `.claude/skills/`).
- Slash command Antigravity = slash command Claude Code, **cùng tên**: `/brainstorm`, `/backend`, `/frontend`, `/firmware`, `/deploy_repo`, `/write_chapter`, `/latex_formatting`.

### 2. Ánh xạ đường dẫn (path mapping)
Các skill/workflow cũ hardcode đường dẫn ổ `d:` — **bỏ qua các path đó**, dùng thư mục tương ứng trong workspace đang mở (`c:\Users\hung.vumanh2\Documents\datn`):

| Path cũ (hardcode) | Dùng trong monorepo này |
|---|---|
| `d:\datn\backend`  → | `./backend`  |
| `d:\datn\frontend` → | `./frontend` |
| `d:\datn\firmware` → | `./firmware` |
| `d:\datn\datn_agent_skills` / `d:/FastAPI/datn/backend` → | `./datn-agent-skills`, `./backend` |

Tài liệu LaTeX (luận văn) nằm trong `./REPORT`.

### 3. Shell
Môi trường này là **Windows + PowerShell**. Nối nhiều lệnh bằng `;` (không dùng `&&`). Đây cũng là lưu ý đã ghi sẵn trong skill `git-ops-manager`.

### 4. Quan hệ với `.agents/`
- `.agents/` (Antigravity) **giữ nguyên, không sửa**. `.claude/commands` và `.claude/skills/*` là **junction** trỏ về cùng nội dung gốc trong `.agents/` → sửa một nơi, cả hai hệ thống cùng cập nhật.
- Skills ở `.claude/skills/` được làm phẳng (bỏ lớp category `fastapidev/`, `firmware/`, ...) nhưng nội dung `SKILL.md` là cùng file gốc trong `.agents/skills/`.

### 5. Quy ước tạo Plan
Khi người dùng yêu cầu tạo plan / checklist / kế hoạch triển khai cho bất kỳ tính năng hoặc task nào (kể cả khi đang ở **plan mode** của Claude Code), **bắt buộc** lưu file plan vào thư mục:
```
datn_agent_skills/plans/<tên_ngắn_gọn>.md
```
> Đây là đường dẫn THẬT trên ổ đĩa (thư mục gạch dưới `datn_agent_skills`, KHÔNG phải `datn-agent-skills`). Tính từ gốc workspace `d:\datn` → `d:\datn\datn_agent_skills\plans\`.
- Tên file: snake_case, mô tả rõ nội dung (vd: `ota_test_checklist.md`, `frontend_auth_plan.md`).
- Nếu plan mode chỉ định một file plan tạm ở nơi khác (vd `~/.claude/plans/...`), vẫn phải **đồng thời lưu/copy bản chính thức** vào `datn_agent_skills/plans/` theo quy ước trên.
- Không hỏi lại người dùng — tự động lưu vào đúng folder trên.
- Sau khi lưu, thông báo đường dẫn file để người dùng có thể mở kiểm tra.