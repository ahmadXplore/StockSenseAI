@echo off
setlocal
title StockSense AI - Windows Firewall Auto-Configurator

:: Check for Administrator privileges
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [INFO] Requesting Administrator privileges...
    powershell -Command "Start-Process cmd -ArgumentList '/c \"\"%~f0\"\"' -Verb RunAs"
    exit /b
)

:: Switch to script directory
cd /d "%~dp0"

echo ===============================================================================
echo            StockSense AI — Windows Firewall Auto-Configurator
echo ===============================================================================
echo.
echo Running setup_windows_firewall.ps1 with elevated privileges...
echo.

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0setup_windows_firewall.ps1"

echo.
pause
