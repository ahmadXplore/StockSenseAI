# Product Requirements Document (PRD)
## AI Stock Prediction & Investment Analysis System
**Version:** 1.0 | **Status:** Draft | **Date:** 2026

---

## 1. Product Overview

### 1.1 Product Name
**StockSense AI** — AI-Powered Investment Analysis Platform

### 1.2 Product Vision
A production-grade, AI-driven investment analysis platform that provides retail and semi-professional investors with institutional-quality analysis: multi-horizon price forecasting, fundamental health scoring, anomaly detection, risk analysis, and explainable buy/hold/sell recommendations — with full auditability of every signal and its data source.

### 1.3 Target Users

| User Type | Description | Primary Need |
|---|---|---|
| Active Retail Investor | Individual buying/selling stocks with own capital | Reliable signals with clear reasoning |
| Semi-professional Trader | Higher volume, more sophisticated analysis needs | Full technical + fundamental data, backtesting |
| Long-term Investor | Holds positions 1–3+ years | Fundamental quality, valuation, long-term outlook |
| Risk-conscious Investor | Prioritizes capital preservation | Risk metrics, downside scenarios, exit rules |

### 1.4 Product Goals
1. Reduce the information advantage gap between retail and institutional investors
2. Provide clear, explainable signals — never a black box
3. Enforce risk discipline through hard rules that can't be overridden
4. Support the full investment lifecycle: research → entry → monitoring → exit

### 1.5 Non-Goals
- This is NOT a trading execution platform (no order routing)
- This is NOT a financial advisor (no personalized financial planning)
- This is NOT a social/copy-trading platform
- This does NOT guarantee returns or provide guaranteed signals

---

## 2. User Stories

### 2.1 Core Analysis Flow

**US-001:** As an investor, I want to enter a stock ticker and receive a complete investment analysis report so I can make an informed entry decision.

**US-002:** As an investor, I want to see predictions for multiple time horizons (7 days to 3 years) so I can decide which holding period suits my strategy.

**US-003:** As an investor, I want to enter my investment amount and see projected returns in dollar terms across bull/base/bear scenarios so I can understand real-world impact.

**US-004:** As an investor, I want to understand WHY the system recommends BUY, HOLD, or AVOID with specific data points so I can validate the reasoning.

### 2.2 Risk Management

**US-005:** As an investor, I want to see a complete exit plan (stop-loss, profit target, fundamental triggers) generated alongside every BUY signal so I know exactly when to exit.

**US-006:** As an investor, I want to be warned if any hard veto rule is triggered (auditor concern, SEC investigation, liquidity issue) so I avoid high-risk situations.

**US-007:** As an investor, I want to see my risk score and risk/reward ratio before entering a position so I can assess if it fits my risk tolerance.

### 2.3 Anomaly Detection

**US-008:** As an investor, I want to be notified when a stock I'm watching has dropped significantly more than its historical norm so I can assess whether it's a buying opportunity.

**US-009:** As an investor, I want the system to classify whether a price drop is a temporary shock (Type A/B) or structural deterioration (Type C) so I don't mistake a dying company for a bargain.

### 2.4 Monitoring

**US-010:** As an investor with open positions, I want to receive thesis validation checks that tell me if my entry reasons are still valid so I can exit if the thesis breaks.

**US-011:** As an investor, I want to be alerted to upcoming earnings announcements for my watched stocks so I can manage risk appropriately.

**US-012:** As an investor, I want a watchlist where I can track multiple stocks and see their current status at a glance.

### 2.5 Education & Transparency

**US-013:** As a user, I want to see the system's historical accuracy metrics (backtested performance) so I know how much to trust its signals.

**US-014:** As a user, I want every data point to show its source and freshness so I can trust the data quality.

**US-015:** As a user, I want technical indicators explained in plain English, not just raw numbers.

---

## 3. Functional Requirements

### 3.1 Stock Analysis Module

