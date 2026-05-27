@echo off
chcp 65001 >nul 2>&1
cd /d "%~dp0.."
set PYTHONPATH=src

echo ==============================================
echo   Video Transcriber — Setup Wizard
echo ==============================================
echo.

if not exist "venv" (
    echo [WARN] Virtual environment not found. Automatically running setup...
    call install.bat
)

call venv\Scripts\activate.bat
python -m video_transcriber.main --setup
echo.
pause
