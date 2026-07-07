import sys

lines = open('build_slides.py', encoding='utf-8').readlines()
count = 1
for i, line in enumerate(lines):
    if line.startswith('s = slide()') or line.startswith('img_slide('):
        count += 1
        title = lines[i-1].strip()
        print(f"Slide {count}: {title}".encode('utf-8', errors='replace').decode('utf-8'))
