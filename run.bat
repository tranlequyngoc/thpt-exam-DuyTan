@echo off
chcp 65001 >nul
title X-EXAM v5.0
echo.
echo ============================================================
echo   X-EXAM v5.0 - He thong luyen thi THPT mien phi
echo ============================================================
echo.
echo [1] Cai dat thu vien can thiet...
pip install flask PyPDF2 python-docx pyngrok --quiet 2>nul
echo [2] Kiem tra...
python -c "import flask; print('  Flask OK')" 2>nul
echo [3] Khoi dong server...
echo.
echo  Mo trinh duyet: http://localhost:5000
echo  TK: admin/admin123 hoac student/123456
echo.
cd /d "%~dp0"
python start_public.py
pause
