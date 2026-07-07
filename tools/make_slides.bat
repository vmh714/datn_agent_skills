@echo off
chcp 65001 >nul
echo ===================================================
echo   DATN SLIDE BUILDER (Extract ^& Build Pipeline)
echo ===================================================
echo.

echo [1/2] Extracting current manual coordinates from PPTX...
python -X utf8 extract_pptx.py > extracted_coordinates.log
if %errorlevel% neq 0 (
    echo [!] WARNING: Failed to extract. Is the PPTX file missing?
) else (
    echo [-] Success! Saved coordinates backup to: extracted_coordinates.log
)
echo.

echo [2/2] Rebuilding PPTX from Python source...
python build_slides.py
echo.

echo ===================================================
echo   DONE!
echo   Tip: Check 'extracted_coordinates.log' if you need
echo   to copy your manual drag-n-drop numbers into code.
echo ===================================================
pause
