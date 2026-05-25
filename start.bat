@echo off
chcp 65001 >nul 2>&1
title Video Transcriber

set PYTHONPATH=src

if not exist "venv" (
    echo [INFO] Virtual environment not found. Automatically running installation...
    call install.bat
    goto :run_start
)

call venv\Scripts\activate.bat
python -c "import yaml, watchdog, requests" >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [WARN] Missing required Python packages. Automatically running repair/installation...
    call install.bat
)

:run_start

call venv\Scripts\activate.bat

if "%1"=="" (
    echo Starting Video Transcriber daemon...
    echo Watching folder defined in config.yaml
    echo Press Ctrl+C to stop
    echo.
    python -m video_transcriber.main
) else (
    echo Processing single file: %1
    python -m video_transcriber.main --file "%1"
)

pause
