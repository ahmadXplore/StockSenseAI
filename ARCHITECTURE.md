# StockSense AI — System Architecture & Design Document

## 1. High-Level System Architecture

StockSense AI is structured as an event-driven modular architecture composed of:
1. **Next.js 14 Web Frontend**: Interactive dark-first financial terminal UI (App Router, TailwindCSS, Recharts).
2. **FastAPI API Gateway**: Async RESTful API with validation, rate limiting, and request tracing.
3. **Celery Worker & Beat**: Asynchronous multi-step pipeline for market ingestion, technical computation, and ML inference.
4. **PostgreSQL 15 + TimescaleDB**: Hybrid relational and time-series database with 8 distinct schemas.
5. **Redis Cache & Message Broker**: Real-time price caching, session state, and Celery job queue.

```
┌─────────────────────────────────────────────────────────┐
│                    Frontend (Next.js 14)                │
│              React + TailwindCSS + Recharts             │
└────────────────────────┬────────────────────────────────┘
                         │ HTTPS / REST
┌────────────────────────▼────────────────────────────────┐
│                   API Gateway (FastAPI)                 │
│               Auth | Rate Limiting | Routing            │
└──┬──────────────┬──────────────┬──────────────┬─────────┘
   │              │              │              │
┌──▼──┐      ┌───▼──┐      ┌───▼──┐      ┌───▼──┐
│Data │      │ ML   │      │Rules │      │Report│
│Svc  │      │Engine│      │Engine│      │ Gen  │
└──┬──┘      └───┬──┘      └───┬──┘      └───┬──┘
   │              │              │              │
┌──▼──────────────▼──────────────▼──────────────▼─────────┐
│                    Message Queue (Redis 7)              │
└──────────────────────────┬──────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────┐
│                PostgreSQL 15 + TimescaleDB              │
│       market_data | fundamentals | analysis | portfolio │
│             ml | news | macro | audit                   │
└─────────────────────────────────────────────────────────┘
```

---

## 2. 100% Free Data Ingestion Strategy

| Data Domain | Primary Source | Cross-Check / Fallback | Cost | Look-Ahead Lag Rule |
| :--- | :--- | :--- | :--- | :--- |
| **Price & Volume** | `yfinance` (~15m delayed) | `Stooq` (EOD CSV), `Alpha Vantage` (25 req/day) | Free | End-of-Day (No future lag needed) |
| **Fundamentals** | `SEC EDGAR` (Company Facts API) | `Financial Modeling Prep` (250 req/day analyst targets) | Free | Minimum 25-day lag post quarter-end |
| **News & Sentiment** | `SEC EDGAR` (8-K, 10-Q) | `Finnhub` (60/min), `GDELT` (global news) | Free | 1-day lag for public sentiment |
| **Macroeconomic** | `FRED` (Federal Reserve) | CBOE VIX (`^VIX` via Yahoo) | Free | 1-day release lag |
| **Insider Activity** | `SEC Form 4` (EDGAR) | `OpenInsider` | Free | 10b5-1 plan filtering |

---

## 3. Machine Learning Ensemble Architecture

### Multi-Horizon Model Stack:
- **Short-Term (7D, 30D)**: XGBoost Regressor + LightGBM Regressor + Logistic Direction Classifier
- **Medium-Term (3M, 6M)**: Random Forest + XGBoost + LightGBM + ARIMA baseline
- **Long-Term (1Y, 3Y)**: Gradient Boosting + DCF Valuation Anchor

### Non-Negotiable Validation Rules:
- **Walk-Forward Validation**: Rolling 12-month out-of-sample test splits (no random time-series shuffling).
- **Probability Calibration**: Platt Scaling / Isotonic Regression curves to convert raw model outputs to calibrated probabilities.
- **Minimum Performance Gates**: Models must achieve >54% directional accuracy, ROC-AUC >0.58, and Sharpe >0.5 to be deployed.

---

## 4. Hard Veto Capital Preservation Engine

Runs independently prior to score aggregation:
- SEC investigations or DOJ inquiries disclosed in 8-K filings
- Going-concern doubt or qualified audit opinion
- Prolonged negative FCF for 3+ consecutive quarters
- Debt covenant violations or junk rating downgrades

**Action on Veto**: Overrides all buy signals to `STRONG AVOID` and renders the persistent red Veto Banner in the UI.
