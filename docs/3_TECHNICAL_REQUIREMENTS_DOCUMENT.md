# Technical Requirements Document (TRD)
## AI Stock Prediction & Investment Analysis System
**Version:** 1.0 | **Status:** Draft | **Date:** 2026

---

## 1. System Architecture Overview

### 1.1 Architecture Pattern
**Microservices with Event-Driven Communication**

```
┌─────────────────────────────────────────────────────────┐
│                    Frontend (Next.js)                     │
│              React + TailwindCSS + Recharts               │
└────────────────────────┬────────────────────────────────┘
                         │ HTTPS / WebSocket
┌────────────────────────▼────────────────────────────────┐
│                   API Gateway (FastAPI)                   │
│               Auth | Rate Limiting | Routing              │
└──┬──────────────┬──────────────┬──────────────┬─────────┘
   │              │              │              │
┌──▼──┐      ┌───▼──┐      ┌───▼──┐      ┌───▼──┐
│Data │      │ ML   │      │Rules │      │Report│
│Svc  │      │Engine│      │Engine│      │ Gen  │
└──┬──┘      └───┬──┘      └───┬──┘      └───┬──┘
   │              │              │              │
┌──▼──────────────▼──────────────▼──────────────▼─────────┐
│                    Message Queue (Redis / Celery)          │
└──────────────────────────┬──────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────┐
│                   PostgreSQL + TimescaleDB                 │
│            (Structured data + Time-series data)           │
└─────────────────────────────────────────────────────────┘
```

### 1.2 Technology Stack

**Backend:**
- Language: Python 3.11+
- API Framework: FastAPI (async, OpenAPI auto-docs)
- Task Queue: Celery + Redis (async analysis jobs)
- Database: PostgreSQL 15 + TimescaleDB extension (time-series)
- Cache: Redis (API response caching, real-time price cache)
- ML Libraries: scikit-learn, XGBoost, LightGBM, CatBoost, statsmodels, Prophet, PyTorch (LSTM/GRU)
- Data Processing: pandas, numpy, polars (performance-critical paths)
- Technical Analysis: TA-Lib, pandas-ta
- NLP/Sentiment: transformers (FinBERT), VADER (fallback)
- Backtesting: Backtrader or custom implementation

**Frontend:**
- Framework: Next.js 14 (App Router)
- Language: TypeScript
- Styling: TailwindCSS + shadcn/ui components
- Charts: Recharts + TradingView Lightweight Charts (price charts)
- State: Zustand (global), React Query (server state)
- Forms: React Hook Form + Zod validation

**Infrastructure:**
- Containerization: Docker + Docker Compose
- Orchestration: Kubernetes (production) or Docker Compose (development)
- CI/CD: GitHub Actions
- Monitoring: Prometheus + Grafana
- Logging: structlog (Python) + Loki
- Deployment (MVP, zero infra budget): self-hosted Docker Compose on an Oracle Cloud "Always Free" VM (genuinely free forever, not a trial — enough RAM/CPU for API + Postgres/TimescaleDB + Redis + Celery), or an equivalent always-free tier such as Fly.io's free allowance. Frontend on Vercel's free tier. See Section 9 for full detail.

---

## 2. Backend Services Specification

### 2.1 Data Collection Service

**Responsibilities:** Fetch, validate, and store all external data

**APIs Integrated:**

| Source | Data Type | Endpoint / Library | Rate Limit | Cost |
|---|---|---|---|---|
| yfinance | Price/Volume (primary, ~15-min delayed) | Python library | ~2000/hr (unofficial, be conservative) | Free |
| Stooq | Price/Volume (cross-check, EOD historical) | CSV export | No documented hard limit; be a good citizen | Free |
| Alpha Vantage | Price/Volume (last-resort fallback) | REST API | 25/day, 5/min free | Free |
| EDGAR (SEC) — Company Facts | Fundamentals (as-reported, point-in-time) | EDGAR REST | 10 req/sec | Free |
| Financial Modeling Prep | Fundamentals — analyst estimates/ratios only (supplemental to EDGAR) | REST API | 250/day free | Free |
| EDGAR (SEC) — full-text search | Filings, insider transactions | EDGAR REST | 10 req/sec | Free |
| FRED (Federal Reserve) | Macro data | REST API | 120/min | Free |
| Finnhub | Company news + basic financials | REST API | 60/min free | Free |
| GDELT Project | Broad news coverage (headlines/summaries) | REST API | Generous, effectively unrestricted for this use case | Free |
| StockTwits | Social sentiment (flag as low-reliability) | Public REST API | Reasonable, unauthenticated | Free |
| CBOE | VIX data | Via yfinance (`^VIX`) | Standard | Free |
| OpenInsider | Insider transactions | Web scrape / RSS | Reasonable | Free |

