# Backend Schema Document
## AI Stock Prediction & Investment Analysis System
**Version:** 1.0 | **Status:** Draft | **Date:** 2026

---

## 1. Database Architecture

### 1.1 Database Choice
- **PostgreSQL 15** with **TimescaleDB extension** for time-series data
- **Redis** for caching, session storage, and task queue
- **SQLAlchemy** ORM (Python backend)

### 1.2 Schema Organization

```
Schemas:
  market_data    — Price, volume, corporate actions
  fundamentals   — Financial statements, ratios
  analysis       — Reports, scores, predictions
  portfolio      — User positions, watchlists
  ml             — Model metadata, features, predictions
  news           — News items, sentiment
  macro          — Macro economic data
  audit          — Logs, data quality reports
```

---

## 2. Core Tables

### 2.1 companies

```sql
CREATE TABLE market_data.companies (
    id                  SERIAL PRIMARY KEY,
    ticker              VARCHAR(10) NOT NULL UNIQUE,
    name                VARCHAR(255) NOT NULL,
    sector              VARCHAR(100),
    industry            VARCHAR(100),
    exchange            VARCHAR(20),          -- NYSE, NASDAQ, etc.
    market_cap          BIGINT,               -- in USD cents
    country             VARCHAR(50),
    currency            VARCHAR(10) DEFAULT 'USD',
    ipo_date            DATE,
    is_active           BOOLEAN DEFAULT TRUE,
    is_delisted         BOOLEAN DEFAULT FALSE,
    delisted_date       DATE,
    delisted_reason     TEXT,                 -- Important for survivorship bias
    sic_code            VARCHAR(10),
    cik                 VARCHAR(20),          -- SEC CIK number for EDGAR
    isin                VARCHAR(20),
    cusip               VARCHAR(20),
    shares_outstanding  BIGINT,
    float_shares        BIGINT,
    employee_count      INTEGER,
    description         TEXT,
    website             VARCHAR(255),
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_companies_ticker ON market_data.companies(ticker);
CREATE INDEX idx_companies_sector ON market_data.companies(sector);
CREATE INDEX idx_companies_active ON market_data.companies(is_active);
```

### 2.2 price_data (TimescaleDB Hypertable)

```sql
CREATE TABLE market_data.price_data (
    time                TIMESTAMPTZ NOT NULL,
    ticker              VARCHAR(10) NOT NULL,
    open                NUMERIC(12,4) NOT NULL,
    high                NUMERIC(12,4) NOT NULL,
    low                 NUMERIC(12,4) NOT NULL,
    close               NUMERIC(12,4) NOT NULL,
    adj_close           NUMERIC(12,4) NOT NULL,  -- Split + dividend adjusted
    volume              BIGINT NOT NULL,
    vwap                NUMERIC(12,4),
    -- Adjustment tracking
    split_factor        NUMERIC(10,6) DEFAULT 1.0,
    dividend_amount     NUMERIC(10,6) DEFAULT 0.0,
    -- Quality
    data_source         VARCHAR(50),             -- 'yfinance', 'stooq', 'alpha_vantage', etc.
    is_adjusted         BOOLEAN DEFAULT TRUE,
    quality_flag        VARCHAR(20) DEFAULT 'ok', -- 'ok', 'suspect', 'gap'
    PRIMARY KEY (time, ticker)
);

-- Convert to TimescaleDB hypertable
SELECT create_hypertable('market_data.price_data', 'time');

-- Continuous aggregate for daily summaries
CREATE MATERIALIZED VIEW market_data.price_daily
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 day', time) AS day,
    ticker,
    FIRST(open, time) AS open,
    MAX(high) AS high,
    MIN(low) AS low,
    LAST(close, time) AS close,
    LAST(adj_close, time) AS adj_close,
    SUM(volume) AS volume
FROM market_data.price_data
GROUP BY day, ticker;

CREATE INDEX idx_price_ticker_time ON market_data.price_data(ticker, time DESC);
```

### 2.3 corporate_actions

```sql
CREATE TABLE market_data.corporate_actions (
    id                  SERIAL PRIMARY KEY,
    ticker              VARCHAR(10) NOT NULL,
    action_date         DATE NOT NULL,
    action_type         VARCHAR(50) NOT NULL,   -- 'split', 'dividend', 'merger', 'spinoff'
    split_ratio         NUMERIC(10,4),          -- e.g., 4.0 for 4:1 split
    dividend_amount     NUMERIC(10,6),
    dividend_type       VARCHAR(20),            -- 'cash', 'stock'
    notes               TEXT,
    source              VARCHAR(100),
    verified            BOOLEAN DEFAULT FALSE,
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    FOREIGN KEY (ticker) REFERENCES market_data.companies(ticker)
);

CREATE INDEX idx_corporate_actions_ticker ON market_data.corporate_actions(ticker, action_date);
```

### 2.4 index_constituents (Survivorship Bias Prevention)

```sql
CREATE TABLE market_data.index_constituents (
    id                  SERIAL PRIMARY KEY,
    index_ticker        VARCHAR(20) NOT NULL,   -- 'SPY', 'QQQ', etc.
    ticker              VARCHAR(10) NOT NULL,
    added_date          DATE NOT NULL,
    removed_date        DATE,                   -- NULL if still member
    removal_reason      VARCHAR(100),           -- 'delisted', 'acquired', 'index_change'
    weight              NUMERIC(8,6),           -- Current weight if still member
    created_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_constituents_index_date
    ON market_data.index_constituents(index_ticker, added_date, removed_date);
```

**Known MVP limitation (build this table fully, but read this before wiring it into the backtest engine):**
This table and the `companies.is_delisted` / `delisted_date` / `delisted_reason` fields above should be populated in full for MVP — tracking historical index membership correctly is cheap and important. What is genuinely **out of MVP scope** is populating `market_data.price_data` (or equivalent OHLCV table) *after* a ticker's `delisted_date` — no free source (yfinance, Stooq, Alpha Vantage) reliably serves that price history. Do not build a workaround that fabricates or interpolates delisted-ticker prices. The backtest engine must instead detect this gap (a constituent row with no corresponding price rows past `removed_date`) and mark the affected backtest run as `universe_note = 'current-universe-approximate'` rather than silently excluding the ticker or claiming full survivorship-bias correction. See PRD Section 5 and Master Prompt Part 1.3.

---

## 3. Fundamental Tables

### 3.1 income_statements

