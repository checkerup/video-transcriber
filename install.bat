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
    echo Python not in PATH. Searching standard directories...
    :: Scan User AppData folder
    for /d %%d in ("%USERPROFILE%\AppData\Local\Programs\Python\Python*") do (
        if exist "%%d\python.exe" (
            set "PATH=%%d;%%d\Scripts;%PATH%"
            echo Found Python in User AppData: %%d
            goto :python_found
        )
    )
    :: Scan Program Files
    for /d %%d in ("C:\Program Files\Python*") do (
        if exist "%%d\python.exe" (
            set "PATH=%%d;%%d\Scripts;%PATH%"
            echo Found Python in Program Files: %%d
            goto :python_found
        )
    )
    
    echo Python not found. Installing Python 3.12 via winget...
    winget install Python.Python.3.12 --accept-source-agreements --accept-package-agreements
    if %ERRORLEVEL% neq 0 (
        echo [ERROR] Python 3.12 installation failed. Please install it manually from https://python.org
        pause
        exit /b 1
    )
    
    :: Add installed Python path to local PATH environment variable
    for /d %%d in ("%USERPROFILE%\AppData\Local\Programs\Python\Python*") do (
        if exist "%%d\python.exe" (
            set "PATH=%%d;%%d\Scripts;%PATH%"
            echo Python path added: %%d
            goto :python_found
        )
    )
    for /d %%d in ("C:\Program Files\Python*") do (
        if exist "%%d\python.exe" (
            set "PATH=%%d;%%d\Scripts;%PATH%"
            echo Python path added: %%d
            goto :python_found
        )
    )
    
    echo [ERROR] Python was installed but python.exe was not found in standard paths. Please restart or check manually.
    pause
    exit /b 1
)
:python_found
python --version
echo.

:: --- FFmpeg ---
where ffmpeg >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo FFmpeg not found in PATH. Checking standard winget install path...
    if exist "%LOCALAPPDATA%\Microsoft\WinGet\Packages\Gyan.FFmpeg*" (
        for /d %%d in ("%LOCALAPPDATA%\Microsoft\WinGet\Packages\Gyan.FFmpeg*") do (
            if exist "%%d\ffmpeg.exe" (
                set "PATH=%%d;%PATH%"
                echo Found FFmpeg in Gyan.FFmpeg: %%d
                goto :ffmpeg_found
            )
            if exist "%%d\bin\ffmpeg.exe" (
                set "PATH=%%d\bin;%PATH%"
                echo Found FFmpeg in Gyan.FFmpeg bin: %%d\bin
                goto :ffmpeg_found
            )
        )
    )
    
    echo FFmpeg not found. Installing Gyan.FFmpeg via winget...
    winget install Gyan.FFmpeg --accept-source-agreements --accept-package-agreements
    if %ERRORLEVEL% neq 0 (
        echo [WARN] Gyan.FFmpeg install failed. Trying alternate FFmpeg package...
        winget install FFmpeg --accept-source-agreements --accept-package-agreements
    )
    
    for /d %%d in ("%LOCALAPPDATA%\Microsoft\WinGet\Packages\Gyan.FFmpeg*") do (
        if exist "%%d\ffmpeg.exe" (
            set "PATH=%%d;%PATH%"
            goto :ffmpeg_found
        )
        if exist "%%d\bin\ffmpeg.exe" (
            set "PATH=%%d\bin;%PATH%"
            goto :ffmpeg_found
        )
    )
    set "PATH=%PATH%;C:\Program Files\FFmpeg\bin"
)
:ffmpeg_found
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
python -m pip install --upgrade pip

:: Detect Nvidia GPU
nvidia-smi >nul 2>&1
if %ERRORLEVEL% == 0 (
    echo [INFO] NVIDIA GPU detected via nvidia-smi. Installing dependencies with CUDA support...
    pip install -e .[cuda]
) else (
    echo [INFO] No NVIDIA GPU detected. Installing standard dependencies...
    pip install -e .
)

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
