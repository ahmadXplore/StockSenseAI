# App Flow Document
## AI Stock Prediction & Investment Analysis System
**Version:** 1.0 | **Date:** 2026

---

## 1. High-Level User Journeys

### Journey 1: New Analysis (Primary Flow)
```
Landing / Dashboard
    → Enter Ticker
    → Configure Analysis (amount, horizon, risk tolerance)
    → Loading Screen (progress indicators)
    → Full Analysis Report
        → Executive Summary
        → Price Forecast Table
        → Score Dashboard
        → Investment Calculator
        → Technical Analysis
        → Fundamental Analysis
        → Valuation Analysis
        → News & Sentiment
        → Risk Analysis
        → Exit Strategy
        → Historical Anomaly (if applicable)
        → Backtesting Summary
    → Add to Watchlist (optional)
    → Record Position (optional)
```

### Journey 2: Watchlist Monitoring
```
Dashboard
    → Watchlist Panel
    → See all stocks at-a-glance (score, rec, last price, thesis status)
    → Click stock → Full Report (cached or refresh)
    → View Earnings Calendar
    → Receive anomaly alerts
```

### Journey 3: Portfolio Position Tracking
```
Portfolio Tab
    → View open positions (entry price, current P&L, thesis status)
    → Thesis Validation Check (is the original reason still valid?)
    → View exit plan for each position
    → Get alerted if stop-loss or fundamental trigger hit
```

---

## 2. Detailed Screen Flows

### 2.1 Landing / Dashboard Screen

**URL:** `/dashboard`

**Elements:**
- Top bar: Logo | Navigation | User menu
- Hero section: Search bar (large, centered) with placeholder "Enter ticker or company name…"
- Quick Market Context bar: SPY | QQQ | VIX | Current Regime badge
- Recent Analyses (last 3 reports)
- Watchlist summary panel (collapsed, expandable)
- Market regime banner (changes color by regime: green=bull, red=bear, yellow=volatile)

**Actions:**
- Search → navigates to Analysis Loading Screen
- Click recent analysis → navigates to cached Report Screen
- Click watchlist item → navigates to Report Screen

---

### 2.2 Analysis Configuration Screen

**URL:** `/analyze?ticker=AAPL`

**Triggered by:** Submitting ticker in search

**Elements:**
- Confirmed ticker + company name + sector (auto-fetched, displayed immediately)
- Current price (live)
- Configuration panel:
  - Investment Amount (input, USD, default $10,000)
  - Horizon selector: Short | Medium | Long | All (toggle buttons, default All)
  - Risk Tolerance: Conservative | Moderate | Aggressive (3-way toggle, default Moderate)
- "Run Analysis" button (primary CTA)
- "Quick Preview" link (shows basic metrics without full ML run)

**Validation:**
- Ticker must resolve to a known stock
- If ticker not found: show "Ticker not found. Did you mean: [suggestions]?"
- Investment amount: 0 is allowed (skips calculator), no upper limit
- All fields have sensible defaults so user can proceed immediately

---

### 2.3 Analysis Loading Screen

**URL:** `/analyze/AAPL/loading`

**Elements:**
- Animated progress bar
- Step indicators with current step highlighted:
  1. ✅ Fetching price data
  2. ✅ Loading fundamentals
  3. 🔄 Running ML models (currently active)
  4. ⬜ Technical analysis
  5. ⬜ Sentiment analysis
  6. ⬜ Risk calculation
  7. ⬜ Generating report

- Estimated time remaining
- Fun fact / educational tip while waiting (rotates every 3s)
- Cancel button

**Behavior:**
- Backend runs as async Celery task
- Frontend polls `/analyze/{report_id}/status` every 2 seconds
- On complete: auto-redirect to Report Screen
- On error: show error with retry option and specific error message

---

### 2.4 Full Report Screen

**URL:** `/report/AAPL/{report_id}`

**Layout:** Sticky left sidebar navigation + scrollable main content

**Left Sidebar (navigation):**
```
├── Executive Summary
├── Recommendations
├── Price Forecast
├── Score Dashboard
├── Investment Calculator
├── Fundamental Analysis
├── Technical Analysis
├── Valuation Analysis
├── News & Sentiment
├── Risk Analysis
├── Historical Anomaly
├── Exit Strategy
├── Backtesting  (MVP: header always shows "Current-Universe-Approximate" badge — see known limitation, PRD Section 5 / Master Prompt Part 1.3)
└── Disclaimers
```

