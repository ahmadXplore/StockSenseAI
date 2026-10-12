

@echo off
echo ========================================================
echo StockSense AI - Starting Local Services (No Docker)
echo ========================================================
start "StockSense AI Backend (FastAPI)" cmd /k "cd /d "%~dp0backend" && .venv\Scripts\activate.bat && python -m uvicorn app.main:app --host 127.0.0.1 --port 8005 --reload"
start "StockSense AI Frontend (Next.js)" cmd /k "cd /d "%~dp0frontend" && npm run dev"
echo.
echo Services launched in dedicated windows!
echo - Frontend:     http://localhost:3005
echo - Backend API:  http://127.0.0.1:8005
echo - Swagger Docs: http://127.0.0.1:8005/docs
echo ========================================================
