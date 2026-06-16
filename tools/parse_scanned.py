import os
import sys
import json
import re
sys.stdout.reconfigure(encoding='utf-8')
import time
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

# Đọc API Key
api_keys_file = r"d:\datn\datn_agent_skills\tools\api_key.txt"
with open(api_keys_file, "r") as f:
    API_KEYS = [line.strip() for line in f if line.strip()]

genai.configure(api_key=API_KEYS[1]) # Dùng Key số 2 vừa được cấp
MODEL_NAME = "gemini-3.5-flash"
model = genai.GenerativeModel(MODEL_NAME)

target_pdf = r"d:\datn\report\science_thesis_pdf\Identification of optimal classifier and sensor placement for fall risk classification using IMU-based gait data.pdf"
output_dir = r"d:\datn\report\science_thesis_md"

prompt = """
Đây là một bài báo khoa học dưới dạng ảnh scan. Hãy đọc nội dung từ file PDF này và trích xuất thông tin.
Đầu tiên, trả về ĐÚNG MỘT KHỐI JSON (không markdown wrapper) với cấu trúc sau:
{
  "summary": "Tóm tắt (3-4 câu tiếng Việt)",
  "bibtex": "@article{...}",
  "suggested_filename": "Ten_Bai_Bao.pdf"
}

Ngay bên dưới khối JSON, hãy thêm chuỗi "---FULLTEXT---", và sau chuỗi đó, hãy trích xuất toàn bộ nội dung chữ (OCR) và bảng biểu mà bạn đọc được từ file PDF.
"""

print(f"[*] Đang upload file PDF scan lên Google Gemini...")
try:
    myfile = genai.upload_file(target_pdf)
    print(f"  -> Upload thành công: {myfile.uri}")
    
    print(f"[*] Đang yêu cầu AI xử lý (đọc OCR và trích xuất)...")
    response = model.generate_content(
        [myfile, prompt],
        safety_settings={
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        }
    )
    
    raw_text = response.text.strip()
    
    # Tách JSON và Fulltext
    if "---FULLTEXT---" in raw_text:
        json_part, full_text_part = raw_text.split("---FULLTEXT---", 1)
    else:
        json_part = raw_text
        full_text_part = "\n(AI không thể trích xuất toàn văn hoặc file quá dài)"
        
    json_part = json_part.strip()
    if json_part.startswith("```json"): json_part = json_part.replace("```json", "", 1)
    if json_part.endswith("```"): json_part = json_part[::-1].replace("```"[::-1], "", 1)[::-1]
    
    data = json.loads(json_part.strip())
    
    new_pdf_name = data.get("suggested_filename", "Scanned_Paper.pdf")
    if not new_pdf_name.endswith(".pdf"): new_pdf_name += ".pdf"
    new_pdf_name = re.sub(r'[<>:"/\\|?*]', '', new_pdf_name)
    
    base_name = os.path.splitext(new_pdf_name)[0]
    output_path = os.path.join(output_dir, f"{base_name}_parsed.md")
    
    final_content = f"### Tóm tắt:\n{data.get('summary', '')}\n\n### BibTeX:\n```bibtex\n{data.get('bibtex', '')}\n```\n\n---\n\n## NỘI DUNG BÀI BÁO CHI TIẾT (AI OCR)\n\n{full_text_part.strip()}"
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(final_content)
        
    print(f"[+] Lưu kết quả thành công: {output_path}")
    
except Exception as e:
    print(f"[X] Lỗi: {e}")
