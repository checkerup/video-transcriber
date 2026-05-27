@echo off
chcp 65001 >nul 2>&1
cd /d "%~dp0.."
echo ==============================================
echo   Video Transcriber — Setup Standard Environment
echo ==============================================
echo.
call install.bat
echo.
echo Setup completed.
pause
