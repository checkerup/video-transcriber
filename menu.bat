@echo off
chcp 65001 >nul 2>&1
title Video Transcriber

set PYTHONPATH=src

if not exist "venv" (
    echo [INFO] Virtual environment not found. Automatically running installation...
    call install.bat
    goto :run_menu
)

call venv\Scripts\activate.bat
python -c "import yaml, watchdog, requests" >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [WARN] Missing required Python packages. Automatically running repair/installation...
    call install.bat
)

:run_menu

:menu
cls
echo.
echo  ╔══════════════════════════════════════════════╗
echo  ║       Video Transcriber — Main Menu          ║
echo  ╚══════════════════════════════════════════════╝
echo.
echo  [1]  Start daemon              (watch folder)
echo  [2]  Process single file / audio (one-shot)
echo  [3]  Convert video(s) to MP3   (supports drag-and-drop)
echo  [4]  Screen recording          (manual, Ctrl+C stop)
echo  [5]  Watch process + record    (auto on program launch)
echo  [6]  Check hardware            (CPU/RAM/GPU)
echo  [7]  Re-run setup wizard
echo  [8]  Install autostart
echo  [9]  Uninstall autostart
echo  [10] Run setup/repair environment
echo  [11] Push to GitHub
echo  [0]  Exit
echo.

set /p choice="  Your choice: "

if "%choice%"=="1" goto daemon
if "%choice%"=="2" goto single
if "%choice%"=="3" goto convert
if "%choice%"=="4" goto record
if "%choice%"=="5" goto watchproc
if "%choice%"=="6" goto hardware
if "%choice%"=="7" goto wizard
if "%choice%"=="8" goto autostart_install
if "%choice%"=="9" goto autostart_uninstall
if "%choice%"=="10" goto setup
if "%choice%"=="11" goto github
if "%choice%"=="0" exit /b 0

echo  Invalid choice.
timeout /t 2 >nul
goto menu

:setup
echo.
echo  Running setup/repair...
call install.bat
pause
goto menu

:daemon
echo.
call venv\Scripts\activate.bat
echo  Starting daemon... Press Ctrl+C to stop.
echo.
python -m video_transcriber.main
pause
goto menu

:single
echo.
set /p filepath="  Enter file path (video/audio): "
call venv\Scripts\activate.bat
python -m video_transcriber.main --file "%filepath%"
pause
goto menu

:convert
echo.
set /p filepaths="  Enter video file path(s) (drag & drop files here): "
call venv\Scripts\activate.bat
python -m video_transcriber.main --convert-mp3 %filepaths%
pause
goto menu

:record
echo.
call venv\Scripts\activate.bat
echo  Starting screen recording... Press Ctrl+C to stop.
echo.
python -m video_transcriber.main --record
pause
goto menu

:watchproc
echo.
set /p procname="  Enter process name (e.g. Zoom.exe): "
call venv\Scripts\activate.bat
echo  Watching for %procname%... Press Ctrl+C to stop.
echo.
python -m video_transcriber.main --watch-process "%procname%"
pause
goto menu

:hardware
echo.
call venv\Scripts\activate.bat
python -m video_transcriber.main --check-hardware
pause
goto menu

:wizard
echo.
call venv\Scripts\activate.bat
python -m video_transcriber.main --setup
pause
goto menu

:autostart_install
echo.
call venv\Scripts\activate.bat
python -m video_transcriber.main --install-autostart
pause
goto menu

:autostart_uninstall
echo.
call venv\Scripts\activate.bat
python -m video_transcriber.main --uninstall-autostart
pause
goto menu

:github
echo.
echo  Checking GitHub auth...
gh auth status 2>nul
if %ERRORLEVEL% neq 0 (
    echo.
    echo  Not logged in. Starting login...
    echo.
    gh auth login
    if %ERRORLEVEL% neq 0 (
        echo  [ERROR] Login failed.
        pause
        goto menu
    )
)
echo.
set /p reponame="  Repository name [video-transcriber]: "
if "%reponame%"=="" set reponame=video-transcriber
echo.
echo  Creating repo '%reponame%' and pushing...
gh repo create %reponame% --public --source=. --push
if %ERRORLEVEL% neq 0 (
    echo  [ERROR] Failed. Maybe repo already exists?
    echo  Try: gh repo create %reponame% --public --source=. --push --force
)
pause
goto menu