**Top Report Banner:**
```
┌──────────────────────────────────────────────────────────┐
│ AAPL — Apple Inc.          $225.50    ▲ +1.2% today      │
│ Technology | NASDAQ | Market Cap: $3.4T                   │
│ Report generated: 2025-08-24 14:30 | Data as of: 14:25   │
│                                          [Add to Watchlist]│
└──────────────────────────────────────────────────────────┘
```

**Veto Banner (appears at top if triggered, RED):**
```
┌──────────────────────────────────────────────────────────┐
│ ⛔ VETO TRIGGERED: [Veto Rule Name]                       │
│ [Explanation of why this blocks a BUY signal]             │
│ Final Recommendation overridden to: STRONG AVOID          │
└──────────────────────────────────────────────────────────┘
```

**Regime Warning Banner (appears if regime mismatch, YELLOW):**
```
┌──────────────────────────────────────────────────────────┐
│ ⚠️ REGIME WARNING: Current market in HIGH VOLATILITY       │
│ Confidence scores reduced by 15%. All intervals widened.  │
└──────────────────────────────────────────────────────────┘
```

---

### 2.4.1 Executive Summary Section

```
┌─────────────────────────────────────────────────────────┐
│  OVERALL SCORE: 78/100        [Progress circle]          │
│                                                          │
│  SHORT TERM:  🟢 BUY    (Confidence: 71%)               │
│  MEDIUM TERM: 🟢 BUY    (Confidence: 66%)               │
│  LONG TERM:   🟢 STRONG BUY (Confidence: 74%)           │
│                                                          │
│  ✅ REASONS FOR                                          │
│  • Strong revenue growth (18% YoY)                       │
│  • FCF yield of 4.2% vs 10Y at 4.5% (near inflection)  │
│  • Current P/E below 5-year average by 12%               │
│                                                          │
│  ❌ REASONS AGAINST                                      │
│  • Beta 1.24 — market-correlated risk                    │
│  • High regulatory risk in EU market                     │
│                                                          │
│  🔑 KEY RISK TO MONITOR: Earnings in 8 days             │
└─────────────────────────────────────────────────────────┘
```

---

### 2.4.2 Price Forecast Section

**Table view:**

| Horizon | Current | Predicted | Return | P(Gain) | Confidence | Signal |
|---|---|---|---|---|---|---|
| 7 Days | $225.50 | $229.10 | +1.6% | 62% | 71% | 🟢 BUY |
| 30 Days | $225.50 | $238.40 | +5.7% | 68% | 68% | 🟢 BUY |
| 3 Months | $225.50 | $248.00 | +10.0% | 65% | 62% | 🟢 BUY |
| 6 Months | $225.50 | $261.30 | +15.9% | 63% | 60% | 🟡 HOLD |
| 1 Year | $225.50 | $275.00 | +22.0% | 61% | 58% | 🟢 BUY |
| 3 Years | $225.50 | $350.00 | +55.2% | 74% | 52% | 🟢 STRONG BUY |

**Prediction interval toggle:** Show/hide 10th–90th percentile range

**Scenario cards (3 cards side by side):**
```
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│  🐂 BULL    │  │  📊 BASE    │  │  🐻 BEAR    │
│             │  │             │  │             │
│  +35%       │  │  +22%       │  │  -12%       │
│  $304       │  │  $275       │  │  $198       │
│  Prob: 25%  │  │  Prob: 50%  │  │  Prob: 20%  │
│             │  │             │  │             │
│  P: $5,000  │  │  P: $5,000  │  │  P: $5,000  │
│  V: $6,750  │  │  V: $6,100  │  │  V: $4,400  │
│  G: +$1,750 │  │  G: +$1,100 │  │  L: -$600   │
└─────────────┘  └─────────────┘  └─────────────┘

+ Tail Risk: -35% ($3,250) Probability: 5%
```

---

### 2.4.3 Score Dashboard Section

**Radial/spider chart showing all scores + individual cards:**

```
Fundamental Health:    82/100  ████████░░  STRONG
Technical Health:      67/100  ██████░░░░  MODERATE
Valuation:             71/100  ███████░░░  MODERATELY UNDERVALUED
Risk Score:            44/100  ████░░░░░░  MODERATE RISK
Opportunity Score:     38/100  ███░░░░░░░  NO ACTIVE OPPORTUNITY
Macro Score:           59/100  █████░░░░░  NEUTRAL
Sentiment Score:       68/100  ██████░░░░  MODERATELY POSITIVE
─────────────────────────────────────────
Overall Score:         78/100  ████████░░  STRONG
```

Each score card is expandable → shows sub-components.

