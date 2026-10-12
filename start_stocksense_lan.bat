@echo off
setlocal enabledelayedexpansion

title StockSense AI — LAN Server Launcher
cls

echo ===============================================================================
echo                STOCKSENSE AI — NATIVE LAN SERVER (NO DOCKER)
echo ===============================================================================
echo.
echo [1/3] Detecting laptop active LAN IPv4 address...

set LAN_IP=
for /f "usebackq tokens=*" %%i in (`powershell -NoProfile -Command "$ip = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.IPAddress -notlike '169.254*' -and $_.IPAddress -notlike '127*' -and $_.InterfaceAlias -notlike '*Loopback*' -and $_.InterfaceAlias -notlike '*vEthernet*' } | Select-Object -First 1).IPAddress; if ($ip) { $ip } else { '127.0.0.1' }"`) do (
    set LAN_IP=%%i
)

if "%LAN_IP%"=="" (
    for /f "usebackq tokens=*" %%i in (`backend\.venv\Scripts\python.exe -c "import socket; s=socket.socket(socket.AF_INET, socket.SOCK_DGRAM); s.connect(('8.8.8.8', 80)); print(s.getsockname()[0]); s.close()" 2^>nul`) do (
        set LAN_IP=%%i
    )
)

if "%LAN_IP%"=="" set LAN_IP=127.0.0.1

echo       Host LAN IP Detected: %LAN_IP%
echo.

echo [2/3] Launching FastAPI Backend (0.0.0.0:8005)...
start "StockSense AI - LAN Backend (Port 8005)" cmd /k "cd /d "%~dp0backend" && .venv\Scripts\activate.bat && python -m uvicorn app.main:app --host 0.0.0.0 --port 8005 --reload"

echo [3/3] Launching Next.js Unified Frontend (0.0.0.0:3005)...
start "StockSense AI - LAN Frontend (Port 3005)" cmd /k "cd /d "%~dp0frontend" && npm run dev -- -H 0.0.0.0 -p 3005"

echo.
echo ===============================================================================
echo                     SERVER SUCCESSFULLY INITIALIZED!
echo ===============================================================================
echo.
echo   * Host Laptop URL (Local):    http://localhost:3005
echo   * Remote LAN URL (Mobile/PC): http://%LAN_IP%:3005
echo   * API & Swagger Docs:         http://%LAN_IP%:3005/docs
echo   * Admin LAN Console:          http://localhost:3005/admin
echo.
echo -------------------------------------------------------------------------------
echo   HOW TO CONNECT FROM SMARTPHONE / TABLET:
echo   1. Connect your smartphone to the SAME Wi-Fi network as this laptop.
echo   2. Open browser and go to: http://%LAN_IP%:3005
echo   3. On this laptop, open http://localhost:3005/admin (LAN Access tab).
echo   4. Click [Approve Device] to instantly grant mobile access!
echo -------------------------------------------------------------------------------
echo.
echo Keep this window open or minimize it. Press any key to exit launcher...
pause >nul
