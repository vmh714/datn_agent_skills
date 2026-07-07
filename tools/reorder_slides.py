import re
import os

filepath = r"d:\datn\datn_agent_skills\tools\build_slides.py"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

# Split the file into header + chunks
parts = content.split('\ns = slide()')
header = parts[0]
chunks = parts[1:]

# We want to re-attach 's = slide()' to each chunk
chunks = ['s = slide()' + c for c in chunks]

# Dictionary to map title substring to chunk
chunk_dict = {}
for i, c in enumerate(chunks):
    m = re.search(r'title\(s,\s*"([^"]+)"', c)
    if m:
        title = m.group(1)
        chunk_dict[title] = c
    else:
        # For the "Thank you" slide and other title-less slides
        if "Trân trọng cảm ơn" in c:
            chunk_dict["THANK_YOU"] = c
        else:
            chunk_dict[f"UNTITLED_{i}"] = c

# Modify the layouts for the engineering slides BEFORE reordering
def modify_chunk(title, old_c):
    if "Firmware hướng sự kiện & Máy trạng thái (FSM)" in title:
        c = re.sub(r'bullets\(s, \[\s*(.*?)\s*\], top=1.4, width=Inches\(5.0\)\)', 
                   r'bullets(s, [\n\g<1>\n], top=1.4)', old_c, flags=re.DOTALL)
        c = re.sub(r'image\(s, "fsm.png",.*?\)', r'image(s, "fsm.png", 2.5, 3.2, 5.0, 4.0)', c)
        return c
    if "Backend & Cơ sở dữ liệu kép" in title:
        c = re.sub(r'bullets\(s, \[\s*(.*?)\s*\], top=1.4, width=Inches\(5.0\)\)', 
                   r'bullets(s, [\n\g<1>\n], top=1.4)', old_c, flags=re.DOTALL)
        c = re.sub(r'image\(s, "erd.png",.*?\)', r'image(s, "erd.png", 2.0, 3.2, 6.0, 4.0)', c)
        return c
    if "Cơ chế đồng bộ cảnh báo lai (Hybrid Alert)" in title:
        c = re.sub(r'bullets\(s, \[\s*(.*?)\s*\], top=1.4, width=Inches\(5.0\)\)', 
                   r'bullets(s, [\n\g<1>\n], top=1.4)', old_c, flags=re.DOTALL)
        c = re.sub(r'image\(s, "sync.png",.*?\)', r'image(s, "sync.png", 2.5, 3.2, 5.0, 4.0)', c)
        return c
    if "Web App: Giám sát Realtime & Cảnh báo" in title:
        return '''s = slide(); title(s, "Web App: Giám sát Realtime & Cảnh báo")
bullets(s, [
    "Theo dõi trạng thái toàn bộ người bệnh theo thời gian thực.",
    "Cảnh báo té ngã toàn cục: popup khẩn cấp trên màn hình y tá.",
], top=1.4)
images_row(s, ["dashboard.png", "global_fall_alert.png"], top=3.0, height=3.8, total_w=9.0, gap=0.2, captions=["Realtime Dashboard", "Popup cảnh báo khẩn cấp"])
'''
    if "Web App: Quản lý thiết bị & Lịch sử" in title:
        return '''s = slide(); title(s, "Web App: Quản lý thiết bị & Lịch sử")
bullets(s, [
    "Lưu trữ chuỗi thời gian (InfluxDB) cho phép xem lại lịch sử chi tiết.",
    "Quản lý thiết bị/người bệnh, cấu hình ngưỡng (Threshold, Cooldown) từ xa.",
], top=1.4)
image(s, "device_vitals.png", 1.0, 3.0, 8.0, 4.0)
'''
    return old_c

for k in chunk_dict.keys():
    chunk_dict[k] = modify_chunk(k, chunk_dict[k])