| ID | Requirement | Priority |
|---|---|---|
| FR-001 | Accept ticker symbol or company name as input | P0 |
| FR-002 | Auto-fetch current price, 5-year historical price, volume | P0 |
| FR-003 | Auto-fetch fundamental data (revenue, EPS, FCF, debt, margins, ROE, ROIC) | P0 |
| FR-004 | Auto-fetch news (last 90 days) and classify sentiment | P0 |
| FR-005 | Generate predictions for 7D, 30D, 3M, 6M, 1Y, 3Y horizons | P0 |
| FR-006 | Display prediction intervals (not just point estimates) | P0 |
| FR-007 | Generate Fundamental Health Score (0–100) with sub-score breakdown | P0 |
| FR-008 | Generate Technical Health Score (0–100) with indicator details | P0 |
| FR-009 | Generate Valuation Score using minimum 4 methods | P0 |
| FR-010 | Generate Risk Score with full metrics (VaR, drawdown, beta, Sharpe) | P0 |
| FR-011 | Generate Opportunity Score for anomaly situations | P1 |
| FR-012 | Generate Macro Score based on economic environment | P1 |
| FR-013 | Run Hard Veto check and display any triggered veto rules | P0 |
| FR-014 | Generate horizon-specific recommendations (Short/Medium/Long) | P0 |
| FR-015 | Generate full explainability report (reasons for and against) | P0 |

### 3.2 Investment Calculator

| ID | Requirement | Priority |
|---|---|---|
| FR-020 | Accept investment amount input | P0 |
| FR-021 | Calculate shares, current value, projected value per scenario | P0 |
| FR-022 | Display bull/base/bear scenarios in dollar and percentage terms | P0 |
| FR-023 | Suggest position size based on risk tolerance | P1 |
| FR-024 | Display annualized return for all horizons | P1 |

### 3.3 Exit Strategy Module

| ID | Requirement | Priority |
|---|---|---|
| FR-030 | Generate stop-loss price based on ATR | P0 |
| FR-031 | Generate trailing stop rule | P0 |
| FR-032 | Generate profit target (partial and full) | P0 |
| FR-033 | List fundamental exit triggers specific to this stock | P0 |
| FR-034 | Generate time-based exit rule | P1 |

### 3.4 Watchlist & Portfolio Monitoring

| ID | Requirement | Priority |
|---|---|---|
| FR-040 | Allow adding stocks to a watchlist | P0 |
| FR-041 | Show current status for each watchlist stock | P0 |
| FR-042 | Run thesis validation for held positions | P1 |
| FR-043 | Display earnings calendar for watchlist stocks | P1 |
| FR-044 | Alert on anomaly detection triggers for watchlist stocks | P1 |
| FR-045 | Allow manual position entry (entry price, date, amount) | P1 |

### 3.5 Backtesting Module

| ID | Requirement | Priority |
|---|---|---|
| FR-050 | Display system's historical signal accuracy per ticker | P1 |
| FR-051 | Show backtested strategy performance vs benchmarks | P1 |
| FR-052 | Include transaction costs in backtest results | P1 |
| FR-053 | Show maximum drawdown and win rate of system signals | P1 |
| FR-054 | Label all backtest/historical-performance output as "current-universe-approximate" and disclose that delisted-security price history is not yet included (see Section 5 known limitation) | P0 |

### 3.6 Market Context

| ID | Requirement | Priority |
|---|---|---|
| FR-060 | Display current market regime classification | P0 |
| FR-061 | Show macro environment score | P0 |
| FR-062 | Show stock performance vs sector ETF and SPY | P0 |
| FR-063 | Display upcoming earnings dates | P0 |

---

## 4. Non-Functional Requirements

### 4.1 Performance
- Analysis report generation: < 30 seconds for full report
- Watchlist refresh: < 10 seconds for up to 20 stocks
- Price data latency: < 15 minutes during market hours
- API uptime target: 99.5%

### 4.2 Data Quality
- Data staleness check on every analysis run
- Source attribution on every data point
- Missing data policy: flag and report, never silently fill
- Corporate action verification on all price series

### 4.3 Accuracy & Reliability
- All ML models must be validated with walk-forward testing
- Backtest must cover minimum 5 years out-of-sample
- Confidence scores must be calibration-based (not arbitrary)
- System must display its own accuracy metrics (not just signal outputs)

### 4.4 Security
- No storage of user financial account credentials
- User watchlist and position data encrypted at rest
- API keys (data providers) stored in environment variables, never in code
- Rate limiting on all API endpoints

### 4.5 Scalability
- Architecture must support adding new data sources without core rebuild
- Each analysis module must be independently deployable
- Support for concurrent analysis of multiple stocks

### 4.6 Compliance & Legal
- Mandatory disclaimers on every report (non-removable)
- No use of language implying guaranteed returns
- No personalized financial advice
- Clear labeling as an analytical tool, not a financial advisor

---

## 5. Constraints