---

### 2.4.4 Investment Calculator Section

```
Investment Amount: [$5,000    ]  [Calculate]

Shares purchasable: 22.2 shares @ $225.50

┌─────────────────────────────────────────────────────────┐
│  SCENARIO PROJECTIONS                                    │
├────────────┬──────────┬───────────┬──────────┬─────────┤
│            │ 1 Month  │ 6 Months  │ 1 Year   │ 3 Years │
├────────────┼──────────┼───────────┼──────────┼─────────┤
│ Bull Case  │ $5,420   │ $6,250    │ $6,750   │ $9,800  │
│ Base Case  │ $5,285   │ $5,795    │ $6,100   │ $7,760  │
│ Bear Case  │ $4,800   │ $4,530    │ $4,400   │ $4,250  │
│ Tail Risk  │ —        │ $3,750    │ $3,250   │ —       │
├────────────┴──────────┴───────────┴──────────┴─────────┤
│ Suggested position: $2,800 (56% of $5,000) based on     │
│ moderate risk tolerance & 1% portfolio risk rule         │
└─────────────────────────────────────────────────────────┘
⚠ Disclaimer: Projections based on model estimates. 
  Actual returns may differ substantially.
```

---

### 2.4.5 Fundamental Analysis Section

**Sub-score table + expandable detail:**

| Category | Score | Status | Key Metric |
|---|---|---|---|
| Revenue Growth | 85/100 | 🟢 Strong | 18.2% YoY |
| Earnings Growth | 88/100 | 🟢 Strong | EPS +22% YoY |
| Profitability | 91/100 | 🟢 Exceptional | Net margin 26.1% |
| Free Cash Flow | 94/100 | 🟢 Exceptional | FCF $102B TTM |
| Debt Health | 76/100 | 🟢 Good | D/EBITDA: 0.8x |
| ROE / ROIC | 89/100 | 🟢 Strong | ROIC 28% vs WACC 9% |
| Cash Position | 82/100 | 🟢 Strong | Net cash $60B |
| Margin Stability | 88/100 | 🟢 Strong | Low variance |
| Competitive Position | 85/100 | 🟢 Strong | Moat: HIGH |
| Historical Stability | 80/100 | 🟢 Strong | Consistent beat rate |

Expandable: click any row → shows 8-quarter trend chart for that metric

---

### 2.4.6 Technical Analysis Section

**Price chart:** TradingView Lightweight Charts with toggle overlays:
- SMA 20/50/200
- Bollinger Bands
- Volume bars

**Indicator summary cards:**
```
TREND           MOMENTUM        VOLATILITY      VOLUME
───────         ──────────      ──────────      ──────
🟢 BULLISH      🟡 NEUTRAL      🟡 MODERATE     🟢 HIGH
                                
Price above     RSI: 54.2       BB Width: 3.2%  Vol 1.4x avg
SMA-20/50/200   (Neutral zone)  (Normal)        (Elevated)
Golden cross    MACD: Positive  ATR: $4.20      OBV: Rising
confirmed 30d   divergence      (1.9% of price)
```

**Support/Resistance levels:**
```
Resistance 2: $245.00  (52-week high zone)
Resistance 1: $232.50  (Recent swing high)
─────────────────────
Current:       $225.50
─────────────────────
Support 1:     $218.00  (SMA-50)
Support 2:     $205.00  (SMA-200)
```

---

### 2.4.7 Valuation Section

```
VALUATION STATUS: ⬇ MODERATELY UNDERVALUED (13% below fair value)

Fair Value Estimate Range: $245 — $275

Method              Current   Fair Value  Status
──────────────────────────────────────────────────
P/E (vs 5Y avg)     28.5x     32.1x      Undervalued
Forward P/E         24.2x     27.0x      Undervalued
PEG Ratio           1.31      1.45       Undervalued
EV/EBITDA           19.4x     22.0x      Undervalued
P/FCF               22.1x     25.0x      Undervalued
DCF (Base Case)     $225      $258       Undervalued (-13%)
──────────────────────────────────────────────────
Consensus           —         $260       Undervalued (-13%)

[DCF Assumptions]
Revenue growth: 8% (Y1-3), 6% (Y4-7), 3% terminal
WACC: 9.2%  |  Terminal growth: 3.0%
[Sensitivity table toggle]
```

---

### 2.4.8 News & Sentiment Section