# New Order
order = [
    "Nội dung trình bày",
    "Các sản phẩm thiết bị đeo thương mại tiêu biểu",
    "Đặt vấn đề & Khoảng trống nghiên cứu",
    "Ba đóng góp chính của đồ án",
    # ENGINEERING
    "Kiến trúc tổng quan hệ thống",
    "Firmware hướng sự kiện & Máy trạng thái (FSM)",
    "Backend & Cơ sở dữ liệu kép",
    "Cơ chế đồng bộ cảnh báo lai (Hybrid Alert)",
    "Web App: Giám sát Realtime & Cảnh báo",
    "Web App: Quản lý thiết bị & Lịch sử",
    # RESEARCH
    "Bài toán TinyML: hai ràng buộc đối nghịch",
    "Bộ dữ liệu SisFall & Tiền xử lý",
    "Phân tích phân bố gia tốc → chọn thang ±8 g",
    "Phân tích phân bố vận tốc góc → chọn thang ±500 dps",
    "Kỹ thuật cắt cửa sổ & tăng cường dữ liệu",
    "★ Chiến lược thiết kế nhãn 5 lớp",
    "Xử lý mất cân bằng & ngưỡng quyết định",
    "★ Các pha động học của một cú ngã",
    "★ Cơ chế xác nhận ngã hai pha (Post-Impact)",
    "Chiến lược chống báo giả 4 tầng",
    "Ba thế hệ tối ưu kiến trúc mô hình",
    "Depthwise Separable Conv & tăng tốc ESP-NN",
    "★ Kiến trúc đề xuất: v30_optimize (26.629 tham số)",
    "★ So sánh hiệu năng các kiến trúc mô hình (LSO)",
    "★ Ma trận nhầm lẫn của mô hình v30_optimize",
    "Kiểm định chéo dân số (KFold v6, Leave-Subjects-Out)",
    # EVALUATION
    "Kết quả hệ thống: Thiết bị đeo & Edge AI",
    "Kết quả hệ thống: Cảnh báo Cloud & Web App",
    "Demo hệ thống",
    "Thảo luận & Hạn chế",
    "Kết luận & Hướng phát triển",
    "THANK_YOU",
    "Phụ lục — Siêu tham số & Thang đo"
]

# Ensure we didn't miss any
missing = set(chunk_dict.keys()) - set(order)
if missing:
    print("MISSING CHUNKS:", missing)

new_content = header
for o in order:
    if o in chunk_dict:
        new_content += "\n" + chunk_dict[o]

# Finally, append the prs.save() at the end. Wait, the last chunk probably includes prs.save(OUT)
# Let's check the last chunk of the original to extract the footer
footer_split = new_content.split('if USING_TEMPLATE:')
if len(footer_split) > 1:
    # Meaning the footer was inside the Phụ lục chunk
    pass
else:
    # If not, let's just make sure the footer is attached
    footer = """
if USING_TEMPLATE:
    lst = prs.slides._sldIdLst
    for sid in _sldids_to_remove:
        rId = sid.get(qn('r:id'))
        prs.part.drop_rel(rId)
        lst.remove(sid)
    lst.remove(_cover_sldid)
    lst.insert(0, _cover_sldid)

prs.save(OUT)
print("SAVED:", OUT)
print("Slides:", len(prs.slides._sldIdLst), "| Template:", "HUST" if USING_TEMPLATE else "default(4:3)")
"""
    new_content += "\n" + footer

# We also need to strip any duplicated footers if it got captured in "Phụ lục"
# Let's clean the "Phụ lục" chunk
new_content = re.sub(r'(if USING_TEMPLATE:.*)', '', new_content, flags=re.DOTALL)
new_content += """
if USING_TEMPLATE:
    lst = prs.slides._sldIdLst
    for sid in _sldids_to_remove:
        rId = sid.get(qn('r:id'))
        prs.part.drop_rel(rId)
        lst.remove(sid)
    lst.remove(_cover_sldid)
    lst.insert(0, _cover_sldid)

# Try saving, if error, print it
try:
    prs.save(OUT)
    print("SAVED:", OUT)
    print("Slides:", len(prs.slides._sldIdLst), "| Template:", "HUST" if USING_TEMPLATE else "default(4:3)")
except PermissionError:
    print("PermissionError: Please close DATN_VuManhHung_slides.pptx first!")
"""

with open(filepath, "w", encoding="utf-8") as f:
    f.write(new_content)

print("Reorder completed!")