**Note on Options Data:** no full-chain or implied-volatility data source with meaningful free access exists. Options-derived features (implied vol surface, put/call ratio) are deliberately **excluded from MVP** rather than sourced from a low-quality workaround — see PRD Section 7 (Post-MVP).

**Data Pipeline per Request:**
```
1. Check cache (Redis) — if fresh, return cached
2. Fetch from primary source
3. Run quality validation checks
4. Apply corporate action adjustments (prices)
5. Apply look-ahead lag enforcement (fundamentals)
6. Store to TimescaleDB (time-series) and PostgreSQL (fundamentals)
7. Update cache with TTL
8. Return to requesting service
```

**Data Quality Validator:**
```python
class DataQualityValidator:
    def validate_price_series(self, df):
        checks = {
            'completeness': self._check_completeness(df),
            'adjustment': self._verify_adjustment(df),
            'staleness': self._check_staleness(df),
            'outliers': self._check_outliers(df),
            'gaps': self._check_trading_day_gaps(df)
        }
        return QualityReport(checks)
    
    def validate_fundamentals(self, data):
        checks = {
            'available_date': self._check_data_availability_date(data),
            'lag_enforcement': self._enforce_minimum_lag(data),
            'point_in_time': self._verify_point_in_time(data),
            'restatement_flag': self._detect_restatements(data)
        }
        return QualityReport(checks)
```

### 2.2 ML Engine Service

**Responsibilities:** Train, validate, and serve all ML models

**Model Registry:**
```
models/
├── regression/
│   ├── xgboost_{ticker}_{horizon}.pkl
│   ├── lightgbm_{ticker}_{horizon}.pkl
│   ├── catboost_{ticker}_{horizon}.pkl
│   └── ensemble_{ticker}_{horizon}.pkl
├── classification/
│   ├── xgboost_classifier_{ticker}_{horizon}.pkl
│   └── ensemble_classifier_{ticker}_{horizon}.pkl
├── timeseries/
│   ├── arima_{ticker}.pkl
│   └── prophet_{ticker}.pkl
├── calibration/
│   └── calibrator_{ticker}_{horizon}.pkl
└── metadata/
    └── model_card_{ticker}_{horizon}.json
```

**Model Card (metadata per model):**
```json
{
  "ticker": "AAPL",
  "horizon": "30d",
  "model_type": "ensemble",
  "training_end_date": "2024-01-01",
  "validation_period": "2024-01-01 to 2024-12-31",
  "walk_forward_periods": 12,
  "directional_accuracy": 0.58,
  "calibration_error": 0.04,
  "feature_count": 87,
  "training_samples": 1890,
  "regime_coverage": {
    "bull": 0.45,
    "bear": 0.18,
    "high_volatility": 0.22,
    "low_volatility": 0.15
  },
  "last_retrain": "2025-01-15",
  "retrain_trigger": "monthly"
}
```

**Feature Engineering Pipeline:**
```python
class FeatureEngineeringPipeline:
    def __init__(self, enforce_look_ahead=True):
        self.enforce_look_ahead = enforce_look_ahead
    
    def build_feature_matrix(self, price_df, fundamental_df, 
                              macro_df, sentiment_df, as_of_date):
        features = {}
        
        # Price features (no lag needed — end-of-day data)
        features.update(self._price_features(price_df, as_of_date))
        
        # Technical features (no lag needed)
        features.update(self._technical_features(price_df, as_of_date))
        
        # Volume features (no lag needed)
        features.update(self._volume_features(price_df, as_of_date))
        
        # Fundamental features (REQUIRE lag enforcement)
        if self.enforce_look_ahead:
            lagged_fundamentals = self._apply_lag(
                fundamental_df, 
                min_lag_days=25
            )
        features.update(self._fundamental_features(lagged_fundamentals, as_of_date))
        
        # Macro features (1-day lag for daily releases)
        features.update(self._macro_features(macro_df, as_of_date))
        
        # Sentiment features (1-day lag)
        features.update(self._sentiment_features(sentiment_df, as_of_date))
        
        # Calendar features
        features.update(self._calendar_features(as_of_date))
        
        return pd.Series(features)
```

