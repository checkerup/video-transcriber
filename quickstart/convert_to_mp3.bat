@echo off
chcp 65001 >nul 2>&1
cd /d "%~dp0.."
set PYTHONPATH=src

echo ==============================================
echo   Video Transcriber — Convert to MP3
echo ==============================================
echo.

set "filepaths=%*"
if "%filepaths%"=="" (
    echo Drag and drop one or more video files here and press Enter,
    echo or enter paths manually (separate multiple files with spaces):
    set /p filepaths="Paths: "
)

:: Strip surrounding quotes from the whole string if any (handles single drags)
if not "%filepaths%"=="" (
    set filepaths=%filepaths:"=%
)

if "%filepaths%"=="" (
    echo [ERROR] No files specified.
    pause
    exit /b 1
)

if not exist "venv" (
    echo [WARN] Virtual environment not found. Automatically running setup...
    call install.bat
)

call venv\Scripts\activate.bat
echo.
echo Converting to MP3: %filepaths%
echo.
python -m video_transcriber.main --convert-mp3 %filepaths%
echo.
pause
