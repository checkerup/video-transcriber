@echo off
chcp 65001 >nul 2>&1
title Video Transcriber — Stop

echo Stopping Video Transcriber...
taskkill /FI "WINDOWTITLE eq Video Transcriber" /T /F >nul 2>&1
echo Done.
timeout /t 2 >nul