**Walk-Forward Validation:**
```python
class WalkForwardValidator:
    def __init__(self, min_train_years=3, step_size_months=1):
        self.min_train_years = min_train_years
        self.step_size = step_size_months
    
    def validate(self, model_class, feature_matrix, target):
        results = []
        
        for fold in self._generate_folds(feature_matrix):
            train_X, train_y = fold['train']
            val_X, val_y = fold['validation']
            
            model = model_class()
            model.fit(train_X, train_y)
            
            pred = model.predict(val_X)
            pred_proba = model.predict_proba(val_X)
            
            metrics = self._compute_metrics(val_y, pred, pred_proba)
            results.append(metrics)
        
        return WalkForwardResults(results)
```

### 2.3 Rules Engine Service

**Responsibilities:** Apply all deterministic rule-based checks

**Hard Veto Checker:**
```python
class HardVetoEngine:
    VETO_RULES = [
        VetoRule("sec_investigation", "Active SEC investigation disclosed"),
        VetoRule("going_concern", "Going concern doubt in audit opinion"),
        VetoRule("negative_fcf_streak", "Negative FCF for 3+ consecutive quarters"),
        VetoRule("covenant_violation", "Debt covenant violation disclosed"),
        VetoRule("revenue_decline_2q", "Revenue declining 2+ consecutive quarters"),
        VetoRule("high_beta", "Beta > 3.0"),
        VetoRule("liquidity_insufficient", "ADV < 5x intended position size"),
        VetoRule("recent_halt", "Trading halt in last 30 days"),
        VetoRule("junk_downgrade", "Credit rating downgraded to junk in last 90 days"),
        VetoRule("c_suite_turnover", "CEO/CFO change in last 60 days without succession clarity"),
        VetoRule("dividend_cut", "Dividend cut/suspension in last 90 days"),
    ]
    
    def check(self, company_data, user_context) -> VetoReport:
        triggered = []
        for rule in self.VETO_RULES:
            if rule.evaluate(company_data, user_context):
                triggered.append(rule)
        return VetoReport(triggered=triggered, blocks_buy=len(triggered) > 0)
```

**Anomaly Classifier:**
```python
class AnomalyClassifier:
    def classify_drop(self, stock_data, market_data, news_data) -> AnomalyType:
        type_a_score = self._score_type_a(stock_data, market_data)
        type_b_score = self._score_type_b(stock_data, news_data)
        type_c_indicators = self._check_type_c_disqualifiers(stock_data)
        
        # Type C check takes priority
        if any(type_c_indicators):
            return AnomalyType.TYPE_C, type_c_indicators
        
        if type_a_score >= 0.8:
            return AnomalyType.TYPE_A, {}
        elif type_b_score >= 0.7:
            return AnomalyType.TYPE_B, {}
        else:
            # Default to TYPE_C when ambiguous
            return AnomalyType.TYPE_C, {"reason": "Ambiguous classification — defaulting to Type C (caution)"}
```

### 2.4 Report Generation Service

**Responsibilities:** Assemble all module outputs into structured report

**Report Schema:**
```python
@dataclass
class InvestmentReport:
    generated_at: datetime
    data_as_of: datetime
    ticker: str
    company_name: str
    sector: str
    current_price: float
    
    # Scores
    fundamental_score: ScoreCard
    technical_score: ScoreCard
    valuation_score: ScoreCard
    risk_score: ScoreCard
    opportunity_score: ScoreCard
    macro_score: ScoreCard
    sentiment_score: ScoreCard
    overall_score: float
    
    # Predictions
    predictions: List[HorizonPrediction]
    scenarios: ScenarioAnalysis
    
    # Recommendations
    short_term_rec: Recommendation
    medium_term_rec: Recommendation
    long_term_rec: Recommendation
    
    # Veto
    veto_report: VetoReport
    
    # Anomaly
    anomaly_report: Optional[AnomalyReport]
    
    # Exit Strategy
    exit_plan: ExitPlan
    
    # Calculator
    investment_simulation: Optional[InvestmentSimulation]
    
    # Explainability
    reasons_for: List[str]
    reasons_against: List[str]
    key_risks: List[str]
    thesis_invalidators: List[str]
    
    # Data quality
    data_quality_report: DataQualityReport
    
    # Backtesting
    # NOTE (known MVP limitation): backtest_summary must include a `universe_note` field
    # set to "current-universe-approximate" whenever delisted-security price history was
    # not available for the test period. Survivorship-bias correction is deferred to
    # Post-MVP (no free data source serves delisted-ticker price history) — see PRD Section 5.
    backtest_summary: Optional[BacktestSummary]
    
    # Disclaimer
    disclaimer: str
```

