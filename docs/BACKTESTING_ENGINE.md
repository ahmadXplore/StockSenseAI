# StockSense AI — Multi-Market Backtesting, Portfolio & Risk Platform

## Overview

The StockSense AI Backtesting Engine is an event-driven, institutional-grade historical simulation platform supporting global equity markets side-by-side:
* **Pakistan (PSX)**
* **United States (NYSE / NASDAQ)**
* **United Kingdom (LSE)**
* **Japan (TSE)**
* **Hong Kong (HKEX)**
* **India (NSE / BSE)**

---

## 1. Core Architecture

```
                               ┌─────────────────────────────┐
                               │  Canonical Market Data      │
                               │  (PostgreSQL market_data)   │
                               └──────────────┬──────────────┘
                                              │
                                              ▼
┌───────────────────────┐      ┌─────────────────────────────┐
│  Point-in-Time Universe│ ───► │  Chronological Event Loop   │
│  (Survivorship Guard) │      │  (Bar-by-Bar Timeline)      │
└───────────────────────┘      └──────────────┬──────────────┘
                                              │
                       ┌──────────────────────┴──────────────────────┐
                       │                                             │
                       ▼                                             ▼
         ┌───────────────────────────┐                 ┌───────────────────────────┐
         │  ML Strategy Engine       │                 │  Position Risk & Exits    │
         │  - AI Predictions (prob)  │                 │  - Dynamic ATR Stops      │
         │  - Momentum / MA Cross    │                 │  - Trailing Exits         │
         │  - MACD Trend Following   │                 │  - Take Profit Stages     │
         │  - RSI Mean Reversion     │                 │  - Thesis Invalidation    │
         │  - Fundamental Quality    │                 │  - Prediction Reversal    │
         │  - Volatility Breakout    │                 └─────────────┬─────────────┘
         │  - Multi-Factor Ensemble  │                               │
         └─────────────┬─────────────┘                               │
                       │                                             │
                       ▼                                             ▼
         ┌───────────────────────────┐                 ┌───────────────────────────┐
         │  Pre-Trade Risk Limits    │ ──────────────► │  Execution & Settlement   │
         │  - Max Position / Sector  │                 │  - NEXT_OPEN Semantics    │
         │  - Max Portfolio Risk     │                 │  - Market Slippage & BPS  │
         │  - Max Drawdown Breaker   │                 │  - Broker Commissions     │
         └───────────────────────────┘                 │  - Statutory Taxes (CVT)  │
                                                       └─────────────┬─────────────┘
                                                                     │
                                                                     ▼
                                                       ┌───────────────────────────┐
                                                       │  Multi-Currency Portfolio │
                                                       │  - Double-Entry Ledger    │
                                                       │  - Splits & Dividends     │
                                                       │  - Daily Cash Interest    │
                                                       └─────────────┬─────────────┘
                                                                     │
                                                                     ▼
                                                       ┌───────────────────────────┐
                                                       │  Evaluation & Attribution │
                                                       │  - CAGR, Sharpe, Sortino  │
                                                       │  - VaR (95/99), CVaR      │
                                                       │  - Brinson Attribution    │
                                                       │  - Historical Stress GFC  │
                                                       │  - Monte Carlo Bootstrap  │
                                                       │  - Portfolio Optimization │
                                                       └───────────────────────────┘
```

---

## 2. Zero Look-Ahead Bias Guarantees

1. **NEXT_OPEN Execution Standard**: Signals generated at bar $T$ evaluate price, features, and ML predictions available up to bar $T$. The resulting order executes at the `Open` price of bar $T+1$.
2. **Timestamp Verification Guard**: All features and prediction inputs are asserted via `assert_no_lookahead_leakage()` before entering the strategy signal generator.
3. **Point-in-Time Universe Resolution**: Historical stock universes only include securities actively listed as of date $t$ (`IPO date <= t` and `delisting date >= t`), eliminating survivorship bias.

---

## 3. Market Friction & Statutory Taxes