- **Known limitation — delisted-security price history (survivorship bias):** The schema tracks historical index membership including delisted, bankrupt, and acquired tickers (`market_data.index_constituents`), but no free data source (yfinance, Stooq, Alpha Vantage) reliably serves *price history* for a ticker after it delists. As a result, MVP backtests are **not** fully survivorship-bias-free in practice, even though the constituent-tracking schema is correct. This is explicitly out of MVP scope — see Section 7 (Post-MVP) — and every backtest result or historical-performance claim in the UI/report output must be labeled **"current-universe-approximate"** rather than implying full correction. This must never be silently glossed over.
- **Budget:** Zero data-vendor budget for MVP. All data sourced from free, no-API-key-cost providers: Yahoo Finance (yfinance) + Stooq + Alpha Vantage free tier for price/volume, SEC EDGAR (primary) + Financial Modeling Prep free tier (supplemental) for fundamentals, SEC EDGAR + Finnhub free tier + GDELT + StockTwits for news/sentiment, FRED for macro.
- **Data Access:** True real-time tick data and full options-chain/implied-volatility data have no viable free source and are explicitly **out of MVP scope** (see Section 7, Post-MVP). The system operates on ~15-minute-delayed price data and omits options-derived features until a paid data budget is available.
- **Latency:** Full fundamental data may lag 1–3 business days after earnings; free-tier rate limits (e.g., Alpha Vantage's 25 requests/day) may add further delay under heavy usage and must be handled via caching, not by silently serving stale data as fresh.
- **Coverage:** Initial launch covers US equities only (NYSE, NASDAQ)
- **Regulatory:** Must not cross into regulated financial advisory territory

---

## 6. Success Metrics

| Metric | Target |
|---|---|
| Analysis accuracy (directional, 30-day) | >55% out-of-sample |
| Report generation time | <30 seconds |
| Hard veto precision (avoiding bad stocks) | >70% of stocks flagged should underperform |
| User report completion rate | >80% (users reading full report) |
| Backtest Sharpe Ratio vs Buy-and-Hold | >1.0 improvement |
| False positive rate on anomaly detection | <30% |

---

## 7. MVP Scope

**MVP includes:**
- Single stock analysis (full pipeline)
- 6 horizon predictions
- Fundamental + Technical + Valuation scores
- Hard veto rules
- Investment calculator
- Exit strategy generation
- Basic watchlist (up to 10 stocks)
- Full report with explainability

**Post-MVP:**
- Portfolio monitoring with position tracking
- Advanced backtesting UI
- Screener (scan universe for signals)
- Alerts and notifications
- Mobile app
- Options data integration
- International markets
- Delisted/bankrupt/acquired-security price history integration, to close the survivorship-bias gap described in Section 5 and enable fully survivorship-bias-free backtesting (requires either a vetted community dataset or a small paid source such as Norgate Data — no free equivalent exists)

---

## 8. Dependencies

| Dependency | Type | Risk |
|---|---|---|
| SEC EDGAR (Company Facts + full-text search) | External data — fundamentals & filings | Low — free, official, unlimited, no key required |
| Yahoo Finance (`yfinance`) | External data — price/volume, primary | Medium — unofficial/unsupported library, can break on Yahoo-side changes; mitigate with Stooq cross-check |
| Stooq | External data — price/volume, cross-check | Low — free, no key, no rate limit, but EOD only (no intraday) |
| Alpha Vantage (free tier) | External data — price/volume, fallback | Medium — very low free-tier limit (25 req/day), usable only as last-resort fallback |
| Financial Modeling Prep (free tier) | External data — analyst estimates/ratios | Medium — 250 req/day free-tier limit, don't rely on it for core fundamentals (EDGAR covers those) |
| Finnhub (free tier) | External data — company news | Medium — 60 calls/min free-tier limit |
| GDELT Project | External data — broad news coverage | Low — free, unlimited, no key required |
| StockTwits (public API) | External data — social sentiment | Low — free, public endpoints; treat output as low-reliability signal |
| FRED API | External data — macro | Low — free, reliable, official |
| Self-hosted open-source LLM (e.g., Llama 3.1 8B via Ollama) or rule-based NLG | ML inference — plain-language explanations | Low — zero marginal cost, runs on the same free-tier compute; quality ceiling is lower than a hosted frontier model, which is an acceptable MVP trade-off. A hosted API (OpenAI/Claude) remains a documented **optional, budgeted upgrade path** for Post-MVP, not an MVP dependency. |
