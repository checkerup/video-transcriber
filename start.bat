@echo off
chcp 65001 >nul 2>&1
title Video Transcriber

if not exist "venv" (
    echo [ERROR] venv not found. Run install.bat first.
    pause
    exit /b 1
)

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