| Market Code | Exchange | Default Commission | Default Slippage | Statutory Taxes & Fees | Default Benchmark |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **PK** | PSX | 0.15% | 10.0 bps | SECP turnover levy, CDC fee, NCCPL fee, CVT | `KSE100` |
| **US** | NASDAQ / NYSE | $0.005/share or 0.10% | 3.0 bps | SEC Section 31 Fee ($27.80/million on sells), FINRA TAF | `SPY` |
| **UK** | LSE | 0.10% (min £5.00) | 5.0 bps | Stamp Duty Reserve Tax (0.5% on buys) | `FTSE100` |
| **JP** | TSE | 0.15% | 6.0 bps | Exchange fee (0.002%) | `N225` |
| **IN** | NSE / BSE | 0.05% (max ₹20) | 8.0 bps | Securities Transaction Tax (STT 0.1%), GST | `NIFTY50` |
| **HK** | HKEX | 0.15% | 7.0 bps | SFC transaction levy, Stamp Duty | `HSI` |

---

## 4. Supported Strategy Archetypes

1. **AI Prediction Strategy (`AI_PREDICTION`)**:
   Trades on point-in-time machine learning predictions. Enters when $P(\text{up}) \ge \text{threshold}$ (default 0.60) and expected return is positive, with market regime filtering.
2. **Moving Average Momentum (`MOMENTUM`)**:
   Fast EMA / SMA crossover (e.g. 20/50) combined with 20-day return velocity filter.
3. **Trend Following (`TREND_FOLLOWING`)**:
   MACD histogram expansion aligned with long-term 200-day trend direction.
4. **Mean Reversion (`MEAN_REVERSION`)**:
   RSI oversold (< 30) bounces off lower Bollinger Bands with dynamic ATR profit targets.
5. **Fundamental Factor Strategy (`FUNDAMENTAL`)**:
   Quality + Value screen selecting low P/E, high ROE ($\ge 12\%$), low Debt-to-Equity, and high Piotroski F-Scores.
6. **Volatility Breakout (`VOLATILITY_BREAKOUT`)**:
   20-day Donchian channel breakouts with adaptive ATR trailing stops.
7. **Multi-Factor Ensemble (`ENSEMBLE`)**:
   Weighted consensus across AI predictions (50%), Momentum (30%), and Fundamentals (20%).

---

## 5. Quantitative Portfolio Optimization

* **Maximum Sharpe Ratio**: Quadratic optimization (SLSQP) maximizing $(R_p - R_f) / \sigma_p$.
* **Equal Risk Contribution (Risk Parity)**: Equalizes marginal risk contribution across all assets ($w_i \cdot (\Sigma w)_i / \sigma_p = \sigma_p / N$).
* **Global Minimum Variance**: Minimizes total portfolio variance $w^T \Sigma w$ subject to constraints.
* **Constraints**: Hard individual position caps ($\le 40\%$), long-only non-negativity bounds, sector limits, and full capital allocation ($\sum w_i = 1.0$).

---

## 6. Stress Testing & Monte Carlo

* **Historical Crisis Scenarios**:
  - 2008 Global Financial Crisis (Lehman Brothers shock)
  - 2020 COVID-19 Liquidity Shock
  - 2022 Global Monetary Tightening & Rate Shock
* **Monte Carlo Forward Simulation**:
  - Bootstrapped resampled daily return trajectories (500 to 5,000 iterations).
  - Calculates percentile wealth distributions ($P_5, P_{25}, P_{50}, P_{75}, P_{95}$), worst-case drawdowns, probability of profit, and probability of ruin.

---

## 7. API Endpoints Reference

```http
POST /api/v1/backtesting/run
GET  /api/v1/backtesting/runs
GET  /api/v1/backtesting/runs/{run_id}
POST /api/v1/backtesting/optimize
POST /api/v1/backtesting/stress
POST /api/v1/backtesting/monte-carlo
GET  /api/v1/backtesting/strategies
GET  /api/v1/backtesting/config/template?market=US&strategy=AI_PREDICTION
```
