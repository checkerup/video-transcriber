@echo off
chcp 65001 >nul 2>&1
cd /d "%~dp0.."
echo =======================================================
echo   Video Transcriber — Setup Speaker Diarization Extra
echo =======================================================
echo.

if not exist "venv" (
    echo [INFO] Virtual environment not found. Automatically running standard installation first...
    call install.bat
)

if not exist "venv" (
    echo [ERROR] Virtual environment creation failed. Can't install diarization packages.
    pause
    exit /b 1
)

call venv\Scripts\activate.bat
echo Installing speaker diarization extra (pyannote.audio)...
pip install -e .[diarization]

echo.
echo =======================================================
echo   Installation Complete!
echo.
echo   NOTE: To use speaker diarization, you must configure:
echo   1. Hugging Face account and accept models terms:
echo      - https://huggingface.co/pyannote/speaker-diarization-3.1
echo      - https://huggingface.co/pyannote/segmentation-3.0
echo   2. Set your Hugging Face token in config.yaml under:
echo      diarization:
echo        enabled: true
echo        auth_token: "your_token_here"
echo =======================================================
echo.
pause
