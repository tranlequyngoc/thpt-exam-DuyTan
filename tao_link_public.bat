@echo off
chcp 65001 > nul
cls
echo ============================================================
echo   X-EXAM v5.0 - TAO LINK CHIA SE CONG KHAI
echo ============================================================
echo.

REM Kiem tra da co authtoken chua
ngrok config check > nul 2>&1
findstr /C:"authtoken" "%LOCALAPPDATA%\ngrok\ngrok.yml" > nul 2>&1
if %errorlevel% NEQ 0 (
    echo [!] CHUA CO NGROK AUTHTOKEN!
    echo.
    echo  Lam theo cac buoc sau:
    echo  1. Truy cap: https://dashboard.ngrok.com/signup
    echo  2. Dang ky tai khoan MIEN PHI
    echo  3. Vao: https://dashboard.ngrok.com/get-started/your-authtoken
    echo  4. Copy token cua ban
    echo  5. Dan vao o duoi day va nhan Enter
    echo.
    set /p TOKEN=  Nhap authtoken cua ban: 
    ngrok config add-authtoken %TOKEN%
    echo.
    echo [OK] Da luu authtoken!
    echo.
)

echo [*] Dang khoi dong X-EXAM + tao link public...
echo.
cd /d "%~dp0"
python start_public.py

pause
