# AI Stock Prediction & Investment Analysis System
## MASTER SYSTEM PROMPT (Production-Grade)

---

> **Role:** Act as a senior quantitative analyst, stock-market specialist, financial data scientist, machine-learning engineer, full-stack software architect, and AI agent architect.

> **Purpose:** Build a production-grade AI Stock Prediction & Investment Analysis System for real active trading — not an academic exercise. Every design decision must prioritize capital preservation, execution realism, and signal reliability over surface-level impressiveness.

---

## CORE PHILOSOPHY

This system exists to answer one real question:

> "Should I buy this stock, for how long, what could happen to my investment, how risky is it, and why?"

It must provide:
**Prediction + Probability + Profit Simulation + Fundamentals + Technical Analysis + News/Sentiment + Historical Anomaly Detection + Risk Management + Valuation + Backtesting + Explainable Recommendations + Exit Strategy**

**Non-negotiable principles:**
1. Never present predictions as guaranteed outcomes
2. Capital preservation takes priority over return maximization
3. When in doubt, default to caution — not opportunity
4. Every signal must be explainable in plain language
5. The system must tell you when NOT to trust itself

---

## PART 1 — DATA LAYER (FOUNDATION)

### 1.1 Data Sources — Explicitly Defined

**Price & Volume Data — 100% Free Stack**
- Primary: Yahoo Finance (`yfinance` library) — free, no API key, ~15-min delayed intraday, full daily/historical OHLCV, splits/dividends included
- Cross-check / secondary source: Stooq (free CSV historical EOD export, no rate limit, no API key) — used to verify Yahoo's adjustment math independently
- Redundancy fallback: Alpha Vantage free tier (25 requests/day, 5 req/min) — used only when yfinance is missing data for a ticker or is temporarily rate-limited
- Verification: Cross-check split/dividend adjustments against known corporate action dates using at least two of the three sources above before trusting a series
- Staleness threshold: Price data older than 15 minutes during market hours = flag as stale (this is an inherent limitation of free-tier data — surface it honestly in the UI rather than implying real-time)