```sql
CREATE TABLE fundamentals.income_statements (
    id                      SERIAL PRIMARY KEY,
    ticker                  VARCHAR(10) NOT NULL,
    -- Period identification
    fiscal_year             INTEGER NOT NULL,
    fiscal_quarter          INTEGER,            -- 1-4, NULL for annual
    period_end_date         DATE NOT NULL,
    report_type             VARCHAR(10) NOT NULL, -- 'annual', 'quarterly', 'ttm'
    -- CRITICAL: Point-in-time compliance
    filing_date             DATE,               -- Date SEC filing submitted
    announcement_date       DATE,               -- Date earnings announced
    data_available_date     DATE GENERATED ALWAYS AS (
                                COALESCE(announcement_date,
                                    period_end_date + INTERVAL '45 days')
                            ) STORED,           -- Conservative availability estimate
    -- Revenue
    revenue                 BIGINT,             -- in USD cents
    revenue_growth_yoy      NUMERIC(8,4),       -- percentage
    gross_profit            BIGINT,
    gross_margin            NUMERIC(8,4),
    -- Operating
    operating_income        BIGINT,
    operating_margin        NUMERIC(8,4),
    ebitda                  BIGINT,
    ebitda_margin           NUMERIC(8,4),
    -- Bottom line
    net_income              BIGINT,
    net_margin              NUMERIC(8,4),
    eps_reported            NUMERIC(10,4),      -- Actual reported EPS
    eps_diluted             NUMERIC(10,4),
    shares_diluted          BIGINT,
    -- Analysts
    eps_consensus_estimate  NUMERIC(10,4),      -- Analyst consensus at time of report
    eps_beat_miss           NUMERIC(10,4),      -- Actual - Estimate
    revenue_consensus_est   BIGINT,
    revenue_beat_miss       BIGINT,
    -- As-reported flag
    is_restated             BOOLEAN DEFAULT FALSE,
    original_eps_reported   NUMERIC(10,4),      -- If restated, keep original
    -- Source
    data_source             VARCHAR(100),
    created_at              TIMESTAMPTZ DEFAULT NOW(),
    FOREIGN KEY (ticker) REFERENCES market_data.companies(ticker),
    UNIQUE(ticker, fiscal_year, fiscal_quarter, report_type)
);

CREATE INDEX idx_income_ticker_date
    ON fundamentals.income_statements(ticker, period_end_date DESC);
CREATE INDEX idx_income_available_date
    ON fundamentals.income_statements(ticker, data_available_date);
```

### 3.2 balance_sheets

```sql
CREATE TABLE fundamentals.balance_sheets (
    id                      SERIAL PRIMARY KEY,
    ticker                  VARCHAR(10) NOT NULL,
    fiscal_year             INTEGER NOT NULL,
    fiscal_quarter          INTEGER,
    period_end_date         DATE NOT NULL,
    report_type             VARCHAR(10) NOT NULL,
    data_available_date     DATE NOT NULL,
    -- Assets
    cash_and_equivalents    BIGINT,
    short_term_investments  BIGINT,
    total_current_assets    BIGINT,
    total_assets            BIGINT,
    -- Liabilities
    short_term_debt         BIGINT,
    long_term_debt          BIGINT,
    total_current_liabilities BIGINT,
    total_liabilities       BIGINT,
    -- Equity
    total_equity            BIGINT,
    retained_earnings       BIGINT,
    -- Computed
    net_debt                BIGINT,             -- Total debt - Cash
    debt_to_equity          NUMERIC(10,4),
    current_ratio           NUMERIC(8,4),
    quick_ratio             NUMERIC(8,4),
    book_value_per_share    NUMERIC(10,4),
    data_source             VARCHAR(100),
    created_at              TIMESTAMPTZ DEFAULT NOW(),
    FOREIGN KEY (ticker) REFERENCES market_data.companies(ticker)
);
```

### 3.3 cash_flow_statements

```sql
CREATE TABLE fundamentals.cash_flow_statements (
    id                      SERIAL PRIMARY KEY,
    ticker                  VARCHAR(10) NOT NULL,
    fiscal_year             INTEGER NOT NULL,
    fiscal_quarter          INTEGER,
    period_end_date         DATE NOT NULL,
    report_type             VARCHAR(10) NOT NULL,
    data_available_date     DATE NOT NULL,
    -- Operating
    operating_cash_flow     BIGINT,
    -- Investing
    capital_expenditures    BIGINT,             -- Typically negative
    -- Free Cash Flow
    free_cash_flow          BIGINT,             -- OCF + CapEx
    fcf_margin              NUMERIC(8,4),       -- FCF / Revenue
    fcf_per_share            NUMERIC(10,4),
    -- Financing
    dividends_paid           BIGINT,
    share_repurchases       BIGINT,
    net_debt_issuance       BIGINT,
    -- Shareholder returns
    total_shareholder_return BIGINT,            -- Dividends + Buybacks
    data_source             VARCHAR(100),
    created_at              TIMESTAMPTZ DEFAULT NOW(),
    FOREIGN KEY (ticker) REFERENCES market_data.companies(ticker)
);
```

### 3.4 financial_ratios

```sql
CREATE TABLE fundamentals.financial_ratios (
    id                      SERIAL PRIMARY KEY,
    ticker                  VARCHAR(10) NOT NULL,
    as_of_date              DATE NOT NULL,      -- The date these ratios are valid
    data_available_date     DATE NOT NULL,      -- Earliest use in features
    -- Valuation
    pe_ratio                NUMERIC(10,4),
    forward_pe               NUMERIC(10,4),
    peg_ratio                NUMERIC(10,4),
    price_to_sales          NUMERIC(10,4),
    price_to_book           NUMERIC(10,4),
    price_to_fcf             NUMERIC(10,4),
    ev_to_ebitda             NUMERIC(10,4),
    ev_to_sales               NUMERIC(10,4),
    fcf_yield                NUMERIC(8,6),       -- FCF / Market Cap
    earnings_yield           NUMERIC(8,6),
    dividend_yield           NUMERIC(8,6),
    -- Profitability
    roe                      NUMERIC(8,4),
    roa                      NUMERIC(8,4),
    roic                     NUMERIC(8,4),
    wacc_estimate             NUMERIC(8,4),
    roic_minus_wacc           NUMERIC(8,4),       -- Economic value creation
    -- Leverage
    debt_to_ebitda            NUMERIC(8,4),
    interest_coverage         NUMERIC(8,4),
    debt_to_equity            NUMERIC(8,4),
    net_debt_to_equity        NUMERIC(8,4),
    -- Growth (YoY)
    revenue_growth_yoy        NUMERIC(8,4),
    eps_growth_yoy             NUMERIC(8,4),
    fcf_growth_yoy             NUMERIC(8,4),
    -- Efficiency
    asset_turnover             NUMERIC(8,4),
    inventory_turnover         NUMERIC(8,4),
    -- Sector comparison (populated after sector analysis run)
    sector_pe_median           NUMERIC(10,4),
    sector_ev_ebitda_median    NUMERIC(10,4),
    pe_vs_sector_pct            NUMERIC(8,4),       -- Premium/discount vs sector
    data_source                VARCHAR(100),
    created_at                 TIMESTAMPTZ DEFAULT NOW(),
    FOREIGN KEY (ticker) REFERENCES market_data.companies(ticker),
    UNIQUE(ticker, as_of_date)
);
```

### 3.5 analyst_estimates

