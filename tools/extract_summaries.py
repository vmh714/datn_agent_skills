import glob
import os
import sys
sys.stdout.reconfigure(encoding='utf-8')

files = glob.glob(r"d:\datn\report\science_thesis_md\*_parsed.md")
for f in files:
    with open(f, 'r', encoding='utf-8') as file:
        content = file.read()
        summary = content.split("### BibTeX:")[0]
        print(f"=== {os.path.basename(f)} ===")
        print(summary.strip())
        print()