```
SENTIMENT SCORE: 68/100  ↑ Improving (last 7 days: +0.12)

Timeline view:
Aug 20 ● [HIGH] Q3 Earnings beat: EPS $1.52 vs $1.44 expected  POSITIVE
Aug 18 ○ [MED]  EU Digital Markets Act compliance update        NEUTRAL
Aug 15 ● [HIGH] Services revenue reaches record $24.2B          POSITIVE
Aug 10 ○ [LOW]  Analyst PT raised to $260 at Goldman Sachs      POSITIVE
Aug 08 ○ [MED]  Supply chain article — no material impact       NEUTRAL

Sentiment trend chart: 90-day rolling score

Insider Activity:
Aug 14 — CFO sold 12,000 shares ($2.7M) [10b5-1 plan — PLANNED]
Jul 30 — Director purchased 5,000 shares ($1.1M) [Discretionary — POSITIVE]

⚠ Earnings in 8 days — binary event risk. [Details ▼]
```

---

### 2.4.9 Risk Analysis Section

```
RISK SCORE: 44/100 (MODERATE RISK)

Quantitative Metrics
──────────────────────────────────────────
Historical Volatility (20d):    22.4% ann.
Historical Volatility (252d):   26.1% ann.
Beta (vs SPY, 1Y):              1.24
Max Drawdown (all-time):        -82.0% (2003)
Max Drawdown (3Y):              -27.3% (2022)
Sharpe Ratio (1Y):              1.42
Sortino Ratio (1Y):             2.01
VaR 95% (1 month):              -8.2%
CVaR 95% (1 month):             -12.4%

Risk/Reward Summary
──────────────────────────────────────────
Expected Return (base, 1Y):     +22.0%
Upside (bull, 1Y):              +35.0%
Downside (bear, 1Y):            -12.0%
Risk/Reward Ratio:              1.83:1  ✅

Position Sizing Recommendation
──────────────────────────────────────────
Conservative:   1.5% of portfolio
Moderate:       2.5% of portfolio
Aggressive:     4.0% of portfolio
```

---

### 2.4.10 Exit Strategy Section

```
EXIT PLAN (Generated at report time — update if price changes >10%)

Entry Reference: $225.50

STOP-LOSS RULES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Hard Stop:          $209.00  (-7.3%)  [2× ATR below entry]
Trailing Stop:      Activate at $238+, trail by $6.30 (1.5× ATR)
Time Stop:          Exit if price < $230 by Nov 1, 2025 (90-day horizon)
Volatility Stop:    Exit if 20d vol exceeds 45% annualized

PROFIT TARGETS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Partial Exit (50%): $247.00  (+9.5%)  [Model base case, 6M]
Full Exit:          $275.00  (+22%)   [Model bull case / DCF fair value]
Earnings Play:      Consider 50% exit before earnings (8 days)

FUNDAMENTAL EXIT TRIGGERS (Exit immediately if ANY occur)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• Revenue misses for 2 consecutive quarters
• Services revenue growth decelerates below 5% YoY
• Gross margin compresses below 42%
• FCF drops below $80B TTM
• Any new SEC investigation disclosed
• China market ban affecting >15% of revenue
• Drop reclassified from Type A/B to Type C

THESIS STATEMENT (Validate weekly)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Entry thesis: Strong FCF + valuation below historical average 
+ Services segment driving margin expansion + current P/E below 
5Y mean suggesting mean-reversion opportunity.
```

---

### 2.4.11 Historical Anomaly Section (Conditional)

Only displayed if current decline > 1.5 standard deviations below historical mean.

```
┌─────────────────────────────────────────────────────────┐
│  📊 HISTORICAL ANOMALY ANALYSIS                          │
│                                                          │
│  Current decline: -18.3% from peak                      │
│  Historical average major decline: -12.1%                │
│  Z-score: 2.4 (Statistically unusual)                   │
│  Similar events in history: 4                            │
│  Recovery within 12 months: 3 of 4 times (75%)          │
│  Average recovery time: 7.2 months                       │
│                                                          │
│  CLASSIFICATION: TYPE A — Market/Technical Shock         │
│  Reason: SPY also -14% in same period; no company-       │
│  specific news; fundamentals unchanged                    │
│                                                          │
│  OPPORTUNITY SCORE: 64/100                               │
│  Status: ✅ POTENTIAL RECOVERY OPPORTUNITY DETECTED       │
│  (6 of 7 required conditions met)                        │
│  Condition not met: Historical recovery rate = 75%        │
│  (threshold: >60% ✅ MET)  [All conditions ▼]            │
└─────────────────────────────────────────────────────────┘
```

---

### 2.5 Watchlist Screen

**URL:** `/watchlist`

