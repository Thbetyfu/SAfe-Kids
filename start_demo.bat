@echo off
title SafeKid Flash 2.0 - Demo Launcher
color 0A
echo.
echo  =============================================
echo   🛡️  SafeKid Flash v2.0
echo  =============================================
echo.

REM Check Python
python --version 2>NUL
if errorlevel 1 (
    echo  ERROR: Python tidak ditemukan!
    echo  Install Python dari: https://python.org/downloads
    echo  Pastikan ceklis "Add python.exe to PATH" saat install!
    pause
    exit /b 1
)
echo  ✅ Python ditemukan!

REM Install dependencies (quiet)
pip install flask requests configparser -q --disable-pip-version-check

echo  ================================================
echo   🚀 Menjalankan Server...
echo.
echo   🌐 Kid UI    → http://localhost:5556/
echo   👨‍👩‍👧 Orang Tua → http://localhost:5556/parent
echo   📡 API       → http://localhost:5556/api/status
echo.
echo   ℹ️  Config   → config\safekid_default.conf
echo   ℹ️  Live USB → live-usb\BUILD_GUIDE.md
echo  ================================================
echo.
echo  Browser akan terbuka otomatis dalam 3 detik...
echo  (Tekan Ctrl+C untuk berhenti)
echo.

REM Open browser after 3 seconds
start /b cmd /c "timeout /t 3 /nobreak >nul && start http://localhost:5556"

REM Run server (using config file defaults, force demo mode)
python safekid\kid_ui\launcher_server.py --demo

pause
