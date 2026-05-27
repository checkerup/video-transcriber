@echo off
chcp 65001 >nul 2>&1
cd /d "%~dp0.."
set PYTHONPATH=src

echo ==============================================
echo   Video Transcriber — Record Screen
echo ==============================================
echo.

if not exist "venv" (
    echo [WARN] Virtual environment not found. Automatically running setup...
    call install.bat
)

call venv\Scripts\activate.bat
echo Starting manual screen recording...
echo Press Ctrl+C to stop recording.
echo.
python -m video_transcriber.main --record
echo.
pause
