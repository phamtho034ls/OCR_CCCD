@echo off
title Vite Frontend Launcher
set "PATH=C:\Program Files\nodejs;%PATH%"
cd /d "%~dp0"
echo ==============================================
echo  Dang khoi chay Vite Frontend Development Server...
echo ==============================================
npm run dev
pause
