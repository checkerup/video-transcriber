@echo off
chcp 65001 >nul 2>&1
title Video Transcriber — Setup

echo ============================================
echo   Video Transcriber — Installation
echo ============================================
echo.

:: --- Python ---
where python >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Python not found. Install Python 3.10+ from https://python.org
    echo         Make sure to check "Add Python to PATH" during installation.
    pause
    exit /b 1
)

python --version
echo.

:: --- FFmpeg ---
where ffmpeg >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [WARN] FFmpeg not found. Installing via winget...
    winget install FFmpeg --accept-source-agreements --accept-package-agreements
    if %ERRORLEVEL% neq 0 (
        echo [ERROR] FFmpeg install failed. Install manually from https://ffmpeg.org/download.html
        pause
        exit /b 1
    )
    echo FFmpeg installed. Refreshing PATH...
    set "PATH=%PATH%;C:\Program Files\FFmpeg\bin"
)
echo FFmpeg: found
echo.

:: --- Virtual environment ---
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
    if %ERRORLEVEL% neq 0 (
        echo [ERROR] Failed to create venv
        pause
        exit /b 1
    )
)

echo Activating venv...
call venv\Scripts\activate.bat

:: --- Install dependencies ---
echo Installing Python dependencies...
pip install --upgrade pip
pip install -e .
if %ERRORLEVEL% neq 0 (
    echo [ERROR] pip install failed
    pause
    exit /b 1
)

:: --- Config ---
if not exist "config.yaml" (
    echo Creating config.yaml from example...
    copy config.example.yaml config.yaml
    echo.
    echo [IMPORTANT] Edit config.yaml and set:
    echo   - watch.folder      = folder to monitor
    echo   - processing.output_folder = where to save results
    echo   - telegram.bot_token  = your bot token from @BotFather
    echo   - telegram.chat_id    = your chat ID
    echo.
)

if not exist ".env" (
    echo Creating .env from example...
    copy .env.example .env
)

echo.
echo ============================================
echo   Setup complete!
echo   Run: start.bat (first run will launch setup wizard)
echo.
echo   CLI options:
echo     --check-hardware         detect hardware
echo     --setup                  re-run setup wizard
echo     --install-autostart      add to autostart
echo     --uninstall-autostart    remove from autostart
echo ============================================
pause