```sql
CREATE TABLE fundamentals.analyst_estimates (
    id                      SERIAL PRIMARY KEY,
    ticker                  VARCHAR(10) NOT NULL,
    estimate_date            DATE NOT NULL,      -- When this estimate was captured
    fiscal_year               INTEGER,
    fiscal_quarter             INTEGER,
    -- EPS estimates
    eps_consensus              NUMERIC(10,4),
    eps_high                   NUMERIC(10,4),
    eps_low                    NUMERIC(10,4),
    eps_num_analysts           INTEGER,
    -- Revenue estimates
    revenue_consensus          BIGINT,
    revenue_high                BIGINT,
    revenue_low                 BIGINT,
    revenue_num_analysts        INTEGER,
    -- Price targets
    price_target_mean           NUMERIC(10,4),
    price_target_high           NUMERIC(10,4),
    price_target_low            NUMERIC(10,4),
    buy_ratings                  INTEGER,
    hold_ratings                 INTEGER,
    sell_ratings                 INTEGER,
    -- Revision tracking
    eps_revision_7d               NUMERIC(10,4),      -- Change in consensus last 7 days
    eps_revision_30d              NUMERIC(10,4),
    revenue_revision_30d          BIGINT,
    data_source                  VARCHAR(100),
    created_at                   TIMESTAMPTZ DEFAULT NOW(),
    FOREIGN KEY (ticker) REFERENCES market_data.companies(ticker)
);
```

---

## 4. Analysis & Report Tables

### 4.1 analysis_reports

```sql
CREATE TABLE analysis.analysis_reports (
    id                      UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    ticker                  VARCHAR(10) NOT NULL,
    user_id                 UUID,               -- NULL for anonymous
    -- Report metadata
    generated_at             TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    generation_duration_ms   INTEGER,
    -- Input parameters
    investment_amount        NUMERIC(15,2),
    risk_tolerance            VARCHAR(20),        -- 'conservative', 'moderate', 'aggressive'
    requested_horizons        VARCHAR(50)[],
    -- Data freshness at report time
    price_data_as_of          TIMESTAMPTZ,
    fundamentals_as_of        DATE,
    news_as_of                 TIMESTAMPTZ,
    -- Veto status
    veto_triggered              BOOLEAN DEFAULT FALSE,
    veto_rules_triggered        TEXT[],
    -- Regime at report time
    market_regime                VARCHAR(50),
    regime_warning                BOOLEAN DEFAULT FALSE,
    -- Overall scores
    overall_score                 NUMERIC(5,2),
    fundamental_score             NUMERIC(5,2),
    technical_score                NUMERIC(5,2),
    valuation_score                NUMERIC(5,2),
    risk_score                      NUMERIC(5,2),
    opportunity_score               NUMERIC(5,2),
    macro_score                     NUMERIC(5,2),
    sentiment_score                 NUMERIC(5,2),
    -- Recommendations
    short_term_rec                  VARCHAR(20),
    short_term_confidence           NUMERIC(5,2),
    medium_term_rec                 VARCHAR(20),
    medium_term_confidence          NUMERIC(5,2),
    long_term_rec                   VARCHAR(20),
    long_term_confidence            NUMERIC(5,2),
    -- Full report (JSONB for flexibility)
    report_data                     JSONB NOT NULL,     -- Complete report as JSON
    -- Exit plan
    exit_plan                       JSONB,
    -- Investment simulation results
    investment_simulation           JSONB,
    -- Disclaimer
    disclaimer_version               VARCHAR(20) DEFAULT 'v1.0',
    FOREIGN KEY (ticker) REFERENCES market_data.companies(ticker)
);

CREATE INDEX idx_reports_ticker_date
    ON analysis.analysis_reports(ticker, generated_at DESC);
CREATE INDEX idx_reports_user
    ON analysis.analysis_reports(user_id, generated_at DESC);
CREATE INDEX idx_reports_data
    ON analysis.analysis_reports USING GIN (report_data);
```

### 4.2 score_history

```sql
CREATE TABLE analysis.score_history (
    id                      SERIAL PRIMARY KEY,
    ticker                  VARCHAR(10) NOT NULL,
    score_date               DATE NOT NULL,
    -- Scores
    overall_score              NUMERIC(5,2),
    fundamental_score           NUMERIC(5,2),
    technical_score             NUMERIC(5,2),
    valuation_score             NUMERIC(5,2),
    risk_score                   NUMERIC(5,2),
    opportunity_score            NUMERIC(5,2),
    macro_score                  NUMERIC(5,2),
    sentiment_score              NUMERIC(5,2),
    -- Recommendations
    short_term_rec               VARCHAR(20),
    medium_term_rec              VARCHAR(20),
    long_term_rec                VARCHAR(20),
    report_id                    UUID REFERENCES analysis.analysis_reports(id),
    FOREIGN KEY (ticker) REFERENCES market_data.companies(ticker),
    UNIQUE(ticker, score_date)
);

-- TimescaleDB for efficient time-series queries on scores
SELECT create_hypertable('analysis.score_history', 'score_date',
    chunk_time_interval => INTERVAL '3 months');
```

### 4.3 predictions

```sql
CREATE TABLE analysis.predictions (
    id                      UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    report_id                UUID REFERENCES analysis.analysis_reports(id),
    ticker                    VARCHAR(10) NOT NULL,
    prediction_date            DATE NOT NULL,      -- Date prediction was made
    target_date                 DATE NOT NULL,      -- Date prediction is for
    horizon_label                VARCHAR(20),        -- '7d', '30d', '3m', '6m', '1y', '3y'
    horizon_days                  INTEGER,
    -- Price predictions
    current_price                  NUMERIC(12,4),
    predicted_price                 NUMERIC(12,4),
    predicted_price_low             NUMERIC(12,4),      -- 10th percentile
    predicted_price_high             NUMERIC(12,4),      -- 90th percentile
    -- Return predictions
    expected_return                  NUMERIC(8,4),       -- percentage
    expected_return_low               NUMERIC(8,4),
    expected_return_high               NUMERIC(8,4),
    -- Scenario predictions
    bull_return                        NUMERIC(8,4),
    base_return                        NUMERIC(8,4),
    bear_return                        NUMERIC(8,4),
    tail_risk_return                   NUMERIC(8,4),
    bull_probability                    NUMERIC(5,4),
    base_probability                     NUMERIC(5,4),
    bear_probability                     NUMERIC(5,4),
    tail_risk_probability                NUMERIC(5,4),
    -- Classification
    prob_positive_return                  NUMERIC(5,4),       -- P(return > 0)
    -- Quality metrics
    confidence_score                       NUMERIC(5,2),       -- 0-100
    model_agreement_score                   NUMERIC(5,2),       -- Agreement between ensemble members
    regime_match_score                       NUMERIC(5,2),       -- How well current regime matches training
    -- Outcome tracking (filled in after target_date)
    actual_price                              NUMERIC(12,4),      -- Filled after target_date passes
    actual_return                              NUMERIC(8,4),
    prediction_correct_direction                BOOLEAN,       -- For directional accuracy tracking
    -- Model info
    models_used                                 TEXT[],
    feature_count                               INTEGER,
    FOREIGN KEY (ticker) REFERENCES market_data.companies(ticker)
);

CREATE INDEX idx_predictions_ticker_date
    ON analysis.predictions(ticker, prediction_date DESC);
CREATE INDEX idx_predictions_outcome
    ON analysis.predictions(ticker, target_date, actual_return)
    WHERE actual_return IS NOT NULL;
```

