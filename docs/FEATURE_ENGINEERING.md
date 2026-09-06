# StockSense AI — Feature Engineering Architecture

## 1. Overview
The StockSense AI Feature Engineering Suite provides a market-independent, point-in-time compliant feature extraction pipeline. It computes over 40 distinct features spanning Technical Analysis, Price Structure, Fundamentals, Market Relatives, Macroeconomics, and News Sentiment for any supported global security (e.g. `PK.PSX.ENGRO`, `US.NASDAQ.AAPL`).

---

## 2. Feature Categories & Mathematical Formulations

### 2.1 Technical Indicators
- **Trend Indicators**:
  - $SMA_n = \frac{1}{n} \sum_{i=0}^{n-1} P_{t-i}$ ($n \in \{20, 50, 200\}$)
  - $EMA_n = P_t \cdot \alpha + EMA_{t-1} \cdot (1 - \alpha)$, where $\alpha = \frac{2}{n + 1}$ ($n \in \{12, 26\}$)
  - $MACD = EMA_{12} - EMA_{26}$, $Signal = EMA_9(MACD)$, $Hist = MACD - Signal$
  - $ADX_{14}$: Trend strength index based on directional movement and smoothed True Range.
  - $Aroon_{25}$: Time since 25-period high/low measuring trend emergence.

- **Momentum Indicators**:
  - $RSI_{14} = 100 - \frac{100}{1 + RS}$, where $RS = \frac{\text{EMA}(\text{Gain}, 14)}{\text{EMA}(\text{Loss}, 14)}$
  - $Stochastic\ \%K = \frac{Close - Low_{14}}{High_{14} - Low_{14}} \times 100$, $\%D = SMA_3(\%K)$
  - $Williams\ \%R = \frac{High_{14} - Close}{High_{14} - Low_{14}} \times -100$
  - $ROC_n = \frac{Close_t - Close_{t-n}}{Close_{t-n}} \times 100$ ($n \in \{10, 21\}$)
  - $MFI_{14}$: Volume-weighted momentum oscillator.

- **Volatility Indicators**:
  - $ATR_{14} = \text{RollingMean}(TR, 14)$, $TR = \max(H-L, |H-C_{t-1}|, |L-C_{t-1}|)$
  - Realized Volatility: $\sigma_{20D} \times \sqrt{252} \times 100$
  - Parkinson Volatility: $\sqrt{\frac{1}{4 \ln 2 \cdot N} \sum_{i=1}^N \left(\ln \frac{H_i}{L_i}\right)^2} \times \sqrt{252} \times 100$
  - Garman-Klass Volatility: OHLC-based variance estimator.

- **Volume Structure**:
  - Volume SMA (20, 50)
  - Relative Volume ($RVOL_{20D} = \frac{Volume_t}{SMA_{20}(Volume)}$)
  - On-Balance Volume ($OBV_t = OBV_{t-1} + \text{sign}(\Delta Close) \times Volume_t$)

---

### 2.2 Point-in-Time Fundamentals
- **Growth**: YoY Revenue Growth, YoY Net Income Growth, EPS Growth.
- **Profitability**: Return on Equity (ROE), Return on Assets (ROA), Gross Margin, Operating Margin, Net Margin.
- **Leverage & Solvency**: Debt-to-Equity, Current Ratio, Quick Ratio, Interest Coverage.
- **Valuation**: Trailing P/E, Forward P/E, P/B, EV/EBITDA, EV/Sales, Dividend Yield.
- **Filing Date Guard**: Statements are visible strictly when `filing_date <= as_of_date` or `period_end + 25 days <= as_of_date`.

---

### 2.3 Market Relatives & Macro
- **Beta ($\beta_{60D}$)**: $\frac{\text{Cov}(R_{stock}, R_{bench})}{\text{Var}(R_{bench})}$ against designated benchmark (e.g. KSE-100 for PK, SPY for US).
- **Excess Return**: $R_{stock, 21D} - R_{bench, 21D}$.
- **Macro Indicators**: 10Y-2Y yield curve slope, VIX level, central bank policy rate, high-volatility regime state.
- **News Sentiment**: Point-in-time rolling 7D/30D sentiment polarity and sentiment momentum ($Score_{7D} - Score_{30D}$).

---

## 3. Versioning & Reproducibility
Every generated feature set includes:
- `feature_version` (e.g. `1.0.0`)
- `config_hash`: Deterministic SHA-256 fingerprint generated from sorted feature names and extractor parameters.