---

## 3. API Specification

### 3.1 Endpoints

**Base URL:** `https://api.stocksense.ai/v1`

```
POST   /analyze              — Full analysis for a ticker
GET    /analyze/{ticker}     — Get cached/latest analysis
POST   /analyze/batch        — Analyze multiple tickers
GET    /price/{ticker}       — Current price and basic metrics
GET    /fundamentals/{ticker} — Latest fundamental data
GET    /news/{ticker}        — Recent news and sentiment
GET    /technicals/{ticker}  — Technical indicator values
GET    /backtest/{ticker}    — Backtesting results (MVP: current-universe-approximate; see known limitation in PRD Section 5 / Master Prompt Part 1.3)
POST   /calculator           — Investment calculator
GET    /market/regime        — Current market regime
GET    /sector/{sector}      — Sector analysis
POST   /watchlist            — Add to watchlist
GET    /watchlist            — Get watchlist
DELETE /watchlist/{ticker}   — Remove from watchlist
GET    /watchlist/status     — Current status for all watchlist items
POST   /portfolio/position   — Record a position entry
GET    /portfolio             — Get all positions
GET    /portfolio/thesis/{ticker} — Check thesis validity
GET    /earnings/calendar    — Upcoming earnings for watchlist
```

### 3.2 Analysis Request/Response

**Request:**
```json
POST /analyze
{
  "ticker": "AAPL",
  "investment_amount": 5000,
  "risk_tolerance": "moderate",
  "horizons": ["all"]
}
```

**Response:**
```json
{
  "report_id": "rpt_abc123",
  "generated_at": "2025-08-24T14:30:00Z",
  "data_freshness": {
    "price": "2025-08-24T14:25:00Z",
    "fundamentals": "2025-07-15T00:00:00Z",
    "news": "2025-08-24T12:00:00Z"
  },
  "ticker": "AAPL",
  "company_name": "Apple Inc.",
  "current_price": 225.50,
  "overall_score": 78,
  "regime_warning": null,
  "veto_triggered": false,
  "recommendations": {
    "short_term": { "signal": "BUY", "confidence": 71 },
    "medium_term": { "signal": "BUY", "confidence": 66 },
    "long_term": { "signal": "STRONG BUY", "confidence": 74 }
  },
  "predictions": [...],
  "scores": {...},
  "investment_simulation": {...},
  "exit_plan": {...},
  "explainability": {...},
  "disclaimer": "This report is an analytical tool only..."
}
```

### 3.3 Authentication
- JWT tokens with 24-hour expiration
- API key option for programmatic access
- Rate limiting: 100 full analyses per day per user (free tier), unlimited (paid)

---

## 4. Database Schema (Overview — see full schema doc)

### 4.1 Core Tables
- `companies` — Company master data
- `price_data` — TimescaleDB hypertable, OHLCV daily
- `fundamentals` — Quarterly fundamental metrics with `data_available_date`
- `news_items` — News articles with sentiment scores
- `analysis_reports` — Stored report results (JSONB)
- `watchlists` — User watchlists
- `portfolio_positions` — User position records
- `ml_model_metadata` — Model cards and performance metrics
- `backtest_results` — Per-ticker backtest summaries
- `market_regime_history` — Historical regime classifications

---

## 5. ML Model Requirements

### 5.1 Minimum Performance Thresholds

Models that do not meet these thresholds are NOT deployed:

| Metric | Minimum Threshold |
|---|---|
| Directional Accuracy (30-day) | >54% out-of-sample |
| ROC-AUC (classification) | >0.58 |
| Calibration Error (ECE) | <0.08 |
| Sharpe Ratio (backtest) | >0.5 |
| Backtest Win Rate | >50% |
| Maximum Drawdown (backtest) | <-35% |