```
┌──────────────────────────────────────────────────────────────────────┐
│ WATCHLIST                                     [+ Add Ticker]         │
├────────┬────────┬───────┬────────┬───────┬────────┬──────┬──────────┤
│ Ticker │ Price  │ Today │ Score  │ 7D    │ 1Y     │ Rec  │ Thesis   │
├────────┼────────┼───────┼────────┼───────┼────────┼──────┼──────────┤
│ AAPL   │ $225.50│ +1.2% │ 78/100 │ +1.6% │ +22.0% │ 🟢 B │ ✅ Valid │
│ MSFT   │ $430.20│ -0.4% │ 82/100 │ +0.8% │ +18.5% │ 🟢 SB│ ✅ Valid │
│ TSLA   │ $198.30│ -2.1% │ 52/100 │ -1.2% │ +8.0%  │ 🟡 H │ ⚠ Review│
│ NVDA   │ $124.50│ +3.2% │ 75/100 │ +2.4% │ +35.0% │ 🟢 B │ ✅ Valid │
└────────┴────────┴───────┴────────┴───────┴────────┴──────┴──────────┘

⚠ Earnings alerts: AAPL in 8 days | MSFT in 22 days

[Rec key: SB=Strong Buy, B=Buy, H=Hold, HR=High Risk, A=Avoid, SA=Strong Avoid]
```

---

### 2.6 Portfolio Screen

**URL:** `/portfolio`

```
OPEN POSITIONS                                    Total Value: $24,350
                                                  Total P&L: +$2,350 (+10.7%)

┌────────┬──────────┬──────────┬────────┬────────┬────────┬───────────┐
│ Ticker │ Entry $  │ Current  │ Shares │ P&L $  │ P&L %  │ Thesis    │
├────────┼──────────┼──────────┼────────┼────────┼────────┼───────────┤
│ AAPL   │ $195.00  │ $225.50  │ 20     │ +$610  │ +15.6% │ ✅ Valid  │
│ MSFT   │ $380.00  │ $430.20  │ 10     │ +$502  │ +13.2% │ ✅ Valid  │
│ TSLA   │ $220.00  │ $198.30  │ 15     │ -$325  │ -9.9%  │ ⚠ Review │
└────────┴──────────┴──────────┴────────┴────────┴────────┴───────────┘

⚠ TSLA approaching hard stop ($188.00). Current: $198.30. 
  Review thesis: Original reason for entry may no longer be valid.
  [View Full Thesis Check]
```

---

### 2.7 Settings Screen

**URL:** `/settings`

- Default investment amount
- Default risk tolerance
- Notification preferences (earnings alerts, stop-loss alerts, anomaly alerts)
- Data source preferences
- Display preferences (dark/light mode, currency)
- Account / subscription management
- Export reports (PDF)

---

## 3. Mobile Responsive Considerations

- All screens must work on mobile (min width 375px)
- Report sections collapse to accordion on mobile
- Score dashboard uses horizontal scrolling cards instead of full table
- Price chart has pinch-to-zoom
- Investment calculator uses full-width inputs
- Navigation becomes bottom tab bar on mobile: Search | Watchlist | Portfolio | Settings

---

## 4. Error States

| Scenario | User Experience |
|---|---|
| Ticker not found | "Ticker 'XYZ' not found. Searching for companies named 'XYZ'…" + suggestions |
| Data source unavailable | "Price data temporarily unavailable. Using last known price from [timestamp]. Fundamental data current." |
| Analysis fails | "Analysis failed for [reason]. Retry? [Button]" — never show stack trace |
| Stale data | Yellow warning banner: "Fundamental data last updated [N] days ago. Analysis may not reflect latest filings." |
| Market closed | "Market closed. Showing last close price. Real-time analysis will resume at market open." |
| Model not available for ticker | "ML models not yet trained for this ticker. Showing rule-based analysis only. Confidence scores reduced." |

---

## 5. Navigation Map

```
/                               ← Landing / redirect to /dashboard
/dashboard                      ← Main hub
/analyze                        ← Redirect to /dashboard
/analyze?ticker=AAPL            ← Analysis configuration
/analyze/AAPL/loading/{job_id}  ← Loading screen
/report/AAPL/{report_id}        ← Full report
/watchlist                      ← Watchlist management
/portfolio                      ← Portfolio tracking
/portfolio/{ticker}/thesis      ← Thesis validation detail
/market                         ← Market regime + macro overview
/backtesting/{ticker}           ← Backtesting results for ticker
/settings                       ← User settings
/settings/subscription          ← Plan management
```