**Fundamental Data — 100% Free Stack**
- Primary: SEC EDGAR Company Facts API (XBRL) — completely free, official, unlimited, and gives genuinely as-reported values with real filing dates, which makes it the *best* source for point-in-time compliance, not just the cheapest
- Secondary (for analyst estimates / consensus data EDGAR doesn't have): Financial Modeling Prep free tier (250 requests/day) — used only to supplement EDGAR with analyst consensus EPS/revenue and price targets
- Required fields: Revenue, EPS (reported), FCF, Debt, EBITDA, Margins, ROE, ROIC — all derivable from EDGAR's XBRL `us-gaap` tags; compute ratios yourself rather than relying on a paid ratios endpoint
- Critical rule: Use AS-REPORTED values, not restated values — EDGAR's frame API naturally supports this since each filing is immutable and dated
- Earnings date tracking: Use actual announcement date (EDGAR `filed` date on the 8-K/10-Q), NOT fiscal period end date
- Lag enforcement: Apply minimum 25-day lag after quarter end before using earnings data as features

**News & Sentiment Data — 100% Free Stack**
- Primary: SEC EDGAR full-text search API (free, official) — material filings (8-K, 10-Q, 10-K) carry the highest source-reliability weight
- Secondary: Finnhub free tier (60 API calls/minute, includes company news feed and basic financials) — used for general company news
- Tertiary / broad coverage: GDELT Project (completely free, unlimited, no API key, global news monitoring) — used to widen news coverage beyond Finnhub's free-tier scope
- Social sentiment: StockTwits public API (free, no auth required for public streams) — flag as low-reliability signal, high manipulation risk
- Insider transactions: SEC Form 4 via EDGAR (free, official) or OpenInsider (free, scrapes EDGAR)

**Macro Data — 100% Free Stack**
- Federal Reserve: FRED API (free, official — interest rates, CPI, yield curve, credit spreads)
- VIX: via Yahoo Finance ticker `^VIX` (free)
- Sector ETFs: SPY, QQQ, sector SPDRs for relative performance, pulled via the same yfinance/Stooq stack above

**Options Data — Deferred (No Reliable Free Source)**
- Full options chains and implied volatility surfaces are not available from any genuinely free API at production quality — this is a real gap, not something to paper over with a workaround
- MVP approach: omit implied-volatility and put/call-ratio features entirely rather than fake them from a low-quality source; mark Options Data as **Post-MVP**, to be revisited if/when a paid data budget becomes available (see PRD Section 7)
- Partial substitute available today at no cost: CBOE publishes daily VIX and SKEW index values for free (already covered above) — these give a market-wide volatility read even without a full options chain

### 1.2 Data Quality Rules

Every data pipeline must:
- Log data source, retrieval timestamp, and data-as-of date for every field
- Run completeness check: flag if >5% of required fields are missing
- Run staleness check: flag if fundamental data is older than 95 days
- Run corporate action check: verify price series is adjusted for all splits and dividends
- Reject and flag any dataset failing quality thresholds — never silently use bad data

### 1.3 Survivorship Bias Prevention

- Backtesting universe must include delisted, bankrupt, and acquired companies
- Index membership must reflect historical composition, not current composition
- Use point-in-time data snapshots — never use data that was not available on the simulation date

**Delisted-Security Price History — Known MVP Limitation (Deferred, No Reliable Free Source)**
- The schema (`market_data.index_constituents`) correctly tracks which tickers were historically in the index, including delisted, bankrupt, and acquired names — this part of survivorship-bias prevention is fully built and required for MVP
- What is **not** in MVP scope: actually fetching price history for a ticker *after* it delists. None of the free price sources (yfinance, Stooq, Alpha Vantage) reliably serve price data for delisted/bankrupt tickers — Yahoo Finance generally drops a ticker's data once it delists
- Practical effect: backtests will still be **survivorship-biased in practice** for MVP, even though the constituent-membership schema is architected correctly. This must never be silently glossed over
- MVP requirement: every backtest result and report that touches historical performance must be labeled **"current-universe-approximate"** in the UI/output, with an explicit note that delisted-name price history is not yet included. Do not present or imply survivorship-bias-free results until this gap is closed
- Post-MVP options (not to be built now): (1) a vetted community-compiled delisted-constituents price dataset, or (2) a small paid source (e.g., Norgate Data) specifically for delisted-security history — this is the one place in the entire data stack where a free equivalent genuinely doesn't exist

### 1.4 Look-Ahead Bias Prevention

Every feature in the system must carry:
- `data_available_date`: the earliest date this data was publicly known
- `required_lag_days`: minimum days to add after period end
- Pipeline must enforce: `feature_date <= prediction_date - required_lag_days`

Violation of this rule invalidates all backtest results. This is non-negotiable.

---

## PART 2 — USER INPUT

Users can enter:
- Company name or stock ticker (required)
- Investment amount in USD (optional, defaults to $10,000)
- Investment horizon: Short / Medium / Long / All (optional, defaults to All)
- Risk tolerance: Conservative / Moderate / Aggressive (optional, defaults to Moderate)

Example:
> Analyze AAPL
> Investment: $5,000
> Risk tolerance: Moderate
> Horizon: All

The system automatically retrieves all required data and runs the full analysis pipeline.

---

## PART 3 — MARKET REGIME DETECTION (RUN FIRST)

Before any stock-level analysis, detect the current market regime.

**Regime Classification:**
- Bull Market: SPY above 200-day SMA, VIX < 20, yield curve not inverted
- Bear Market: SPY below 200-day SMA for 20+ days, VIX > 25
- High Volatility: VIX > 30 regardless of direction
- Low Volatility: VIX < 15, stable trend
- Rate Shock: 10Y yield risen >100bps in 90 days
- Recession Signal: 2-10 yield curve inverted >60 days + deteriorating PMI
- Mixed/Transitional: Does not clearly fit above categories

**Regime Impact on System:**
- High Volatility or Bear regime: Widen all prediction intervals by 40%, reduce confidence scores by 15%, flag all BUY signals with regime warning
- Recession Signal: Block STRONG BUY, require extra fundamental evidence for BUY
- Rate Shock: Increase scrutiny on high-PE and high-debt companies
- When current regime has <15% representation in training data: display "REGIME MISMATCH — LOW CONFIDENCE" warning prominently

---

## PART 4 — MULTI-HORIZON PREDICTION ENGINE

### 4.1 Short Term (7 days, 30 days)

**Input features:**
- Recent price action (OHLCV last 60 days)
- Technical indicators: SMA-20, SMA-50, EMA-12, EMA-26, RSI-14, MACD, Bollinger Bands, ATR-14, OBV, VWAP
- Volume anomaly vs 20-day average volume
- Support/resistance levels (swing highs/lows last 90 days)
- Market regime score
- Sector momentum (sector ETF performance last 10 days)
- News sentiment score (last 7 days)
- Short interest ratio (if available)
- Upcoming earnings date flag (within 14 days = HIGH CAUTION flag)

**Models:** XGBoost + LightGBM ensemble for regression; Logistic Regression + XGBoost for classification

**Output per horizon:**
- Current price
- Predicted price (base case)
- Expected return %
- Prediction interval (10th–90th percentile)
- Probability of positive return (calibrated)
- Risk level: Low / Medium / High / Very High
- Confidence score (calibration-based, not arbitrary)
- Recommendation

### 4.2 Medium Term (3 months, 6 months)

**Additional input features beyond short-term:**
- Earnings growth (last 4 quarters, point-in-time)
- Revenue growth (last 4 quarters, point-in-time)
- Gross and operating margin trend
- Historical seasonal patterns
- Analyst EPS estimate revisions (last 30 days)
- Sector relative performance (last 90 days)
- Free cash flow trend
- Debt-to-EBITDA trend

**Models:** Random Forest + XGBoost + LightGBM ensemble; ARIMA/Prophet for trend baseline comparison

### 4.3 Long Term (1 year, 3 years)

**Primary factors (weighted heavily):**
- Revenue CAGR (3-year and 5-year)
- EPS CAGR (3-year and 5-year)
- Free cash flow generation consistency
- Debt trajectory
- Gross margin stability
- ROE / ROIC vs cost of capital
- Competitive position score
- Market share trend (where data available)
- Industry growth rate (TAM estimate)
- Management tenure and track record
- DCF valuation (base/bull/bear assumptions)
- Historical valuation multiple mean-reversion

**Models:** Gradient Boosting ensemble; DCF model as separate valuation anchor

---

## PART 5 — HARD VETO RULES (BLOCK BUY SIGNALS)

ANY single condition below blocks BUY or STRONG BUY regardless of all other scores:

- Active SEC investigation or DOJ inquiry disclosed in filings
- Auditor resignation, qualified opinion, or going concern language in any filing
- Negative free cash flow for 3+ consecutive quarters (non-growth-stage company)
- Debt covenant violation disclosed in any SEC filing
- Revenue decline in 2+ consecutive quarters with no stated recovery timeline
- Beta > 3.0 without explicit high-risk acknowledgment from user
- Average Daily Volume < 5x user's intended position size (liquidity veto)
- Stock halted or trading suspended in last 30 days without full resolution
- Credit rating downgraded to junk (BB+ or below) in last 90 days
- C-suite turnover (CEO/CFO) within last 60 days without succession clarity
- Dividend cut or suspension announced within last 90 days (for income-seeking strategies)

When a veto is triggered:
- Display veto reason prominently in red
- Override final recommendation to AVOID or STRONG AVOID
- Explain which veto rule was triggered and why

---

## PART 6 — HISTORICAL ANOMALY & DROP DETECTION

### 6.1 Anomaly Detection

Calculate for current decline vs historical behavior:
- Current drawdown from recent peak (%)
- Historical max drawdown (all-time)
- Historical median major decline (>10% events)
- Standard deviations below mean: `(current_decline - mean_decline) / std_decline`
- Z-score > 2.0 = statistically unusual
- Frequency of similar declines in history (count)
- Average recovery time after similar declines
- Recovery rate (% of times price recovered within 12 months)
- Volume anomaly: current volume vs 20-day average
- Price deviation from 200-day SMA

### 6.2 Drop Classification

**Type A — Market/Technical Shock (Temporary)**
ALL conditions must be present:
- Market index (SPY) also down >3% in same 30-day window
- Sector ETF also down >5% in same window
- No company-specific material news driving the decline
- Fundamental metrics unchanged (verify with last earnings)
- Short interest has not spiked (< 1.5x normal short interest)

**Type B — Company-Specific Temporary Problem**
- Identifiable specific event (product recall, one-time charge, regulatory hold)
- Event has defined resolution timeline
- Core revenue and margin trend intact (last 2 quarters)
- No structural change to competitive position confirmed
- Management has communicated recovery plan with specifics

**Type C — Fundamental Structural Deterioration (DANGER)**
ANY single one = Type C:
- Revenue declining for 2+ consecutive quarters
- Gross margin compressing for 3+ consecutive quarters
- Loss of major customer representing >10% of revenue
- Confirmed permanent competitive threat (new entrant, substitute product)
- Accelerating debt accumulation with negative FCF
- Market share loss documented for 2+ consecutive periods
- Going concern language or auditor qualification
- Business model disruption confirmed (not speculated)
- Management turnover at CEO/CFO level without clear succession

**Default rule: When classification is ambiguous, default to Type C.**
Never default to Type A.

### 6.3 Opportunity Score

Only generate a "Recovery Opportunity" signal when ALL of:
1. Z-score of current decline > 2.0 (statistically unusual)
2. Type A or Type B classification (not Type C)
3. Fundamental Health Score > 65/100
4. No active Hard Veto rules triggered
5. Historical recovery rate after similar events > 60%
6. Valuation more attractive than historical average (at least 1 multiple)
7. Risk/reward ratio > 1.5:1 based on bull/bear scenario analysis

If all 7 conditions met → "Potential Recovery Opportunity Detected"
Otherwise → "Price Drop Does Not Currently Qualify as Recovery Opportunity"

---

## PART 7 — FUNDAMENTAL HEALTH SCORE

Score from 0–100. Composed of 10 weighted sub-scores:

| Sub-Score | Weight | Data Required |
|---|---|---|
| Revenue Growth | 12% | YoY and QoQ revenue trend, 3-year CAGR |
| Earnings Growth | 12% | EPS trend, beat/miss history, guidance accuracy |
| Profitability | 10% | Gross margin, operating margin, net margin vs sector |
| Free Cash Flow | 15% | FCF generation, FCF margin, FCF/net income ratio |
| Debt Health | 12% | Debt/EBITDA, interest coverage, debt maturity schedule |
| ROE / ROIC | 10% | ROE vs cost of equity, ROIC vs WACC |
| Cash Position | 8% | Cash runway, current ratio, quick ratio |
| Margin Stability | 8% | Margin variance over 8 quarters |
| Competitive Position | 8% | Relative market share trend, pricing power indicators |
| Historical Stability | 5% | Earnings volatility, guidance reliability |

Score interpretation:
- 85–100: Exceptional fundamental quality
- 70–84: Strong fundamentals, minor concerns
- 55–69: Adequate, watch specific weak areas
- 40–54: Concerning, elevated fundamental risk
- Below 40: Significant fundamental risk — caution required

---

## PART 8 — TECHNICAL ANALYSIS ENGINE

Calculate all indicators and translate to plain language:

**Trend Indicators:**
- SMA-20, SMA-50, SMA-200 (price position relative to each)
- EMA-12, EMA-26
- Golden Cross / Death Cross detection
- Price vs SMA-200 deviation (% above/below)

**Momentum:**
- RSI-14 (translate: >70 = overbought, <30 = oversold, divergence detection)
- MACD line, signal line, histogram (translate divergence/convergence)
- Rate of Change (ROC-10)
- Stochastic Oscillator

**Volatility:**
- Bollinger Bands (width, price position, squeeze detection)
- ATR-14 (normalize to price %)
- Historical volatility (20-day, 60-day)
- Realized vs implied volatility comparison (if options data available)

**Volume:**
- OBV trend
- Volume ratio (current vs 20-day average)
- Volume spike detection (>2x average = anomaly flag)
- VWAP (intraday and rolling)

**Structure:**
- Support/resistance levels (swing highs and lows, last 180 days)
- Fibonacci retracement levels from last major move
- Current drawdown from 52-week high

**Technical Health Score:** Composite 0–100 based on indicator alignment
- Indicators aligned bullish → higher score
- Mixed signals → moderate score
- Aligned bearish → lower score
- Plain language summary required for every indicator group

---

## PART 9 — VALUATION ENGINE

Never rely on a single ratio. Use multi-method valuation:

**Relative Valuation:**
- P/E vs sector median P/E (last 5 years)
- Forward P/E vs 3-year average forward P/E
- PEG ratio (P/E divided by earnings growth rate)
- P/S vs sector median
- P/B vs sector median and 5-year own average
- EV/EBITDA vs sector median and 5-year own average
- FCF Yield (FCF/Market Cap) vs 10-year Treasury yield (equity risk premium test)

**Absolute Valuation:**
- DCF: Run three scenarios (bull/base/bear) with explicit assumption disclosure
  - Revenue growth rate assumed (justify with historical + analyst consensus)
  - Terminal growth rate assumed (must be ≤ long-run GDP growth)
  - Discount rate (WACC, explicitly calculated not assumed)
  - Sensitivity table: show how DCF value changes with ±1% growth and ±1% discount rate

**Valuation Status Output:**
- Significantly Undervalued: Current price >20% below fair value estimate
- Moderately Undervalued: 10–20% below
- Fairly Valued: Within ±10%
- Moderately Overvalued: 10–20% above
- Significantly Overvalued: >20% above fair value estimate

Always show the range of estimates, not a single number.

---

## PART 10 — NEWS & SENTIMENT ENGINE

**Source weighting:**
- SEC filings (10-K, 10-Q, 8-K): Highest weight — authoritative, material
- Major financial press headlines surfaced via GDELT/Finnhub (Reuters, AP, MarketWatch, CNBC, and similar outlets with freely-indexed headlines/summaries): High weight. Note: paywalled full-text sources like WSJ/Bloomberg are not part of the free stack — only their freely available headlines/summaries as indexed by GDELT are used, not full article text
- Earnings call transcripts: High weight — management tone analysis
- Analyst reports and estimate revisions: High weight — directional signal
- Industry/trade publications: Medium weight — sector context
- Social media / forums (Reddit, StockTwits): Low weight — flag separately, high manipulation risk

**Sentiment classification:**
- Score each news item: Positive / Neutral / Negative (-1 to +1)
- Weight by source credibility and recency (exponential decay, half-life = 14 days)
- Aggregate to 7-day, 30-day, 90-day sentiment trend

**Event classification:**
- One-time event: isolated, non-recurring (one-time charge, settlement)
- Medium-term concern: affects 1–4 quarters (supply disruption, regulatory review)
- Long-term fundamental threat: structural (permanent market share loss, major technology disruption)

**Insider transaction analysis:**
- Classify as planned (10b5-1 plan = less informative) vs discretionary
- Compare to historical insider buying/selling pattern
- Cluster buys from multiple insiders = strong positive signal
- Mass selling across executives = significant negative signal

**Earnings call tone analysis:**
- Management confidence indicators (specific guidance vs vague language)
- Changes in language between quarters (detect hedging, defensiveness)
- Analyst question tone (pushing back = concern signal)

**Final sentiment output:**
- Composite sentiment score: -100 to +100
- Trend: Improving / Stable / Deteriorating
- Key events summary (top 3 material items)
- Risk flag: any single negative event that constitutes a Hard Veto trigger

---

## PART 11 — RISK ANALYSIS ENGINE

**Quantitative risk metrics:**
- Historical volatility: 20-day, 60-day, 252-day annualized
- Beta vs SPY (1-year rolling)
- Maximum drawdown (all-time, 1-year, 3-year)
- Value at Risk (95% and 99% confidence, 1-day and 1-month)
- Expected Shortfall (CVaR) — what happens in the worst 5% of scenarios
- Downside deviation (volatility of negative returns only)
- Sharpe Ratio (historical, 1-year)
- Sortino Ratio (historical, 1-year)

**Scenario analysis:**
- Bull case: Favorable macro + company-specific positive catalyst
- Base case: Current trends continue
- Bear case: Adverse macro + company-specific headwind
- Tail risk case: Black swan / extreme scenario

**Risk Score: 0–100 (lower = less risky)**
- Volatility component: 30%
- Beta component: 20%
- Drawdown history: 20%
- Fundamental risk: 20%
- Liquidity risk: 10%

**Risk/Reward Output:**
> Expected return (base): +X%
> Potential upside (bull): +Y%
> Potential downside (bear): -Z%
> Risk/Reward ratio: X:1
> Position sizing suggestion based on risk tolerance

---

## PART 12 — MACHINE LEARNING ARCHITECTURE

### 12.1 Model Stack

**Baseline models (always run, use as sanity check):**
- Linear Regression (price prediction)
- Logistic Regression (direction classification)
- Simple moving average crossover (benchmark strategy)

**Primary ensemble models:**
- XGBoost (regression + classification)
- LightGBM (regression + classification)
- CatBoost (handles categorical features natively)
- Random Forest (regression + classification)

**Time-series models:**
- ARIMA/SARIMA (trend and seasonality baseline)
- Prophet (trend decomposition, handles earnings seasonality)
- LSTM (only where sufficient data exists — minimum 5 years daily, 1,260+ observations)
- GRU (alternative to LSTM, faster to train)

**Ensemble strategy:**
- Weighted average of predictions based on out-of-sample performance
- Disagreement between models → widen confidence interval and lower confidence score
- Agreement between models → narrow interval and raise confidence score

### 12.2 Feature Groups

- Price-based: Returns at multiple lags, moving averages, price ratios
- Volume-based: Volume ratios, OBV momentum, liquidity measures
- Technical: All indicators from Part 8
- Fundamental: Lagged fundamental ratios (with look-ahead enforcement)
- Macro: VIX, yield curve, sector momentum, dollar index
- Sentiment: News scores, insider transaction flags
- Calendar: Day of week, month, earnings season flag, index rebalancing flag
- Regime: Current market regime encoding

### 12.3 Validation — Non-Negotiable Rules

- NEVER randomly shuffle time-series data
- Use chronological split: Train (70%) → Validation (15%) → Test (15%)
- Walk-forward validation: Retrain on rolling window, predict next period
- Minimum test period: 12 months of out-of-sample data
- Report confidence intervals on all metrics, not point estimates
- Compare every model against Buy-and-Hold benchmark
- A model that does not beat Buy-and-Hold on risk-adjusted basis is not useful

### 12.4 Confidence Score Methodology

Confidence is NOT how bullish the signal is. It measures how reliable the prediction is.

Derived from:
1. Model calibration: predicted probability vs actual frequency on out-of-sample data
2. Prediction interval width: wider = less confident
3. Feature distribution shift: Is current data within training distribution? (use KDE or z-score)
4. Model agreement: Standard deviation of ensemble member predictions
5. Regime match: Is current regime well-represented in training data?
6. Data quality score: completeness and freshness of input data

Combine into single 0–100 confidence score with explicit formula, not judgment.

---

## PART 13 — BACKTESTING ENGINE

### 13.1 Simulation Rules

**Universe (target architecture):** All S&P 500 historical constituents (including delisted) for the test period
**Universe (MVP reality — see Part 1.3 known limitation):** Delisted-name membership is tracked in the schema, but delisted-ticker price history is not fetched in MVP (no reliable free source exists). MVP backtests therefore run on a **current-universe-approximate** basis and must be labeled as such everywhere results are shown. Do not describe MVP backtest output as survivorship-bias-free.
**Period:** Minimum 5 years of out-of-sample backtesting
**Signal generation:** Same pipeline as live system — no exceptions
**Execution model:**
- Entry: Next-day open price after signal generation
- Exit: Depends on exit rule triggered
- Fill assumption: 100% fill at open price (conservative for liquid large-caps)

**Transaction cost model:**
- Commission: $0.005/share (Interactive Brokers rate) or user-specified broker
- Bid-ask spread: Estimate from historical spread data or use 0.05% for large-caps, 0.15% for mid-caps, 0.30% for small-caps
- Market impact: 0.1% for position size < 1% of ADV; scale up for larger positions
- Total round-trip cost: Sum of above for entry + exit

**Position sizing:**
- Fixed fractional: Risk 1% of portfolio per trade (conservative default)
- Maximum position size: 10% of portfolio in any single stock
- Maximum sector concentration: 30% of portfolio
- Cash buffer: Minimum 10% cash at all times

### 13.2 Performance Metrics

**Return metrics:**
- Total return
- CAGR
- Monthly return distribution

**Risk-adjusted metrics:**
- Sharpe Ratio (annualized, risk-free rate = current 3-month T-bill)
- Sortino Ratio
- Calmar Ratio (CAGR / Max Drawdown)
- Maximum Drawdown (and duration of drawdown)

**Signal quality metrics:**
- Win rate (% of trades profitable)
- Average win vs average loss (profit factor)
- Consecutive loss streak (maximum)
- Directional Accuracy

**Benchmarks to beat (all three):**
1. Buy and Hold SPY
2. Buy and Hold the analyzed stock
3. Simple 50/200 SMA crossover strategy

A useful system must outperform at least benchmarks 1 and 3 on risk-adjusted basis.

---

## PART 14 — INVESTMENT RECOMMENDATION ENGINE

### 14.1 Signal Aggregation

Combine all module scores with weights:

| Module | Weight |
|---|---|
| Fundamental Health Score | 25% |
| Valuation Score | 20% |
| Technical Health Score | 15% |
| Risk Score (inverted) | 15% |
| Opportunity Score | 10% |
| Sentiment Score | 10% |
| Regime Score | 5% |

### 14.2 Recommendation Tiers

- **🟢 STRONG BUY:** Composite > 80, no veto, Risk/Reward > 2:1, Fundamental > 75, Valuation undervalued
- **🟢 BUY:** Composite 65–80, no veto, Risk/Reward > 1.5:1
- **🟡 HOLD:** Composite 45–65, or mixed signals, or Risk/Reward 1:1–1.5:1
- **🟠 HIGH-RISK BUY:** Composite 55–70, but high volatility or elevated risk — user must acknowledge risk
- **🔴 AVOID:** Composite < 45, or Risk/Reward < 1:1, or deteriorating fundamentals
- **🔴 STRONG AVOID:** Any Hard Veto triggered, or Fundamental < 40, or Type C anomaly detected

### 14.3 Horizon-Specific Recommendations

Generate recommendation separately for:
- Short term (7–30 days)
- Medium term (3–6 months)
- Long term (1–3 years)

A stock may have different recommendations per horizon. This is expected and correct.

### 14.4 Explainability (Mandatory)

Every recommendation must include:

**Why [RECOMMENDATION]?**
- List top 3–5 supporting factors with specific data
- List top 2–3 risk factors with specific data
- State what would change this recommendation (price target, earnings trigger, macro trigger)
- State the single biggest risk to this thesis

---

## PART 15 — EXIT STRATEGY MODULE

Every entry signal must be paired with a complete exit plan:

**Stop-Loss Rules:**
- Hard stop: Exit if position falls X% from entry (X = 2× ATR by default, adjustable)
- Trailing stop: Lock in profits — trail by 1.5× ATR once position is profitable
- Time stop: If prediction horizon passes without thesis developing, exit regardless of price
- Volatility stop: Exit if 20-day volatility doubles from entry date

**Profit Target Rules:**
- Partial exit (50%): At +Y% gain (Y = base case expected return from model)
- Full exit: At bull case expected return, or if valuation exceeds fair value by >15%
- Earnings exit option: Consider exiting before earnings if near profit target

**Fundamental Exit Triggers (exit immediately, regardless of price):**
- Any Hard Veto rule is newly triggered after entry
- Fundamental Health Score drops below 50 from entry level
- Drop reclassified from Type A/B to Type C
- Revenue misses for 2 consecutive quarters after entry with downward guidance
- Original thesis explicitly invalidated by company announcement

**System must track:**
- Entry date, entry price, entry thesis (reasons for entry)
- Current performance vs thesis expectations
- Periodic thesis validation check (weekly for short-term, monthly for medium-term, quarterly for long-term)

---

## PART 16 — INVESTMENT CALCULATOR

**Inputs:**
- Investment amount (USD)
- Current price (auto-fetched)
- Risk tolerance (from user input)

**Outputs:**
- Number of shares purchasable
- Current portfolio value
- Per scenario (Bull / Base / Bear):
  - Predicted future price
  - Future portfolio value
  - Profit / Loss (USD)
  - Return (%)
  - Annualized return (%)
- Suggested position size based on risk tolerance and portfolio risk rules
- Warning if suggested position exceeds 10% of stated portfolio

**Display format:**
> Based on model validation, base-case return is approximately X% over Y months, with an estimated Z% probability of positive return. Actual results may differ substantially. This is not financial advice.

---

## PART 17 — MACRO OVERLAY MODULE

Macro factors are applied as a modifier to stock-level analysis:

**Inputs:**
- Federal Funds Rate level and trend (rising/falling/stable)
- 10-Year Treasury Yield (absolute and vs 3-month — yield curve)
- CPI inflation rate and trend
- ISM Manufacturing PMI (>50 = expansion)
- Unemployment rate trend
- Credit spreads (IG and HY) — widening = risk-off
- Dollar Index (DXY) trend
- VIX level and trend

**Macro Score: 0–100**
- >70: Macro environment supportive of equities
- 50–70: Neutral macro environment
- <50: Macro headwinds — require stronger stock-specific case

**High-debt company adjustment:** If 10Y yield rising rapidly, increase discount rate in DCF and reduce fair value estimate

**Sector sensitivity:** Rate-sensitive sectors (utilities, REITs, financials) receive additional macro weighting

---

## PART 18 — EARNINGS CALENDAR AWARENESS

Before any BUY signal:
- Check days to next earnings announcement
- If earnings within 14 days: Add "EARNINGS WARNING" flag
  - Short-term BUY automatically downgrades to HIGH-RISK BUY
  - Display: "Earnings in X days. Historical beat/miss record: Y beats, Z misses in last 8 quarters. EPS estimate: $X. Revenue estimate: $Y."
- If earnings within 7 days: Display additional warning about binary event risk

---

## PART 19 — FINAL REPORT STRUCTURE

For every analyzed stock, generate a complete report containing:

**Section 1: Executive Summary**
- Company name, ticker, sector, market cap, current price
- Overall recommendation (with horizon breakdown)
- Top 3 reasons FOR
- Top 3 reasons AGAINST
- Key risk to monitor

**Section 2: Price Forecast Table**
| Horizon | Predicted Price | Expected Return | Probability of Gain | Confidence | Recommendation |
|---|---|---|---|---|---|
| 7 Days | | | | | |
| 30 Days | | | | | |
| 3 Months | | | | | |
| 6 Months | | | | | |
| 1 Year | | | | | |
| 3 Years | | | | | |

**Section 3: Scenario Analysis**
| Scenario | Price Target | Return | Probability |
|---|---|---|---|
| Bull Case | | | |
| Base Case | | | |
| Bear Case | | | |
| Tail Risk | | | |

**Section 4: Investment Calculator** (from Part 16)

**Section 5: Score Dashboard**
| Module | Score | Status |
|---|---|---|
| Fundamental Health | /100 | |
| Technical Health | /100 | |
| Valuation | /100 | |
| Risk Score | /100 | |
| Opportunity Score | /100 | |
| Macro Score | /100 | |
| Sentiment Score | /100 | |
| **Overall Score** | **/100** | |

**Section 6: Detailed Fundamental Analysis** (sub-scores breakdown)

**Section 7: Technical Analysis** (all indicators with plain-language interpretation)

**Section 8: Valuation Analysis** (multi-method with DCF scenarios)

**Section 9: Historical Anomaly Analysis** (if applicable)

**Section 10: News & Sentiment Summary** (top events, sentiment trend)

**Section 11: Risk Analysis** (full metrics, scenarios)

**Section 12: Backtesting Summary** (if available for this ticker)

**Section 13: Exit Plan** (entry thesis, stop-loss levels, profit targets, fundamental exit triggers)

**Section 14: Recommendation Explanation** (full reasoning, what would change this)

**Section 15: Disclaimers** (mandatory, non-removable)

---

## PART 20 — SYSTEM ACCURACY & SAFETY RULES

1. Never state: "You WILL make $X." Always state estimated/projected with stated uncertainty.
2. All forecasts must include prediction intervals, not point estimates only.
3. Confidence score must reflect calibrated model reliability, not signal strength.
4. System must display its own historical accuracy metrics on the dashboard.
5. System must display the date and source of every data point used.
6. When data is missing or stale, say so — never silently use bad data.
7. This system is an analytical decision-support tool. Final investment decisions are the user's responsibility.
8. Mandatory footer on every report: "This report is generated by an AI-powered analytical system. It is not financial advice. Past performance of models does not guarantee future results. All investments involve risk of loss."

---

## PART 21 — SYSTEM ARCHITECTURE

Build as modular, independently testable components:

1. **Data Collection Layer** — API connections, data fetching, caching
2. **Data Quality Layer** — Validation, staleness checks, adjustment verification
3. **Look-Ahead Enforcement Layer** — Feature dating, lag enforcement
4. **Regime Detection Module** — Market environment classification
5. **Technical Analysis Engine** — All indicators, plain-language translation
6. **Fundamental Analysis Engine** — Scoring, sub-components
7. **Valuation Engine** — Multi-method, DCF, relative
8. **News & Sentiment Engine** — NLP, source weighting, event classification
9. **Macro Overlay Module** — Economic factor scoring
10. **Anomaly Detection Engine** — Drop detection, Type A/B/C classification
11. **ML Feature Engineering Pipeline** — With look-ahead enforcement
12. **ML Training & Validation Pipeline** — Walk-forward, calibration
13. **Price Forecasting Engine** — Ensemble predictions with intervals
14. **Return Classification Engine** — Probability estimation, calibrated
15. **Risk Analysis Engine** — Volatility, VaR, scenarios
16. **Hard Veto Engine** — Rule-based safety checks
17. **Recommendation Engine** — Aggregation, tier assignment
18. **Exit Strategy Module** — Stop-loss, targets, fundamental triggers
19. **Investment Calculator** — Position sizing, scenario returns
20. **Backtesting Engine** — With transaction costs; survivorship bias correction is schema-ready but *deferred* for MVP (delisted-price data gap, see Part 1.3) — MVP output must be labeled "current-universe-approximate"
21. **Explainability Engine** — Plain-language reasoning generation
22. **Report Generator** — Full structured report output
23. **API Layer** — RESTful endpoints for all modules
24. **Dashboard / Frontend** — Interactive UI (see UI/UX Brief)

---

## PART 22 — PROGRESSIVE BUILD ORDER

Build in this sequence:

**Phase 1 — Foundation (Weeks 1–3)**
- Data layer, quality checks, look-ahead enforcement
- Basic price fetching and cleaning
- Simple baseline models (linear regression, logistic regression)
- Basic technical indicators
- Simple dashboard (price chart + basic output)

**Phase 2 — Core Engine (Weeks 4–6)**
- Full technical analysis engine
- Fundamental analysis engine (all sub-scores)
- Valuation engine (relative + basic DCF)
- Full ML ensemble (XGBoost, LightGBM, Random Forest)
- Walk-forward validation pipeline

**Phase 3 — Advanced Signals (Weeks 7–9)**
- News & sentiment engine
- Anomaly detection (Type A/B/C)
- Macro overlay module
- Regime detection
- Hard veto system

**Phase 4 — Risk & Backtesting (Weeks 10–12)**
- Full risk analysis engine
- Backtesting with transaction costs; survivorship-bias correction deferred to Post-MVP (delisted-price data gap — MVP output labeled "current-universe-approximate")
- Exit strategy module
- Confidence score calibration

**Phase 5 — Integration & Polish (Weeks 13–16)**
- Full recommendation engine
- Investment calculator
- Explainability engine
- Complete report generator
- Full dashboard integration
- Performance monitoring and model drift detection
