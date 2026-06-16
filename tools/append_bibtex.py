import os
import glob
import re
import sys
sys.stdout.reconfigure(encoding='utf-8')

md_dir = r"d:\datn\report\science_thesis_md"
output_bib = r"d:\datn\report\Do_an_tot_nghiep_Vu_Manh_Hung\Danh_sach_tai_lieu_tham_khao.bib"

with open(output_bib, "r", encoding="utf-8") as f:
    existing_bib = f.read()

md_files = glob.glob(os.path.join(md_dir, "*_parsed.md"))

new_blocks = []
for md_file in md_files:
    with open(md_file, "r", encoding="utf-8") as f:
        content = f.read()
        match = re.search(r'```bibtex\n(.*?)\n```', content, re.DOTALL)
        if match:
            block = match.group(1).strip()
            key_match = re.search(r'@\w+\{([^,]+)', block)
            if key_match:
                key = key_match.group(1).strip()
                if key not in existing_bib:
                    new_blocks.append(block)

if new_blocks:
    with open(output_bib, "a", encoding="utf-8") as f:
        f.write("\n\n% --- TỰ ĐỘNG THÊM TỪ PARSER ---\n\n")
        f.write("\n\n".join(new_blocks))
    print(f"Added {len(new_blocks)} new entries.")
else:
    print("No new entries.")
