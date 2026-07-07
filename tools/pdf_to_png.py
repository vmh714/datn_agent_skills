import fitz
import os

pdf_path = "v30opt.pdf"
if not os.path.exists(pdf_path):
    print("PDF not found!")
    exit(1)

doc = fitz.open(pdf_path)
page = doc.load_page(0)
pix = page.get_pixmap(dpi=300)
png_path = r"d:\datn\report\Do_an_tot_nghiep_Vu_Manh_Hung\Hinhve\v30opt_architecture.png"
pix.save(png_path)
print(f"Saved PNG to {png_path}")
