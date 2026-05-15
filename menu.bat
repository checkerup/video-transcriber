@echo off
chcp 65001 >nul 2>&1
title Video Transcriber

:menu
cls
echo.
echo  ╔══════════════════════════════════════════════╗
echo  ║       Video Transcriber — Main Menu          ║
echo  ╚══════════════════════════════════════════════╝
echo.
echo  [1]  Setup / Install           (first run)
echo  [2]  Start daemon              (watch folder)
echo  [3]  Process single file       (one-shot)
echo  [4]  Screen recording          (manual, Ctrl+C stop)
echo  [5]  Watch process + record    (auto on program launch)
echo  [6]  Check hardware            (CPU/RAM/GPU)
echo  [7]  Re-run setup wizard
echo  [8]  Install autostart
echo  [9]  Uninstall autostart
echo  [10] Push to GitHub
echo  [0]  Exit
echo.

set /p choice="  Your choice: "

if "%choice%"=="1" goto setup
if "%choice%"=="2" goto daemon
if "%choice%"=="3" goto single
if "%choice%"=="4" goto record
if "%choice%"=="5" goto watchproc
if "%choice%"=="6" goto hardware
if "%choice%"=="7" goto wizard
if "%choice%"=="8" goto autostart_install
if "%choice%"=="9" goto autostart_uninstall
if "%choice%"=="10" goto github
if "%choice%"=="0" exit /b 0

echo  Invalid choice.
timeout /t 2 >nul
goto menu

:setup
echo.
echo  Running setup...
call install.bat
pause
goto menu

:daemon
echo.
if not exist "venv" (
    echo  [ERROR] venv not found. Run setup first (option 1).
    pause
    goto menu
)
call venv\Scripts\activate.bat
echo  Starting daemon... Press Ctrl+C to stop.
echo.
python -m video_transcriber.main
pause
goto menu

:single
echo.
if not exist "venv" (
    echo  [ERROR] venv not found. Run setup first (option 1).
    pause
    goto menu
)
set /p filepath="  Enter video file path: "
call venv\Scripts\activate.bat
python -m video_transcriber.main --file "%filepath%"
pause
goto menu

:record
echo.
if not exist "venv" (
    echo  [ERROR] venv not found. Run setup first (option 1).
    pause
    goto menu
)
call venv\Scripts\activate.bat
echo  Starting screen recording... Press Ctrl+C to stop.
echo.
python -m video_transcriber.main --record
pause
goto menu

:watchproc
echo.
if not exist "venv" (
    echo  [ERROR] venv not found. Run setup first (option 1).
    pause
    goto menu
)
set /p procname="  Enter process name (e.g. Zoom.exe): "
call venv\Scripts\activate.bat
echo  Watching for %procname%... Press Ctrl+C to stop.
echo.
python -m video_transcriber.main --watch-process "%procname%"
pause
goto menu

:hardware
echo.
if not exist "venv" (
    echo  [ERROR] venv not found. Run setup first (option 1).
    pause
    goto menu
)
call venv\Scripts\activate.bat
python -m video_transcriber.main --check-hardware
pause
goto menu

:wizard
echo.
if not exist "venv" (
    echo  [ERROR] venv not found. Run setup first (option 1).
    pause
    goto menu
)
call venv\Scripts\activate.bat
python -m video_transcriber.main --setup
pause
goto menu

:autostart_install
echo.
if not exist "venv" (
    echo  [ERROR] venv not found. Run setup first (option 1).
    pause
    goto menu
)
call venv\Scripts\activate.bat
python -m video_transcriber.main --install-autostart
pause
goto menu

:autostart_uninstall
echo.
if not exist "venv" (
    echo  [ERROR] venv not found. Run setup first (option 1).
    pause
    goto menu
)
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
