# Kế hoạch: Tách nội dung slide ra Markdown (content-driven build)

> Mục tiêu: sửa **1 file Markdown** (`slides_content.md`) là tự sinh lại nội dung tương ứng
> trong `DATN_VuManhHung_slides.pptx`. Không phải sửa code Python nữa cho các thay đổi nội dung
> thông thường (tiêu đề, bullet, bảng, flow, ảnh, caption, speaker notes).

## Kiến trúc

```
slides_content.md   ──parse──►  build_slides.py  ──python-pptx──►  DATN_VuManhHung_slides.pptx
 (NỘI DUNG, sửa tay)            (RENDERER, giữ helper layout)       (KHÔNG sửa tay)
```

- `slides_content.md` = **nguồn nội dung duy nhất**. Mỗi slide 1 khối; mỗi phần tử là 1 directive block.
- `build_slides.py` = giữ nguyên toàn bộ helper layout (`title/bullets/image/images_row/table/flow/_box/divider/img_slide`) + thêm parser Markdown + vòng lặp render.
- `build_slides_legacy_imperative.py.bak` = bản imperative cũ (backup, không dùng).

## Cú pháp Markdown (tóm tắt — chi tiết ở đầu `slides_content.md`)

- Mở slide: `## <kind> | <title> [| <subtitle>]`  — kind ∈ `cover` | `divider` | `content`.
- Block trong slide: `### @<type> key=val key="val có dấu cách"` + các dòng nội dung bên dưới.
- Block types: `@bullets @image @images-row @table @flow @banner @notes @heading` (+ `@title/@subtitle` cho cover).
- Bullet cấp 2: thụt 2 dấu cách. Xuống dòng trong ô flow: dùng `\n`. Bảng: dòng `| a | b |`.

## Việc đã làm

- [x] Backup `build_slides.py` → `build_slides_legacy_imperative.py.bak`.
- [x] Tạo `tools/slides_content.md` (export 57 slide hiện tại).
- [x] Refactor `tools/build_slides.py` thành renderer đọc `slides_content.md`.
- [x] Build lại → xác nhận số slide == bản cũ.
- [x] Thêm RULE vào `slide_bao_ve_implementation_guide.md` + memory.

## Quy trình sửa slide từ nay

1. Sửa `datn_agent_skills/tools/slides_content.md`.
2. `cd /d/datn/datn_agent_skills/tools && python build_slides.py`.
3. Export PNG (recipe §2 guide) → Read verify.

## Lưu ý / giới hạn

- Toạ độ/kích thước là **thuộc tính tuỳ chọn** trên block; bỏ trống thì dùng default trong renderer.
  Sửa nội dung chữ thì KHÔNG cần đụng toạ độ. Chỉ chỉnh toạ độ khi bị tràn/đè footer.
- Thêm ảnh mới: đặt PNG vào `Hinhve/` rồi tham chiếu trong block `@image`/`@images-row`.
- Giữ RULE 1-ảnh: biểu đồ/UI/API = 1 ảnh/slide.
