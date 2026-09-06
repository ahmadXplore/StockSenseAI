# StockSense AI — Complete Database Architecture & Persistence Documentation

## 1. Executive Summary

The database architecture for **StockSense AI** is engineered as a hybrid relational and time-series persistence layer using **PostgreSQL 15** with the **TimescaleDB extension**. It implements strict financial correctness guarantees, auditability, point-in-time look-ahead bias prevention, versioning, alert deduplication, and atomic multi-table report storage.

---

## 2. PostgreSQL Schemas Overview (8 Schemas, 32 Tables)

| Schema | Purpose | Tables | Key Constraints / Features |
| :--- | :--- | :--- | :--- |
| **`market_data`** | Master company profiles, OHLCV prices, technical indicators, corporate actions, index constituents. | `companies`, `price_data`, `technical_indicators`, `corporate_actions`, `index_constituents` | TimescaleDB hypertable (`price_data`, `technical_indicators`), check constraints (`volume >= 0`, `high >= low`), survivorship bias tracking. |
| **`fundamentals`** | SEC EDGAR point-in-time financial statements, ratios, analyst targets, earnings calendar. | `income_statements`, `balance_sheets`, `cash_flow_statements`, `financial_ratios`, `analyst_estimates`, `earnings_events` | Explicit `period_end_date` vs `data_available_date` (25-day minimum lag enforcement). |
| **`analysis`** | Job queues, reports, forecasts, scenarios, calculator runs, score breakdowns, valuation, risk, exit plans, anomalies, backtests. | `analysis_jobs`, `analysis_reports`, `score_components`, `score_history`, `predictions`, `scenarios`, `investment_calculator_runs`, `fundamental_health_scores`, `valuation_analysis`, `risk_metrics`, `exit_strategies`, `anomaly_detection`, `backtest_runs` | Atomic multi-table persistence, 14-state job queue, check constraints (`probability BETWEEN 0 AND 1`, `score BETWEEN 0 AND 100`), `universe_type` disclosure. |
| **`ml`** | Model card registry, feature rankings, prediction outcomes, distribution drift checks. | `model_metadata`, `feature_importance`, `prediction_outcomes`, `model_drift_monitoring` | Model/feature/dataset versioning, KS-test distribution drift monitoring. |
| **`news`** | Material news items, historical sentiment observations, Form 4 insider transactions. | `news_items`, `sentiment_aggregates`, `insider_transactions` | Hard veto triggers (`triggers_veto`), dated sentiment history with `data_available_date`. |
| **`macro`** | FRED economic indicators, timestamped historical market regimes. | `indicators`, `market_regimes` | Point-in-time macro release dates, historical regime resolvers. |
| **`portfolio`** | Auth & User accounts, watchlists, portfolio positions, thesis audit checks, system alerts. | `users`, `watchlists`, `watchlist_items`, `positions`, `thesis_validations`, `alerts` | Bcrypt password hashing, thesis health status (`VALID`, `REVIEW`, `INVALIDATED`), alert deduplication keys (`deduplication_key`). |
| **`audit`** | API request logs, dataset quality checks, PDF report exports. | `analysis_requests`, `data_quality_log`, `report_exports` | Automated data quality checks (`PASS`, `WARNING`, `FAIL`), request IP/User-Agent tracking. |

---

## 3. Financial Correctness & Look-Ahead Bias Prevention

In financial machine learning, evaluating signals against future data invalidates backtest results and causes silent live trading failures.

### The Point-in-Time Rule:
Every financial statement, ratio, news item, and macro indicator carries three distinct dates:
1. **`period_end_date` / `observation_date`**: The fiscal or economic period ending date.
2. **`filing_date` / `release_date`**: The date the SEC filing or official report was released.
3. **`data_available_date`**: The earliest date this record is legally and technically accessible for feature extraction (enforcing a minimum 25-day lag for quarterly earnings).

### Enforcement in Repository Layer:
```python
# app/db/repositories/fundamental_repo.py
stmt = select(IncomeStatement).where(
    and_(
        IncomeStatement.ticker == ticker,
        IncomeStatement.data_available_date <= as_of_date
    )
).order_by(desc(IncomeStatement.period_end_date))
```
*Regression Test Verified*: `tests/test_look_ahead_bias.py` proves Q1 data filed on April 25 is **omitted** when querying as of April 15 and **included** when querying as of April 26.

---

## 4. Alert Deduplication Mechanism

To prevent notification spam for identical market events (e.g. repeated earnings announcements or stop-loss warnings):
- Table `portfolio.alerts` enforces a `UNIQUE` database constraint on `deduplication_key`.
- Key format: `{ticker}:{ALERT_TYPE}:{event_identifier}` (e.g., `AAPL:EARNINGS:2025-09-01`).
- `AlertRepository.create_deduplicated_alert(...)` gracefully returns `None` on key collision.

---

## 5. Normalized 14-Section Report Storage

Instead of relying solely on an unstructured blob, `AnalysisReport` persists master metadata and atomically inserts child rows across 10 normalized section tables in a single transaction:
1. `predictions` (7D, 30D, 3M, 6M, 1Y, 3Y with intervals & calibrated probabilities)
2. `scenarios` (Bull, Base, Bear, Tail Risk with probabilities)
3. `score_components` (8 module score cards)
4. `investment_calculator_runs` (simulator parameters & scenario projections)
5. `fundamental_health_scores` (10 sub-scores)
6. `valuation_analysis` (DCF assumptions & multiples)
7. `risk_metrics` (VaR, CVaR, drawdown, Sortino, position sizing)
8. `exit_strategies` (hard stop, trailing stop, profit targets, thesis statement)
9. `anomaly_detection` (Type A/B/C classification, z-score, recovery stats)
10. `backtest_runs` (universe disclosure, Sharpe, win rate)

Additionally, `report_snapshot_jsonb` is stored for ultra-fast single-query UI rendering.

---

## 6. Migration & Setup Instructions

### Apply Migrations to PostgreSQL/TimescaleDB
```bash
cd backend
.venv\Scripts\alembic upgrade head
```

### Run Full Test Suite
```bash
cd backend
.venv\Scripts\pytest tests/ -v
```
