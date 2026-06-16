import os
import sys
sys.stdout.reconfigure(encoding='utf-8')
import time
import json
import re
import pymupdf4llm
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

api_keys_file = r"d:\datn\datn_agent_skills\tools\api_key.txt"
with open(api_keys_file, "r") as f:
    API_KEYS = [line.strip() for line in f if line.strip()]

current_key_idx = 0

def configure_gemini():
    global current_key_idx
    genai.configure(api_key=API_KEYS[current_key_idx])
    print(f"[*] Đang sử dụng API Key thứ {current_key_idx + 1}")

configure_gemini()
MODEL_NAME = "gemini-3.5-flash"
model = genai.GenerativeModel(MODEL_NAME)

pdf_dir = r"d:\datn\report\science_thesis_pdf"
output_dir = r"d:\datn\report\science_thesis_md"
os.makedirs(output_dir, exist_ok=True)

pdf_files = [
    os.path.join(pdf_dir, "Development of artificial intelligence edge computing based.pdf")
]
print(f"Tìm thấy {len(pdf_files)} file PDF.")

prompt_template = """
Dưới đây là phần đầu của nội dung từ một bài báo khoa học.
Hãy trích xuất thông tin và CHỈ TRẢ VỀ JSON HỢP LỆ (không chứa markdown wrapper):
{{
  "summary": "Tóm tắt (3-4 câu tiếng Việt) mô tả bài báo.",
  "bibtex": "@article{{...}} (Mã BibTeX chuẩn xác)",
  "suggested_filename": "Ten_Bai_Bao.pdf (Dựa trên title, viết liền, không dấu, dùng dấu _)"
}}

Nội dung:
{content}
"""

def process_paper(pdf_path):
    global current_key_idx
    filename = os.path.basename(pdf_path)
    is_unclear_name = "s41598" in filename or "s2.0" in filename or "2507." in filename or "sensors" in filename or "IJTech" in filename
    
    print(f"\n[+] Đang xử lý: {filename}")
    try:
        print("  -> Đọc toàn bộ PDF bằng pymupdf4llm...")
        full_md_text = pymupdf4llm.to_markdown(pdf_path)
        
        snippet_for_ai = full_md_text[:15000]
            
        print("  -> Gửi tới Gemini API...")
        prompt = prompt_template.format(content=snippet_for_ai)
        
        for attempt in range(len(API_KEYS)):
            try:
                response = model.generate_content(prompt, safety_settings={
                        HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                        HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
                })
                
                raw_text = response.text.strip()
                if raw_text.startswith("```json"): raw_text = raw_text.replace("```json", "", 1)
                if raw_text.endswith("```"): raw_text = raw_text[::-1].replace("```"[::-1], "", 1)[::-1]
                
                data = json.loads(raw_text.strip())
                new_pdf_name = data.get("suggested_filename", filename)
                if not new_pdf_name.endswith(".pdf"): new_pdf_name += ".pdf"
                new_pdf_name = re.sub(r'[<>:"/\\|?*]', '', new_pdf_name)
                
                base_name = os.path.splitext(new_pdf_name)[0]
                output_path = os.path.join(output_dir, f"{base_name}_parsed.md")
                
                final_content = f"### Tóm tắt:\n{data['summary']}\n\n### BibTeX:\n```bibtex\n{data['bibtex']}\n```\n\n---\n\n## NỘI DUNG BÀI BÁO CHI TIẾT\n\n{full_md_text}"
                
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(final_content)
                    
                print(f"  -> Lưu kết quả thành công (Full text: {len(full_md_text)} chars): {output_path}")
                
                if is_unclear_name and new_pdf_name != filename:
                    new_pdf_path = os.path.join(pdf_dir, new_pdf_name)
                    if not os.path.exists(new_pdf_path):
                        os.rename(pdf_path, new_pdf_path)
                        print(f"  -> ĐÃ ĐỔI TÊN FILE: {filename} => {new_pdf_name}")
                
                return True
                
            except Exception as e:
                err_msg = str(e)
                if "429" in err_msg or "quota" in err_msg.lower():
                    current_key_idx = (current_key_idx + 1) % len(API_KEYS)
                    configure_gemini()
                    time.sleep(2)
                else:
                    print(f"  [X] Lỗi: {e}")
                    break
    except Exception as e:
        print(f"  [X] Lỗi: {e}")
        return False

for pdf in pdf_files:
    process_paper(pdf)