### 5.2 Model Monitoring

- Retrain trigger: Monthly, or when directional accuracy drops below threshold on last 60 days
- Feature drift detection: KS-test on feature distributions weekly
- Regime mismatch alert: Flag when current feature values fall outside training distribution
- Performance degradation alert: 14-day rolling accuracy drops >5% below validation accuracy

### 5.3 Calibration Requirement

All classification models must be calibrated using Platt Scaling or Isotonic Regression.
Calibration must be validated on out-of-sample data (not training data).
Calibration plot (reliability diagram) must be stored with each model.

---

## 6. Data Retention & Caching

| Data Type | Cache TTL | Database Retention |
|---|---|---|
| Real-time price | 15 minutes | 10 years |
| Daily OHLCV | 24 hours | 10 years |
| Fundamentals | 24 hours | 10 years |
| News/Sentiment | 1 hour | 2 years |
| Full Analysis Report | 4 hours | 1 year |
| Macro data | 4 hours | 10 years |
| Market Regime | 1 hour | 5 years |
| ML Model | Until retrain | Version history kept |

---

## 7. Security Requirements

- All API keys stored in environment variables (never in code or version control)
- Database credentials managed via `.env` (local/VM) and GitHub Actions encrypted secrets (CI) — both free. If/when the project moves to paid infrastructure, migrate to a managed secrets service at that point; do not block MVP on it.
- HTTPS enforced on all endpoints
- Input validation and sanitization on all user inputs (ticker symbols: alphanumeric only, 1–5 chars)
- SQL injection prevention: use parameterized queries / ORM (SQLAlchemy)
- Rate limiting per user and per IP
- Audit log: all analysis requests logged with user ID, ticker, timestamp
- No storage of any financial account information

---

## 8. Testing Requirements

| Test Type | Coverage Target | Tools |
|---|---|---|
| Unit tests (business logic) | >80% | pytest |
| Integration tests (API) | >70% | pytest + httpx |
| ML model validation | Walk-forward, all models | Custom framework |
| Data pipeline tests | Every transformer | pytest |
| End-to-end tests | Critical user flows | Playwright |
| Load tests | 100 concurrent users | Locust |
| Backtesting validation | 5+ years, all tickers | Custom |

---

## 9. Deployment Architecture

### 9.1 Development
```
docker-compose up
# Starts: API, DB, Redis, Celery worker, Frontend
```

### 9.2 Production — Free-Tier Stack (MVP)
- API + Celery worker + Postgres/TimescaleDB + Redis: single Oracle Cloud "Always Free" VM (4 ARM cores / 24GB RAM tier, or the 2 AMD micro VMs, both genuinely free forever, not a trial) running the same Docker Compose stack as development
- Cache: self-hosted Redis in the same Compose stack, OR Upstash Redis free tier (10,000 commands/day, serverless, no VM management) if you'd rather not self-host it
- ML training jobs: run on the same free VM during off-peak hours (walk-forward validation and retraining are not latency-sensitive); if training becomes too slow on free-tier CPU, Google Colab's free tier (with usage limits) is a viable free GPU/CPU burst option for one-off retraining runs
- Frontend: Vercel free tier (genuinely free for this scale of traffic)
- CI/CD: GitHub Actions (free minutes for public/small private repos) → Docker → GitHub Container Registry (free) → deploy to the VM via SSH/`docker compose pull && up`

**Documented upgrade path (Post-MVP, when a budget exists):** migrate to AWS/GCP managed services (RDS, ElastiCache, ECS) or a PaaS like Railway/Render's paid tiers for better uptime SLAs, auto-scaling, and multi-AZ resilience. This is an explicit future decision, not an MVP requirement — the free-tier stack above is sufficient to validate the product with real usage first.

### 9.3 Monitoring
- API response times: Prometheus + Grafana alerts if p95 > 5s
- Error rate: Alert if >1% 5xx errors
- ML model drift: Weekly automated report
- Data freshness: Alert if any data source stale >2× normal refresh interval
- Uptime: UptimeRobot free tier (50 monitors, 5-min checks) or self-hosted Uptime Kuma (fully free, open-source) — alert if downtime >2 minutes
