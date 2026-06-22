# Quy Tắc Định Tuyến Vai Trò (Role Routing)

> Single source of truth cho việc "role nào dùng skill nào / slash command nào". File này được
> `CLAUDE.md` `@import` và các workflow trong `.agents/workflows/` tham chiếu. Khi đổi danh sách skill
> của một role, **chỉ sửa ở đây** (và `project_setup/agents_config.md` nếu cần thêm persona chi tiết).

## Bảng định tuyến

| Vai trò | Slash command | Skills kích hoạt | Đọc bắt buộc trước khi làm |
|---|---|---|---|
| **Solution Architect** | `/brainstorm` | `iot-system-architect-brainstormer`, `requirement-validator` | `architecture/PROJECT_MAP.md`, `architecture/overview.md`, `architecture/protocol.md`, `architecture/DECISIONS.md` |
| **Backend Developer** | `/backend` | `fastapi-iot-core`, `fastapi-route-generator`, `fastapi-iot-security`, `iot-database-manager`, `iot-testing-deployment`, `influxdb-query-manager`, `mqtt-to-db-bridge` | `architecture/backend.md`, schema tại `backend/app/schemas/` |
| **Frontend Developer** | `/frontend` | `shadcn-component-builder`, `mqtt-hook-generator`, `realtime-chart-config` | `architecture/frontend.md` |
| **Firmware Developer** | `/firmware` | `esp-idf-build-manager`, `esp-idf-sensor-driver`, `tinyml-wrapper`, `lte-mqtt-client-manager` | `architecture/firmware.md`, `CLAUDE_firmware.md` |
| **Git / Deploy** | `/deploy_repo` | `git-ops-manager` | `.gitignore` của workspace liên quan |
| **Thesis Writer** | `/write_chapter` | `latex_generation`, `resource_management` | `project_setup/thesis_writing_plan.md` |
| **Thesis Formatter** | `/latex_formatting` | `latex_generation` | `project_setup/thesis_writing_plan.md` |

## Nguyên tắc chung

1. **Luôn đọc trước khi code.** Mọi role bắt đầu bằng `architecture/PROJECT_MAP.md` để biết "cái gì ở đâu"
   (xem reading protocol trong [codebase_context.md](codebase_context.md)). Đừng grep/scan mò.
2. **Một fact sống một nơi.** `architecture/*` là nguồn chuẩn khi mâu thuẫn; component README chỉ trỏ tới
   header. Khi code lệch doc → code là chuẩn, sửa doc cho khớp.
3. **Cập nhật doc sau khi sửa.** Theo bảng trong [codebase_context.md](codebase_context.md) mục 2.
4. **Kích hoạt skill qua Skill tool** (Claude Code) hoặc cơ chế skill tương ứng (Antigravity) — không copy
   nội dung skill vào prompt.
