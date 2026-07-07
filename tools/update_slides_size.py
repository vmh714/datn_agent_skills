import re

with open('build_slides.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Add note function
if 'def note(' not in content:
    note_func = """
def note(s, text):
    notes_slide = s.notes_slide
    notes_slide.notes_text_frame.text = text

"""
    content = content.replace("def bullets(", note_func + "def bullets(")

# Change default size in bullets
content = re.sub(r'def bullets\(s, items, left=0\.6, top=1\.55, width=None, height=None, size=\d+', 'def bullets(s, items, left=0.6, top=1.55, width=None, height=None, size=24', content)

# Change all size=\d+ to size=24
content = re.sub(r'size=\d+', 'size=24', content)
content = re.sub(r'fs=\d+', 'fs=18', content)  # Also increase table font size a bit

# Update specific slides
content = re.sub(r'image\(s, "accel_distribution_2x2\.png".*\nbullets\(s, \[(.*?)\], top=5\.6, size=24\)',
    lambda m: f'image(s, "accel_distribution_2x2.png", 0.5, 1.4, 9.0, 5.8)\nnote(s, """{m.group(1)}""")', content, flags=re.DOTALL)

content = re.sub(r'image\(s, "gyro_distribution_2x2\.png".*\nbullets\(s, \[(.*?)\], top=5\.6, size=24\)',
    lambda m: f'image(s, "gyro_distribution_2x2.png", 0.5, 1.4, 9.0, 5.8)\nnote(s, """{m.group(1)}""")', content, flags=re.DOTALL)

content = re.sub(r'image\(s, "har_windows\.png".*\nbullets\(s, \[(.*?)\], top=5\.4, size=24\)',
    lambda m: f'image(s, "har_windows.png", 0.5, 1.4, 9.0, 5.8)\nnote(s, """{m.group(1)}""")', content, flags=re.DOTALL)

content = re.sub(r'image\(s, "fall_phases\.png".*\nbullets\(s, \[(.*?)\], size=24, top=5\.5\)',
    lambda m: f'image(s, "fall_phases.png", 0.5, 1.4, 9.0, 5.8)\nnote(s, """{m.group(1)}""")', content, flags=re.DOTALL)

content = re.sub(r'bullets\(s, \[(.*?)\], size=24, top=1\.5, width=Inches\(9\.0\)\)\nimage\(s, "model_evolution\.png", .*?\)',
    lambda m: f'image(s, "model_evolution.png", 0.5, 1.4, 9.0, 5.8)\nnote(s, """{m.group(1)}""")', content, flags=re.DOTALL)

# Slide 18 updates
# Need to specifically replace Slide 18 bullets with note and resize image
slide_18_old = """], left=0.7, top=1.55, width=8.6, height=1.6, fs=18)
image(s, "confusion_matrix_v30_opt_espnn_ON_sram_firmware.png", 3.2, 3.35, 3.6, 3.05)
bullets(s, [
    "v30_optimize: acc ~ TCN nhưng nhanh ~180× (11 ms « 500 ms); F1-Trans 0,799→0,907→0,945 (kd2); "
    "INT8 gần như không suy giảm.",
], size=24, top=6.55)"""

slide_18_new = """], left=0.7, top=1.4, width=8.6, height=1.8, fs=18)
image(s, "confusion_matrix_v30_opt_espnn_ON_sram_firmware.png", 2.0, 3.3, 6.0, 4.0)
note(s, "v30_optimize: acc ~ TCN nhưng nhanh ~180× (11 ms « 500 ms); F1-Trans 0,799→0,907→0,945 (kd2); INT8 gần như không suy giảm.")"""
content = content.replace(slide_18_old, slide_18_new)

with open('build_slides.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Updated build_slides.py")