### 4.4 fundamental_health_scores

```sql
CREATE TABLE analysis.fundamental_health_scores (
    id                      SERIAL PRIMARY KEY,
    report_id                UUID REFERENCES analysis.analysis_reports(id),
    ticker                    VARCHAR(10) NOT NULL,
    score_date                 DATE NOT NULL,
    -- Overall
    total_score                  NUMERIC(5,2),
    -- Sub-scores (0-100 each)
    revenue_growth_score          NUMERIC(5,2),
    revenue_growth_detail         JSONB,              -- Supporting data
    earnings_growth_score         NUMERIC(5,2),
    earnings_growth_detail        JSONB,
    profitability_score            NUMERIC(5,2),
    profitability_detail           JSONB,
    free_cash_flow_score            NUMERIC(5,2),
    fcf_detail                       JSONB,
    debt_health_score                 NUMERIC(5,2),
    debt_detail                        JSONB,
    roe_roic_score                      NUMERIC(5,2),
    roe_roic_detail                      JSONB,
    cash_position_score                   NUMERIC(5,2),
    cash_detail                            JSONB,
    margin_stability_score                  NUMERIC(5,2),
    margin_detail                            JSONB,
    competitive_score                         NUMERIC(5,2),
    competitive_detail                         JSONB,
    historical_stability_score                  NUMERIC(5,2),
    historical_detail                            JSONB,
    -- Metadata
    data_period                                  VARCHAR(50),        -- e.g., "Q2 2025 (TTM)"
    data_quality_score                            NUMERIC(5,2),
    FOREIGN KEY (ticker) REFERENCES market_data.companies(ticker)
);
```

### 4.5 valuation_analysis

```sql
CREATE TABLE analysis.valuation_analysis (
    id                      SERIAL PRIMARY KEY,
    report_id                UUID REFERENCES analysis.analysis_reports(id),
    ticker                    VARCHAR(10) NOT NULL,
    analysis_date               DATE NOT NULL,
    current_price                 NUMERIC(12,4),
    -- Multi-method fair value
    fair_value_low                  NUMERIC(12,4),
    fair_value_mid                   NUMERIC(12,4),
    fair_value_high                   NUMERIC(12,4),
    valuation_status                   VARCHAR(30),        -- 'significantly_undervalued', etc.
    premium_discount_pct                NUMERIC(8,4),       -- vs fair_value_mid
    -- Relative valuation
    pe_current                            NUMERIC(10,4),
    pe_5y_average                          NUMERIC(10,4),
    pe_sector_median                        NUMERIC(10,4),
    pe_status                                VARCHAR(20),
    forward_pe_current                        NUMERIC(10,4),
    forward_pe_status                          VARCHAR(20),
    peg_current                                 NUMERIC(10,4),
    peg_status                                   VARCHAR(20),
    ps_current                                    NUMERIC(10,4),
    ps_5y_average                                  NUMERIC(10,4),
    ps_status                                       VARCHAR(20),
    pb_current                                       NUMERIC(10,4),
    pb_status                                         VARCHAR(20),
    ev_ebitda_current                                  NUMERIC(10,4),
    ev_ebitda_5y_avg                                    NUMERIC(10,4),
    ev_ebitda_status                                     VARCHAR(20),
    fcf_yield                                             NUMERIC(8,6),
    -- DCF Analysis
    dcf_base_value                                          NUMERIC(12,4),
    dcf_bull_value                                           NUMERIC(12,4),
    dcf_bear_value                                            NUMERIC(12,4),
    dcf_assumptions                                            JSONB,              -- All DCF inputs stored here
    dcf_sensitivity_table                                       JSONB,
    -- Confidence in valuation
    valuation_confidence                                          NUMERIC(5,2),
    data_quality_flag                                              VARCHAR(20),
    FOREIGN KEY (ticker) REFERENCES market_data.companies(ticker)
);
```

---

## 5. Risk Analysis Tables

### 5.1 risk_metrics

```sql
CREATE TABLE analysis.risk_metrics (
    id                      SERIAL PRIMARY KEY,
    report_id                UUID REFERENCES analysis.analysis_reports(id),
    ticker                    VARCHAR(10) NOT NULL,
    calculation_date            DATE NOT NULL,
    -- Volatility
    hist_vol_20d                  NUMERIC(8,4),       -- 20-day annualized
    hist_vol_60d                   NUMERIC(8,4),
    hist_vol_252d                   NUMERIC(8,4),
    implied_vol_30d                  NUMERIC(8,4),       -- From options if available
    -- Beta
    beta_1y                            NUMERIC(8,4),
    beta_3y                             NUMERIC(8,4),
    beta_sector_adjusted                 NUMERIC(8,4),
    -- Drawdown
    max_drawdown_alltime                  NUMERIC(8,4),
    max_drawdown_1y                        NUMERIC(8,4),
    max_drawdown_3y                         NUMERIC(8,4),
    current_drawdown                         NUMERIC(8,4),
    drawdown_from_peak_pct                    NUMERIC(8,4),
    days_since_peak                            INTEGER,
    -- VaR / CVaR
    var_95_1d                                    NUMERIC(8,4),
    var_95_1m                                     NUMERIC(8,4),
    var_99_1m                                      NUMERIC(8,4),
    cvar_95_1m                                      NUMERIC(8,4),
    -- Risk-adjusted returns
    sharpe_1y                                        NUMERIC(8,4),
    sortino_1y                                        NUMERIC(8,4),
    calmar_ratio                                       NUMERIC(8,4),
    -- Risk score components
    risk_score_total                                     NUMERIC(5,2),
    risk_score_volatility                                 NUMERIC(5,2),
    risk_score_beta                                        NUMERIC(5,2),
    risk_score_drawdown                                     NUMERIC(5,2),
    risk_score_fundamental                                   NUMERIC(5,2),
    risk_score_liquidity                                      NUMERIC(5,2),
    -- Risk/reward
    risk_reward_ratio                                           NUMERIC(8,4),
    expected_return_base                                         NUMERIC(8,4),
    expected_upside                                               NUMERIC(8,4),
    expected_downside                                              NUMERIC(8,4),
    FOREIGN KEY (ticker) REFERENCES market_data.companies(ticker)
);
```

### 5.2 anomaly_detection

