import os
import re
import subprocess
import fitz  # PyMuPDF

TEX_FILE = r"d:\datn\report\Do_an_tot_nghiep_Vu_Manh_Hung\Chuong\4_1_Phan_tich_yeu_cau.tex"
OUT_DIR = r"d:\datn\report\Do_an_tot_nghiep_Vu_Manh_Hung\Hinhve"
PDFLATEX = r"C:\TinyTeX\bin\windows\pdflatex.exe"

with open(TEX_FILE, 'r', encoding='utf-8') as f:
    content = f.read()

# Pre-defined preamble for standalone tikz
PREAMBLE = r"""\documentclass[tikz,border=2mm]{standalone}
\usepackage[utf8]{vietnam}
\usepackage{amsmath}
\usepackage{amssymb}
\usetikzlibrary{shapes.geometric, positioning, fit, arrows.meta, backgrounds, calc}
\tikzset{
    usecase/.style={draw, ellipse, align=center, minimum width=3cm, minimum height=0.95cm, inner sep=1pt, font=\small},
    ucsystem/.style={draw, rounded corners, inner xsep=1.1cm, inner ysep=0.5cm},
    assoc/.style={-},
    ucinc/.style={-{Latex[length=2mm]}, dashed},
    ucactorpic/.pic={
        \draw[thick] (0,0.55) circle (0.16);
        \draw[thick] (0,0.39) -- (0,-0.15);
        \draw[thick] (-0.28,0.22) -- (0.28,0.22);
        \draw[thick] (0,-0.15) -- (-0.22,-0.62);
        \draw[thick] (0,-0.15) -- (0.22,-0.62);
    },
}
\begin{document}
"""

figures = re.finditer(r'\\begin\{figure\}.*?\\end\{figure\}', content, re.DOTALL)

for fig_match in figures:
    fig_text = fig_match.group(0)
    # Find label
    label_match = re.search(r'\\label\{fig:(.*?)\}', fig_text)
    if not label_match:
        continue
    label = label_match.group(1)
    
    # Find tikzpicture
    tikz_match = re.search(r'\\begin\{tikzpicture\}(.*?)\\end\{tikzpicture\}', fig_text, re.DOTALL)
    if not tikz_match:
        continue
    
    tikz_code = tikz_match.group(0)
    
    tex_code = PREAMBLE + tikz_code + "\n\\end{document}\n"
    
    with open("temp.tex", "w", encoding='utf-8') as f:
        f.write(tex_code)
    
    print(f"Compiling {label}...")
    subprocess.run([PDFLATEX, "-interaction=nonstopmode", "temp.tex"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    if os.path.exists("temp.pdf"):
        doc = fitz.open("temp.pdf")
        pix = doc[0].get_pixmap(dpi=300)
        out_png = os.path.join(OUT_DIR, f"{label}.png")
        pix.save(out_png)
        print(f"Saved {out_png}")
        doc.close()
    else:
        print(f"Failed to compile {label}")
