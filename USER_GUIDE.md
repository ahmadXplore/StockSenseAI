# StockSense AI — Comprehensive Local Setup, API Key, Testing & Navigation Guide

This guide provides step-by-step instructions for running, testing, and navigating the **StockSense AI** platform locally.

---

## 1. API Keys & Environment Configuration

The application is pre-configured to use **free-tier** data providers so you do not need paid subscriptions.

### Pre-Configured `.env` File Location
Path: [`c:\Users\User\Desktop\Ahmad\Stock-Price_Predictor\.env`](file:///c:/Users/User/Desktop/Ahmad/Stock-Price_Predictor/.env)

### API Key Matrix (All Free Tier)

| Service Name | Purpose | Required for Phase | Where to Get Free Key (1-Min Registration) | Environment Variable Key | Default Fallback / Mock Mode |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **SEC EDGAR** | SEC 10-K/10-Q Financial Statements | Fundamentals | No key required (User-Agent header required by SEC) | `SEC_EDGAR_USER_AGENT` | Set to `"StockSenseAI contact@stocksense.ai"` |
| **Alpha Vantage** | Daily OHLCV Prices & Fundamentals | Market & Fundamentals | [alphavantage.co/support/#api-key](https://www.alphavantage.co/support/#api-key) | `ALPHA_VANTAGE_API_KEY` | Free key `"demo"` / Yahoo Finance fallback |
| **Financial Modeling Prep (FMP)** | Financial Ratios & Statements | Fundamentals & Estimates | [site.financialmodelingprep.com/developer/docs](https://site.financialmodelingprep.com/developer/docs) | `FMP_API_KEY` | Free key `"demo"` |
| **Finnhub** | Stock News, Sentiment & Earnings Calendar | News & Sentiment | [finnhub.io/register](https://finnhub.io/register) | `FINNHUB_API_KEY` | Free key `"demo"` |
| **FRED** | Interest Rates, Inflation & VIX Macro Data | Macro & Regimes | [fred.stlouisfed.org/docs/api/api_key.html](https://fred.stlouisfed.org/docs/api/api_key.html) | `FRED_API_KEY` | Stooq / CBOE free data fallback |

### Your Local `.env` Structure:
```env
# Application Settings
ENVIRONMENT=development
SECRET_KEY=dev_secret_key_stocksense_ai_change_in_production_32_bytes_min
LOG_LEVEL=INFO

# Database URLs
POSTGRES_USER=stocksense
POSTGRES_PASSWORD=stocksense_dev_password
POSTGRES_DB=stocksense
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
DATABASE_URL=postgresql+asyncpg://stocksense:stocksense_dev_password@localhost:5432/stocksense
SYNC_DATABASE_URL=postgresql+psycopg://stocksense:stocksense_dev_password@localhost:5432/stocksense

# Redis Cache URL
REDIS_URL=redis://localhost:6379/0

# Free-Tier Financial Data Provider Keys
ALPHA_VANTAGE_API_KEY=demo
FMP_API_KEY=demo
FINNHUB_API_KEY=demo
FRED_API_KEY=demo
SEC_EDGAR_USER_AGENT=StockSenseAI contact@stocksense.ai
```

---

## 2. How to Run the Project Locally

You can run StockSense AI locally using standard Python and Node.js dev servers.

### Prerequisites Installed:
- **Python**: `3.14` (installed at `C:\Python314\python.exe`)
- **Node.js**: `v24.14.0` (with `npm 11.9.0`)

---

### Step 1: Run Backend API Server

Open Terminal 1 (PowerShell or CMD) and execute:

```powershell
cd c:\Users\User\Desktop\Ahmad\Stock-Price_Predictor\backend

# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Start FastAPI server on port 8000
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
> **Backend Base URL**: `http://localhost:8000`  
> **Interactive Swagger API Docs**: [`http://localhost:8000/docs`](http://localhost:8000/docs)  
> **ReDoc API Documentation**: [`http://localhost:8000/redoc`](http://localhost:8000/redoc)

---

### Step 2: Run Frontend Web Application

Open Terminal 2 (PowerShell or CMD) and execute:

```powershell
cd c:\Users\User\Desktop\Ahmad\Stock-Price_Predictor\frontend

# Start Next.js Development Server
npm run dev
```
> **Frontend Application URL**: [`http://localhost:3000`](http://localhost:3000)

---

## 3. How to Test & Verify Everything

### 1. Automated Backend Unit & Integration Tests

Run the full pytest suite to verify health, database check constraints, alert deduplication, repository CRUD, and look-ahead bias prevention:

```powershell
cd c:\Users\User\Desktop\Ahmad\Stock-Price_Predictor\backend
.\.venv\Scripts\pytest tests/ -v
```

Expected Output:
```text
tests/test_db_constraints.py::test_alert_deduplication PASSED            [ 16%]
tests/test_health.py::test_root_health PASSED                            [ 33%]
tests/test_settings_defaults PASSED                      [ 50%]
tests/test_look_ahead_bias.py::test_look_ahead_bias_prevention PASSED    [ 66%]
tests/test_repositories.py::test_job_state_progression PASSED            [ 83%]
tests/test_repositories.py::test_atomic_report_persistence PASSED        [100%]

======================= 6 passed in 1.16s =======================
```

---

### 2. Testing API Endpoints via Browser / Swagger

Open [`http://localhost:8000/docs`](http://localhost:8000/docs) in your browser:

1. **`/api/v1/health`** (GET): Returns system health, database status, and environment variables.
2. **`/api/v1/analyze`** (POST): Trigger a stock analysis job (e.g. `{"ticker": "AAPL", "investment_amount": 10000}`). Returns `job_id` and 14-step job status.
3. **`/api/v1/market/quote/{ticker}`** (GET): Fetch live quote, daily OHLCV, and technical summary for ticker.
4. **`/api/v1/watchlist`** (GET): Fetch user's default watchlist items.
5. **`/api/v1/portfolio/positions`** (GET): Fetch open portfolio positions and P&L metrics.
6. **`/api/v1/settings`** (GET): Fetch user preferences and API key configuration status.

---

### 3. Navigating the Frontend Next.js Web App

Open [`http://localhost:3000`](http://localhost:3000) in your browser. All 13 core screens are fully routed and interactive:

| Route Path | Screen Title | Interactive Features & Elements |
| :--- | :--- | :--- |
| **`/dashboard`** | Main Dashboard | Quick stock search, market context bar (SPY, QQQ, VIX), recent analyses, portfolio summary card. |
| **`/analyze`** | Stock Analysis Entry | Symbol search bar (`AAPL`, `NVDA`, `MSFT`), horizon selector (`7d` to `3y`), risk tolerance toggle. |
| **`/analyze/[ticker]/loading/[jobId]`** | Analysis Progress | 14-step animated loading bar displaying current step (e.g. "Step 5/14: Running Sentiment NLP"). |
| **`/report/[ticker]/[reportId]`** | Master Analysis Report | Radar chart, 6-horizon forecasts, Bull/Base/Bear scenarios, Score dashboard, Investment Calculator, Exit strategy. |
| **`/watchlist`** | Watchlist Manager | Ticker list, daily change badges, alert triggers, quick re-analyze action buttons. |
| **`/portfolio`** | Portfolio Tracker | Open positions table, entry vs current price, P&L $, P&L %, stop-loss indicators. |
| **`/portfolio/[ticker]/thesis`** | Thesis Validation Audit | Thesis statement, supporting vs invalidating factors list, health badge (`VALID`/`REVIEW`). |
| **`/market`** | Market Intelligence | SPY 200SMA status, VIX volatility level, FRED 10Y yield, active market regime indicator. |
| **`/backtesting/[ticker]`** | Backtesting Engine | Historical return vs buy-and-hold, Sharpe ratio, win rate, non-dismissible survivorship bias disclosure badge. |
| **`/settings`** | Application Settings | API key inputs, dark mode toggle, default investment parameters, currency dropdown. |
| **`/settings/subscription`** | Subscription & Quotas | Free vs Pro tier feature matrix, monthly quota usage counter. |

---

## 5. How to View and Inspect Your Database

You can inspect all **32 tables across all 8 PostgreSQL schemas** (`market_data`, `fundamentals`, `analysis`, `portfolio`, `ml`, `news`, `macro`, `audit`) using any of the following methods:

### Database Connection Credentials:
- **Host**: `localhost` (or `127.0.0.1`)
- **Port**: `5432`
- **Database Name**: `stocksense`
- **Username**: `stocksense`
- **Password**: `stocksense_dev_password`

---

### Option A: Using a Free Visual Database GUI Tool (Recommended)

1. **Download & Install DBeaver or pgAdmin 4**:
   - [DBeaver Free Community Edition](https://dbeaver.io/) or [pgAdmin 4](https://www.pgadmin.org/) or [TablePlus](https://tableplus.com/).
   - Alternatively, install the **PostgreSQL Extension** inside VS Code / Cursor.

2. **Connect to StockSense AI Database**:
   - Create a new PostgreSQL Connection.
   - Enter Host: `localhost`, Port: `5432`, Database: `stocksense`, User: `stocksense`, Password: `stocksense_dev_password`.
   - Click **Test Connection** -> **Connect**.

3. **Navigate the 8 Schemas**:
   - Expand `stocksense` -> `Schemas`.
   - You will see all 8 dedicated schemas:
     - `market_data` -> `companies`, `price_data`, `technical_indicators`, `corporate_actions`, `index_constituents`
     - `fundamentals` -> `income_statements`, `balance_sheets`, `cash_flow_statements`, `financial_ratios`, `analyst_estimates`, `earnings_events`
     - `analysis` -> `analysis_jobs`, `analysis_reports`, `predictions`, `scenarios`, `investment_calculator_runs`, `fundamental_health_scores`, `valuation_analysis`, `risk_metrics`, `exit_strategies`, `anomaly_detection`, `backtest_runs`
     - `portfolio` -> `users`, `watchlists`, `watchlist_items`, `positions`, `thesis_validations`, `alerts`
     - `ml` -> `model_metadata`, `feature_importance`, `prediction_outcomes`, `model_drift_monitoring`
     - `news` -> `news_items`, `sentiment_aggregates`, `insider_transactions`
     - `macro` -> `indicators`, `market_regimes`
     - `audit` -> `analysis_requests`, `data_quality_log`, `report_exports`

---

### Option B: Using Command Line (`psql`)

If you have `psql` or Docker installed:

```powershell
# Connect directly via psql
psql -h localhost -U stocksense -d stocksense
# Password: stocksense_dev_password

# Useful psql Commands:
\dn                            # List all 8 PostgreSQL schemas
\dt market_data.*              # List all tables in market_data schema
\dt fundamentals.*             # List all tables in fundamentals schema
\dt analysis.*                 # List all tables in analysis schema
\d analysis.analysis_reports   # Inspect structure of analysis_reports table

# Useful SQL Queries:
SELECT ticker, name, sector, currency FROM market_data.companies;
SELECT id, ticker, status, progress_pct, requested_at FROM analysis.analysis_jobs;
SELECT id, ticker, overall_score, market_regime, generated_at FROM analysis.analysis_reports;
SELECT user_id, ticker, alert_type, deduplication_key, message FROM portfolio.alerts;
```

---

### Option C: Quick Python Verification Script

Run this command from your `backend/` directory to list all registered schemas and table row counts:

```powershell
cd c:\Users\User\Desktop\Ahmad\Stock-Price_Predictor\backend
.\.venv\Scripts\python -c "
import asyncio
from app.db.session import AsyncSessionLocal
from sqlalchemy import text

async def check():
    async with AsyncSessionLocal() as session:
        res = await session.execute(text(\"SELECT schema_name FROM information_schema.schemata WHERE schema_name IN ('market_data','fundamentals','analysis','portfolio','ml','news','macro','audit')\"))
        print('Active Schemas:', [r[0] for r in res.fetchall()])

asyncio.run(check())
"
```