```sql
CREATE TABLE analysis.anomaly_detection (
    id                      SERIAL PRIMARY KEY,
    report_id                UUID REFERENCES analysis.analysis_reports(id),
    ticker                    VARCHAR(10) NOT NULL,
    detection_date              DATE NOT NULL,
    -- Anomaly metrics
    peak_price                     NUMERIC(12,4),
    peak_date                       DATE,
    current_price                    NUMERIC(12,4),
    current_drawdown_pct              NUMERIC(8,4),
    -- Historical comparison
    historical_avg_decline              NUMERIC(8,4),
    historical_max_decline               NUMERIC(8,4),
    historical_std_decline                NUMERIC(8,4),
    z_score                                NUMERIC(8,4),       -- Standard deviations from mean
    is_statistically_unusual                 BOOLEAN,           -- z_score > 2.0
    -- Similar historical events
    similar_events_count                       INTEGER,
    recovery_rate_pct                            NUMERIC(8,4),       -- % of similar events that recovered
    avg_recovery_time_days                        INTEGER,
    -- Classification
    anomaly_type                                    VARCHAR(10),        -- 'TYPE_A', 'TYPE_B', 'TYPE_C', 'UNCLEAR'
    classification_confidence                         NUMERIC(5,2),
    type_a_conditions_met                              JSONB,              -- Which Type A conditions are met
    type_b_conditions_met                               JSONB,
    type_c_disqualifiers                                 JSONB,              -- Which Type C disqualifiers triggered
    -- Context
    market_drawdown_same_period                            NUMERIC(8,4),
    sector_drawdown_same_period                             NUMERIC(8,4),
    volume_anomaly_score                                     NUMERIC(8,4),
    news_event_identified                                     BOOLEAN,
    news_event_description                                     TEXT,
    -- Opportunity assessment
    opportunity_score                                            NUMERIC(5,2),
    is_recovery_opportunity                                        BOOLEAN,
    opportunity_conditions_met                                      JSONB,           -- All 7 conditions status
    -- Explanation
    plain_language_summary                                          TEXT,
    FOREIGN KEY (ticker) REFERENCES market_data.companies(ticker)
);
```

---

## 6. Machine Learning Tables

### 6.1 ml_model_metadata

```sql
CREATE TABLE ml.model_metadata (
    id                      UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    ticker                  VARCHAR(10),        -- NULL for universal models
    horizon                  VARCHAR(20),        -- '7d', '30d', etc.
    model_type                 VARCHAR(50),        -- 'xgboost_regressor', 'ensemble', etc.
    task_type                    VARCHAR(20),        -- 'regression', 'classification'
    -- Training info
    training_start_date            DATE,
    training_end_date               DATE,
    validation_start_date             DATE,
    validation_end_date                DATE,
    training_samples                    INTEGER,
    validation_samples                   INTEGER,
    feature_count                         INTEGER,
    feature_names                          TEXT[],
    -- Performance metrics
    val_directional_accuracy                 NUMERIC(6,4),
    val_roc_auc                               NUMERIC(6,4),
    val_calibration_error                      NUMERIC(6,4),
    val_mae                                     NUMERIC(12,4),
    val_rmse                                     NUMERIC(12,4),
    val_sharpe_ratio                              NUMERIC(8,4),
    val_win_rate                                    NUMERIC(6,4),
    -- Walk-forward results
    wf_periods                                        INTEGER,
    wf_avg_accuracy                                    NUMERIC(6,4),
    wf_std_accuracy                                     NUMERIC(6,4),
    wf_results_detail                                    JSONB,
    -- Calibration
    is_calibrated                                          BOOLEAN DEFAULT FALSE,
    calibration_method                                      VARCHAR(30),
    calibration_score                                        NUMERIC(6,4),
    -- Regime coverage
    regime_coverage                                            JSONB,              -- % of training data in each regime
    -- Status
    is_deployed                                                  BOOLEAN DEFAULT FALSE,
    deployed_at                                                    TIMESTAMPTZ,
    retired_at                                                      TIMESTAMPTZ,
    retirement_reason                                                TEXT,
    -- File reference
    model_file_path                                                    VARCHAR(500),
    model_file_hash                                                     VARCHAR(64),        -- SHA-256 for integrity
    -- Thresholds check (PASS or model not deployed)
    passed_minimum_thresholds                                             BOOLEAN DEFAULT FALSE,
    threshold_check_detail                                                  JSONB,
    hyperparameters                                                          JSONB,
    created_at                                                                TIMESTAMPTZ DEFAULT NOW(),
    FOREIGN KEY (ticker) REFERENCES market_data.companies(ticker)
);

CREATE INDEX idx_model_ticker_horizon
    ON ml.model_metadata(ticker, horizon)
    WHERE is_deployed = TRUE;
```

### 6.2 feature_importance

```sql
CREATE TABLE ml.feature_importance (
    id                      SERIAL PRIMARY KEY,
    model_id                 UUID REFERENCES ml.model_metadata(id),
    feature_name               VARCHAR(100) NOT NULL,
    importance_score              NUMERIC(10,6),
    rank                            INTEGER,
    importance_type                  VARCHAR(30),        -- 'gain', 'shap', 'permutation'
    created_at                         TIMESTAMPTZ DEFAULT NOW()
);
```

### 6.3 prediction_outcomes (Accuracy Tracking)

```sql
CREATE TABLE ml.prediction_outcomes (
    id                      SERIAL PRIMARY KEY,
    prediction_id             UUID REFERENCES analysis.predictions(id),
    model_id                    UUID REFERENCES ml.model_metadata(id),
    ticker                        VARCHAR(10) NOT NULL,
    prediction_date                DATE NOT NULL,
    target_date                      DATE NOT NULL,
    -- Predicted
    predicted_return                    NUMERIC(8,4),
    predicted_direction                   VARCHAR(10),        -- 'positive', 'negative'
    predicted_probability                   NUMERIC(6,4),
    -- Actual (filled after target_date)
    actual_return                              NUMERIC(8,4),
    actual_direction                             VARCHAR(10),
    -- Accuracy
    direction_correct                              BOOLEAN,
    return_error                                     NUMERIC(8,4),       -- predicted - actual
    absolute_error                                     NUMERIC(8,4),
    -- Used in rolling accuracy calculation
    created_at                                           TIMESTAMPTZ DEFAULT NOW(),
    outcome_recorded_at                                    TIMESTAMPTZ
);

-- View for rolling accuracy metrics
CREATE VIEW ml.rolling_accuracy AS
SELECT
    model_id,
    ticker,
    COUNT(*) as total_predictions,
    AVG(CASE WHEN direction_correct THEN 1.0 ELSE 0.0 END) as directional_accuracy,
    AVG(absolute_error) as mae,
    STDDEV(return_error) as prediction_std,
    MAX(prediction_date) as last_prediction_date
FROM ml.prediction_outcomes
WHERE outcome_recorded_at IS NOT NULL
GROUP BY model_id, ticker;
```

### 6.4 model_drift_monitoring

