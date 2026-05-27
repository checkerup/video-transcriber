@echo off
chcp 65001 >nul 2>&1
cd /d "%~dp0.."
set PYTHONPATH=src

echo ==============================================
echo   Video Transcriber — Watch Process
echo ==============================================
echo.

set "procname=%~1"
if "%procname%"=="" (
    set /p procname="Enter the process name to watch (e.g. Zoom.exe): "
)

if "%procname%"=="" (
    echo [ERROR] No process name specified.
    pause
    exit /b 1
)

if not exist "venv" (
    echo [WARN] Virtual environment not found. Automatically running setup...
    call install.bat
)

call venv\Scripts\activate.bat
echo.
echo Watching for process: "%procname%"
echo Press Ctrl+C to stop watching.
echo.
python -m video_transcriber.main --watch-process "%procname%"
echo.
pause
