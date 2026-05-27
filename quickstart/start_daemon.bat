@echo off
chcp 65001 >nul 2>&1
cd /d "%~dp0.."
set PYTHONPATH=src

echo ==============================================
echo   Video Transcriber — Start Daemon
echo ==============================================
echo.

if not exist "venv" (
    echo [WARN] Virtual environment not found. Automatically running setup...
    call install.bat
)

call venv\Scripts\activate.bat
echo Starting daemon (watching folders and processes)...
echo Press Ctrl+C to stop.
echo.
python -m video_transcriber.main
pause