```sql
CREATE TABLE ml.model_drift_monitoring (
    id                      SERIAL PRIMARY KEY,
    model_id                 UUID REFERENCES ml.model_metadata(id),
    check_date                 DATE NOT NULL,
    -- Feature drift
    feature_name                  VARCHAR(100),
    train_mean                       NUMERIC(12,6),
    train_std                          NUMERIC(12,6),
    current_mean                        NUMERIC(12,6),
    current_std                           NUMERIC(12,6),
    ks_statistic                            NUMERIC(8,6),       -- KS test statistic
    ks_p_value                                NUMERIC(8,6),
    is_drifting                                 BOOLEAN,            -- p_value < 0.05
    -- Rolling performance drift
    recent_accuracy_14d                            NUMERIC(6,4),
    baseline_accuracy                                NUMERIC(6,4),
    accuracy_degradation                               NUMERIC(6,4),
    requires_retrain                                     BOOLEAN DEFAULT FALSE,
    alert_sent                                             BOOLEAN DEFAULT FALSE,
    created_at                                               TIMESTAMPTZ DEFAULT NOW()
);
```

---

## 7. News & Sentiment Tables

### 7.1 news_items

```sql
CREATE TABLE news.news_items (
    id                      UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    ticker                  VARCHAR(10),        -- NULL if market-wide
    headline                  TEXT NOT NULL,
    summary                     TEXT,
    url                           VARCHAR(2000),
    published_at                   TIMESTAMPTZ NOT NULL,
    fetched_at                       TIMESTAMPTZ DEFAULT NOW(),
    -- Source metadata
    source_name                        VARCHAR(100),
    source_type                          VARCHAR(30),        -- 'sec_filing', 'press_release', 'news', 'social'
    source_reliability                     NUMERIC(4,2),       -- 0-1 weight
    -- Sentiment
    sentiment_score                          NUMERIC(5,4),       -- -1 to +1
    sentiment_label                             VARCHAR(10),        -- 'positive', 'neutral', 'negative'
    sentiment_confidence                          NUMERIC(5,4),
    sentiment_model                                 VARCHAR(50),        -- 'finbert', 'vader'
    -- Event classification
    event_type                                        VARCHAR(50),        -- 'earnings', 'product', 'regulatory', etc.
    event_temporality                                    VARCHAR(20),        -- 'one_time', 'medium_term', 'long_term'
    is_material                                             BOOLEAN DEFAULT FALSE,
    materiality_reason                                        TEXT,
    -- Veto check
    triggers_veto                                               BOOLEAN DEFAULT FALSE,
    veto_rule                                                     VARCHAR(100),
    -- SEC specific
    filing_type                                                    VARCHAR(20),        -- '10-K', '10-Q', '8-K', 'Form-4'
    accession_number                                                 VARCHAR(50),
    FOREIGN KEY (ticker) REFERENCES market_data.companies(ticker)
);

CREATE INDEX idx_news_ticker_date ON news.news_items(ticker, published_at DESC);
CREATE INDEX idx_news_veto ON news.news_items(ticker, triggers_veto) WHERE triggers_veto = TRUE;
```

### 7.2 sentiment_aggregates

```sql
CREATE TABLE news.sentiment_aggregates (
    id                      SERIAL PRIMARY KEY,
    ticker                  VARCHAR(10) NOT NULL,
    aggregate_date            DATE NOT NULL,
    -- Rolling windows
    sentiment_7d                 NUMERIC(5,4),
    sentiment_30d                  NUMERIC(5,4),
    sentiment_90d                    NUMERIC(5,4),
    -- Item counts
    news_count_7d                       INTEGER,
    news_count_30d                        INTEGER,
    -- Trend
    sentiment_trend                          VARCHAR(20),        -- 'improving', 'stable', 'deteriorating'
    trend_change_7d                             NUMERIC(5,4),
    -- High-weight sentiment (SEC filings, major press only)
    high_weight_sentiment_30d                     NUMERIC(5,4),
    -- Composite score (0-100)
    sentiment_score                                  NUMERIC(5,2),
    -- Top events
    top_events_json                                    JSONB,              -- Top 3 material events
    created_at                                            TIMESTAMPTZ DEFAULT NOW(),
    FOREIGN KEY (ticker) REFERENCES market_data.companies(ticker),
    UNIQUE(ticker, aggregate_date)
);
```

### 7.3 insider_transactions

```sql
CREATE TABLE news.insider_transactions (
    id                      SERIAL PRIMARY KEY,
    ticker                  VARCHAR(10) NOT NULL,
    transaction_date          DATE NOT NULL,
    filing_date                  DATE,
    insider_name                    VARCHAR(255),
    insider_title                     VARCHAR(255),
    transaction_type                     VARCHAR(20),        -- 'buy', 'sell', 'option_exercise'
    shares                                  BIGINT,
    price_per_share                            NUMERIC(12,4),
    total_value                                   BIGINT,
    shares_owned_after                               BIGINT,
    -- Context
    is_planned_10b51                                    BOOLEAN,            -- Pre-planned sale (less informative)
    is_discretionary                                       BOOLEAN,
    signal_strength                                          VARCHAR(10),        -- 'strong_buy', 'neutral', 'strong_sell'
    -- SEC reference
    form_type                                                  VARCHAR(10) DEFAULT 'Form 4',
    accession_number                                             VARCHAR(50),
    created_at                                                     TIMESTAMPTZ DEFAULT NOW(),
    FOREIGN KEY (ticker) REFERENCES market_data.companies(ticker)
);
```

---

## 8. Macro Data Tables

### 8.1 macro_indicators

```sql
CREATE TABLE macro.indicators (
    id                      SERIAL PRIMARY KEY,
    indicator_name          VARCHAR(100) NOT NULL,  -- 'vix', 'fed_funds_rate', etc.
    indicator_date            DATE NOT NULL,
    value                        NUMERIC(12,6) NOT NULL,
    -- Derived
    change_1d                      NUMERIC(12,6),
    change_7d                        NUMERIC(12,6),
    change_30d                         NUMERIC(12,6),
    change_90d                           NUMERIC(12,6),
    -- Source
    source                                  VARCHAR(50),        -- 'fred', 'cboe', 'census'
    series_id                                  VARCHAR(50),        -- FRED series ID e.g. 'DGS10'
    created_at                                    TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(indicator_name, indicator_date)
);

-- Key indicators tracked:
-- vix, spy_price, qqq_price
-- fed_funds_rate, treasury_2y, treasury_10y, yield_curve_2_10
-- cpi_yoy, core_cpi_yoy
-- ism_manufacturing_pmi, ism_services_pmi
-- unemployment_rate
-- hy_credit_spread, ig_credit_spread
-- dxy (dollar index)
-- oil_wti
```

### 8.2 market_regimes

```sql
CREATE TABLE macro.market_regimes (
    id                      SERIAL PRIMARY KEY,
    regime_date              DATE NOT NULL UNIQUE,
    regime                     VARCHAR(30) NOT NULL,   -- 'bull', 'bear', 'high_vol', 'low_vol', 'rate_shock', 'recession', 'mixed'
    -- Supporting metrics
    spy_above_200sma              BOOLEAN,
    vix_level                        NUMERIC(8,4),
    yield_curve_inverted                BOOLEAN,
    hy_spread_level                       NUMERIC(8,4),
    spy_30d_return                           NUMERIC(8,4),
    -- Confidence
    regime_confidence                           NUMERIC(5,2),       -- How clearly defined the regime is
    -- Impact on models
    model_confidence_modifier                      NUMERIC(5,2),     -- Applied to all confidence scores
    interval_width_modifier                          NUMERIC(5,2),      -- Applied to prediction intervals
    created_at                                          TIMESTAMPTZ DEFAULT NOW()
);
```

