@echo off
cd d:\datn\datn_agent_skills\tools
echo "Compiling LaTeX..." > run_all.log
pdflatex -interaction=nonstopmode v30opt.tex >> run_all.log 2>&1
echo "Installing PyMuPDF..." >> run_all.log
python -m pip install PyMuPDF >> run_all.log 2>&1
echo "Converting PDF to PNG..." >> run_all.log
python pdf_to_png.py >> run_all.log 2>&1
echo "Building Slides..." >> run_all.log
python build_slides.py >> run_all.log 2>&1
echo "Done!" >> run_all.log
