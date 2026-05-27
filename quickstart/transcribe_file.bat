@echo off
chcp 65001 >nul 2>&1
cd /d "%~dp0.."
set PYTHONPATH=src

echo ==============================================
echo   Video Transcriber — Transcribe File
echo ==============================================
echo.

set "filepath=%~1"
if "%filepath%"=="" (
    echo Drag and drop your audio or video file here and press Enter,
    set /p filepath="or enter the absolute path manually: "
)

:: Strip surrounding quotes if any
if not "%filepath%"=="" (
    set filepath=%filepath:"=%
)

if "%filepath%"=="" (
    echo [ERROR] No file path specified.
    pause
    exit /b 1
)

if not exist "venv" (
    echo [WARN] Virtual environment not found. Automatically running setup...
    call install.bat
)

call venv\Scripts\activate.bat
echo.
echo Processing: "%filepath%"
echo.
python -m video_transcriber.main --file "%filepath%"
echo.
pause