---

## 9. Portfolio & User Tables

### 9.1 users

```sql
CREATE TABLE portfolio.users (
    id                      UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    email                   VARCHAR(255) UNIQUE NOT NULL,
    email_verified            BOOLEAN DEFAULT FALSE,
    -- Preferences
    default_risk_tolerance      VARCHAR(20) DEFAULT 'moderate',
    default_investment_amount     NUMERIC(15,2) DEFAULT 10000,
    preferred_horizons              VARCHAR(20)[] DEFAULT ARRAY['all'],
    -- Display
    dark_mode                          BOOLEAN DEFAULT TRUE,
    currency                              VARCHAR(10) DEFAULT 'USD',
    -- Subscription
    plan_type                                VARCHAR(20) DEFAULT 'free',    -- 'free', 'pro', 'premium'
    plan_started_at                             TIMESTAMPTZ,
    plan_expires_at                                TIMESTAMPTZ,
    -- Usage
    analyses_today                                    INTEGER DEFAULT 0,
    analyses_this_month                                  INTEGER DEFAULT 0,
    last_analysis_at                                        TIMESTAMPTZ,
    -- Account
    created_at                                                TIMESTAMPTZ DEFAULT NOW(),
    updated_at                                                  TIMESTAMPTZ DEFAULT NOW(),
    last_login_at                                                 TIMESTAMPTZ,
    is_active                                                       BOOLEAN DEFAULT TRUE
);
```

### 9.2 watchlists

```sql
CREATE TABLE portfolio.watchlists (
    id                      SERIAL PRIMARY KEY,
    user_id                  UUID REFERENCES portfolio.users(id),
    ticker                     VARCHAR(10) NOT NULL,
    added_at                     TIMESTAMPTZ DEFAULT NOW(),
    -- Alert preferences per stock
    alert_earnings                  BOOLEAN DEFAULT TRUE,
    alert_anomaly                      BOOLEAN DEFAULT TRUE,
    alert_score_change                    BOOLEAN DEFAULT TRUE,
    alert_stop_loss                          BOOLEAN DEFAULT TRUE,
    -- Notes
    user_notes                                  TEXT,
    UNIQUE(user_id, ticker),
    FOREIGN KEY (ticker) REFERENCES market_data.companies(ticker)
);
```

### 9.3 portfolio_positions

```sql
CREATE TABLE portfolio.positions (
    id                      UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id                  UUID REFERENCES portfolio.users(id),
    ticker                     VARCHAR(10) NOT NULL,
    -- Entry
    entry_date                    DATE NOT NULL,
    entry_price                      NUMERIC(12,4) NOT NULL,
    shares                              NUMERIC(12,4) NOT NULL,
    investment_amount                     NUMERIC(15,2),
    -- Entry context (from report at time of entry)
    entry_report_id                          UUID REFERENCES analysis.analysis_reports(id),
    entry_overall_score                         NUMERIC(5,2),
    entry_recommendation                           VARCHAR(20),
    entry_thesis                                      TEXT,               -- Why you bought it
    entry_stop_loss_price                                NUMERIC(12,4),
    entry_profit_target_1                                   NUMERIC(12,4),
    entry_profit_target_2                                      NUMERIC(12,4),
    entry_time_horizon                                            VARCHAR(20),        -- '30d', '6m', '1y', '3y'
    -- Exit
    exit_date                                                       DATE,
    exit_price                                                        NUMERIC(12,4),
    exit_reason                                                         VARCHAR(100),       -- 'stop_loss', 'profit_target', 'thesis_invalid', 'manual'
    -- Status
    status                                                                VARCHAR(20) DEFAULT 'open',  -- 'open', 'closed', 'partial'
    -- P&L (calculated)
    realized_pnl                                                            NUMERIC(15,2),
    realized_return_pct                                                       NUMERIC(8,4),
    -- Thesis validation
    last_thesis_check_date                                                      DATE,
    thesis_valid                                                                  BOOLEAN,
    thesis_check_notes                                                              TEXT,
    -- Metadata
    broker                                                                          VARCHAR(50),
    notes                                                                             TEXT,
    created_at                                                                        TIMESTAMPTZ DEFAULT NOW(),
    updated_at                                                                          TIMESTAMPTZ DEFAULT NOW(),
    FOREIGN KEY (ticker) REFERENCES market_data.companies(ticker)
);

CREATE INDEX idx_positions_user_status
    ON portfolio.positions(user_id, status) WHERE status = 'open';
```

---

## 10. Backtesting Tables

### 10.1 backtest_runs

```sql
CREATE TABLE analysis.backtest_runs (
    id                      UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    ticker                  VARCHAR(10),        -- NULL for portfolio-level backtest
    model_id                  UUID REFERENCES ml.model_metadata(id),
    -- Period
    backtest_start_date          DATE NOT NULL,
    backtest_end_date               DATE NOT NULL,
    -- Configuration
    initial_capital                    NUMERIC(15,2) DEFAULT 100000,
    position_size_pct                     NUMERIC(5,4) DEFAULT 0.02,   -- 2% per trade
    max_position_pct                         NUMERIC(5,4) DEFAULT 0.10,
    commission_per_share                        NUMERIC(8,6) DEFAULT 0.005,
    spread_assumption_pct                          NUMERIC(5,4),
    -- Results
    total_return                                      NUMERIC(8,4),
    cagr                                                 NUMERIC(8,4),
    sharpe_ratio                                            NUMERIC(8,4),
    sortino_ratio                                              NUMERIC(8,4),
    max_drawdown                                                  NUMERIC(8,4),
    max_drawdown_duration_days                                       INTEGER,
    total_trades                                                        INTEGER,
    win_rate                                                               NUMERIC(6,4),
    avg_win                                                                  NUMERIC(8,4),
    avg_loss                                                                   NUMERIC(8,4),
    profit_factor                                                                NUMERIC(8,4),
    -- Benchmark comparison
    buy_hold_return                                                                NUMERIC(8,4),
    spy_return                                                                       NUMERIC(8,4),
    sma_strategy_return                                                                NUMERIC(8,4),
    alpha_vs_buy_hold                                                                    NUMERIC(8,4),
    alpha_vs_spy                                                                           NUMERIC(8,4),
    -- Monthly returns (JSONB)
    monthly_returns                                                                          JSONB,
    trade_log                                                                                  JSONB,              -- Individual trade records
    -- Passed thresholds
    passed_minimum_requirements                                                                  BOOLEAN,
    -- Known MVP limitation: universe honesty flag (see Section 2.4 note above)
    universe_note               VARCHAR(50) DEFAULT 'current-universe-approximate',  -- set to 'survivorship-bias-corrected' only once delisted-price data is integrated (Post-MVP)
    excluded_delisted_tickers   TEXT[],      -- tickers that were index members during the period but could not be simulated (no price data post-delisting)
    created_at                                                                                     TIMESTAMPTZ DEFAULT NOW(),
    FOREIGN KEY (ticker) REFERENCES market_data.companies(ticker)
);
```

