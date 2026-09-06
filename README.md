# StockSense AI

> **Institutional-Quality AI Stock Prediction & Investment Risk Analysis Platform**

StockSense AI is a production-grade analytical platform for US equities providing multi-horizon price forecasting, point-in-time fundamental health scoring, statistical drop anomaly detection, Hard Veto capital preservation rules, and explainable recommendations.

---

## System Architecture

- **Backend**: FastAPI (Python 3.11+), SQLAlchemy 2.0 (Async + Sync), Pydantic v2
- **Database**: PostgreSQL 15 with TimescaleDB time-series extension
- **Cache & Queue**: Redis 7 + Celery Workers & Beat Scheduler
- **Machine Learning**: XGBoost, LightGBM, CatBoost, scikit-learn, statsmodels
- **Sentiment NLP**: VADER, HuggingFace Transformers
- **Frontend**: Next.js 14 (App Router), TypeScript, TailwindCSS, Recharts
- **Deployment**: Multi-container Docker & Docker Compose

---

## Quick Start (Docker Compose)

### 1. Environment Setup
```bash
cp .env.example .env
```
Edit `.env` to configure your free data provider API keys (Alpha Vantage, FMP, Finnhub, FRED, SEC User-Agent).

### 2. Launch Full Stack
```bash
docker compose up -d --build
```

### 3. Verify Health
```bash
curl http://localhost:8000/health
```

- **Frontend App**: `http://localhost:3000`
- **Backend API Docs**: `http://localhost:8000/api/v1/docs`

---

## Local Development (Without Docker)

### Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

---

## Non-Negotiable Core Principles

1. **Capital Preservation First**: If an active SEC investigation or auditor concern exists, the Hard Veto Engine overrides all signals to `STRONG AVOID`.
2. **Strict Look-Ahead Bias Prevention**: Fundamental data is locked to its point-in-time `data_available_date` (minimum 25-day reporting lag).
3. **Calibrated Confidence**: Confidence scores are strictly computed from out-of-sample walk-forward calibration curves, not heuristic numbers.
4. **Honest Data Limitation Disclosure**: Delisted-security price history gaps are explicitly labeled as `current-universe-approximate` on all backtest views.
