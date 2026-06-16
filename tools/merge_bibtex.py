import os
import glob
import re

md_dir = r"d:\datn\report\science_thesis_md"
tech_stack_file = r"C:\Users\vuman\.gemini\antigravity-ide\brain\5a334daa-49f6-4c61-9ab6-6771188ba433\tech_stack_references.md"
output_bib = r"d:\datn\report\Do_an_tot_nghiep_Vu_Manh_Hung\Danh_sach_tai_lieu_tham_khao.bib"

all_bibtex_blocks = []

# 1. Quét tất cả các bài báo khoa học đã parse
md_files = glob.glob(os.path.join(md_dir, "*_parsed.md"))
# Bỏ qua file bị thiếu nội dung cũ
md_files = [f for f in md_files if "Tai_lieu_thieu_noi_dung_van_ban" not in f and "Khong_The_Xac_Dinh_Ten_Bai_Bao" not in f]

for md_file in md_files:
    with open(md_file, "r", encoding="utf-8") as f:
        content = f.read()
        # Tìm block bibtex
        match = re.search(r'```bibtex\s*(.*?)\s*```', content, re.DOTALL)
        if match:
            all_bibtex_blocks.append(match.group(1).strip())

# 2. Thêm 2 bài báo y khoa
medical_bibtex = """
@online{who_falls_2021,
  author = {{World Health Organization}},
  title = {Falls - Fact Sheet},
  year = {2021},
  url = {https://www.who.int/news-room/fact-sheets/detail/falls},
  urldate = {2026-06-14}
}

@article{fleming2008longlie,
  title={The inability to get up after falling, subsequent time on floor, and summoning help: prospective cohort study in people over 90},
  author={Fleming, Jane and Brayne, Carol and {Cambridge City over-75s Cohort (CC75C) study collaboration}},
  journal={BMJ},
  volume={337},
  pages={a2227},
  year={2008},
  publisher={British Medical Journal Publishing Group},
  doi={10.1136/bmj.a2227}
}
"""
all_bibtex_blocks.append(medical_bibtex.strip())

# 3. Quét Tech Stack
with open(tech_stack_file, "r", encoding="utf-8") as f:
    content = f.read()
    match = re.search(r'```bibtex\s*(.*?)\s*```', content, re.DOTALL)
    if match:
        all_bibtex_blocks.append(match.group(1).strip())

# Ghi ra file
final_content = "% ============================================================\n"
final_content += "% DANH SÁCH TÀI LIỆU THAM KHẢO (TỔNG HỢP TỰ ĐỘNG)\n"
final_content += "% ============================================================\n\n"
final_content += "\n\n".join(all_bibtex_blocks)

with open(output_bib, "w", encoding="utf-8") as f:
    f.write(final_content)

print(f"Đã ghi thành công {len(md_files) + 15 + 2} tài liệu tham khảo vào file .bib!")