---

## 11. Audit & Logging Tables

### 11.1 analysis_request_log

```sql
CREATE TABLE audit.analysis_requests (
    id                      UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id                  UUID,
    ticker                     VARCHAR(10),
    requested_at                 TIMESTAMPTZ DEFAULT NOW(),
    completed_at                    TIMESTAMPTZ,
    duration_ms                        INTEGER,
    status                                VARCHAR(20),        -- 'completed', 'failed', 'cached'
    error_message                           TEXT,
    ip_address                                 INET,
    user_agent                                    TEXT,
    report_id                                        UUID
);
```

### 11.2 data_quality_log

```sql
CREATE TABLE audit.data_quality_log (
    id                      SERIAL PRIMARY KEY,
    logged_at                TIMESTAMPTZ DEFAULT NOW(),
    data_source                 VARCHAR(50),
    ticker                         VARCHAR(10),
    data_type                        VARCHAR(50),
    quality_check                       VARCHAR(100),
    status                                  VARCHAR(20),        -- 'pass', 'fail', 'warning'
    detail                                     TEXT,
    auto_remediated                               BOOLEAN DEFAULT FALSE,
    remediation_action                               TEXT
);
```

---

## 12. Redis Cache Keys

```
# Price data (TTL: 15 minutes during market hours)
price:{ticker}:current              → Current price data JSON

# Daily OHLCV (TTL: 24 hours)
price:{ticker}:daily:{date}         → Daily OHLCV JSON

# Fundamental data (TTL: 24 hours)
fundamentals:{ticker}:latest        → Latest fundamental data JSON

# Analysis reports (TTL: 4 hours)
report:{ticker}:latest              → Latest full report JSON
report:{report_id}                  → Specific report JSON

# Technical indicators (TTL: 1 hour)
technicals:{ticker}:daily           → All TA indicators JSON

# Market regime (TTL: 1 hour)
market:regime:current               → Current regime JSON

# News sentiment (TTL: 1 hour)
sentiment:{ticker}:7d               → 7-day sentiment JSON

# Analysis job status (TTL: 24 hours)
job:{job_id}:status                 → Job progress JSON

# User watchlist (TTL: 5 minutes)
watchlist:{user_id}                 → Watchlist items JSON

# Model predictions (TTL: 4 hours)
prediction:{ticker}:{horizon}       → Latest prediction JSON
```

---

## 13. Database Indexes Summary

Critical indexes (beyond those defined above):

```sql
-- For watchlist status refresh
CREATE INDEX idx_price_data_ticker_recent
    ON market_data.price_data(ticker, time DESC)
    WHERE time > NOW() - INTERVAL '5 days';

-- For scoring history trends
CREATE INDEX idx_score_history_recent
    ON analysis.score_history(ticker, score_date DESC);

-- For news veto detection
CREATE INDEX idx_news_veto_ticker
    ON news.news_items(ticker, published_at DESC)
    WHERE triggers_veto = TRUE;

-- For backtest survivorship bias queries
CREATE INDEX idx_constituents_historical
    ON market_data.index_constituents(index_ticker, added_date, removed_date)
    WHERE removed_date IS NOT NULL;

-- For prediction accuracy tracking
CREATE INDEX idx_pred_outcomes_pending
    ON ml.prediction_outcomes(target_date)
    WHERE outcome_recorded_at IS NULL;
```

---

## 14. Entity Relationship Summary

```
market_data.companies (1) ──< market_data.price_data (many)
market_data.companies (1) ──< market_data.corporate_actions (many)
market_data.companies (1) ──< market_data.index_constituents (many)

market_data.companies (1) ──< fundamentals.income_statements (many)
market_data.companies (1) ──< fundamentals.balance_sheets (many)
market_data.companies (1) ──< fundamentals.cash_flow_statements (many)
market_data.companies (1) ──< fundamentals.financial_ratios (many)
market_data.companies (1) ──< fundamentals.analyst_estimates (many)

market_data.companies (1) ──< analysis.analysis_reports (many)
analysis.analysis_reports (1) ──< analysis.predictions (many)
analysis.analysis_reports (1) ──< analysis.score_history (many, via report_id)
analysis.analysis_reports (1) ──1 analysis.fundamental_health_scores
analysis.analysis_reports (1) ──1 analysis.valuation_analysis
analysis.analysis_reports (1) ──1 analysis.risk_metrics
analysis.analysis_reports (1) ──1 analysis.anomaly_detection

ml.model_metadata (1) ──< analysis.predictions (many, via models used)
ml.model_metadata (1) ──< ml.feature_importance (many)
ml.model_metadata (1) ──< ml.prediction_outcomes (many)
ml.model_metadata (1) ──< ml.model_drift_monitoring (many)
analysis.predictions (1) ──1 ml.prediction_outcomes

market_data.companies (1) ──< news.news_items (many)
market_data.companies (1) ──< news.sentiment_aggregates (many)
market_data.companies (1) ──< news.insider_transactions (many)

portfolio.users (1) ──< portfolio.watchlists (many)
portfolio.users (1) ──< portfolio.positions (many)
market_data.companies (1) ──< portfolio.watchlists (many)
market_data.companies (1) ──< portfolio.positions (many)
analysis.analysis_reports (1) ──< portfolio.positions (many, via entry_report_id)

market_data.companies (1) ──< analysis.backtest_runs (many)
ml.model_metadata (1) ──< analysis.backtest_runs (many)
```

---

## 15. Data Retention & Partitioning Notes

| Table | Partitioning Strategy | Retention |
|---|---|---|
| `market_data.price_data` | TimescaleDB hypertable, 1-week chunks | 10 years |
| `analysis.score_history` | TimescaleDB hypertable, 3-month chunks | 5 years |
| `news.news_items` | Standard table, monthly archival job | 2 years hot, archive after |
| `analysis.analysis_reports` | Standard table, JSONB payload | 1 year hot, archive after |
| `ml.model_drift_monitoring` | Standard table | 1 year |
| `audit.analysis_requests` | Standard table, monthly archival job | 1 year |
| `audit.data_quality_log` | Standard table, monthly archival job | 1 year |

TimescaleDB compression policies should be enabled on `price_data` and `score_history` chunks older than 90 days to reduce storage footprint while keeping query performance for point-in-time backtesting lookups.

---

## 16. Migration & Versioning

- Schema migrations managed via **Alembic** (paired with SQLAlchemy ORM)
- Every migration is additive-first: new columns nullable by default, backfilled via background job, then constrained in a follow-up migration
- No destructive migrations (`DROP COLUMN`, `DROP TABLE`) permitted against production without a reviewed data-archival step first
- `analysis.analysis_reports.report_data` JSONB payload is versioned via `disclaimer_version` and an internal `schema_version` key so historical reports remain parseable after report-structure changes
