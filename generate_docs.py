import os

DOCS_DIR = r"c:\Users\User\Desktop\Ahmad\Stock-Price_Predictor\docs"

docs = {
    "FRONTEND_ARCHITECTURE.md": """# Frontend Architecture
StockSense AI uses a modern Next.js App Router frontend built with React, TypeScript, and Tailwind CSS.
It is designed as a manual financial analysis platform. No autonomous agent acts on behalf of the user.

## Core Stack
- **Framework:** Next.js 14 (App Router)
- **Styling:** Tailwind CSS + Lucide React for iconography
- **State Management:** React Context (MarketContext) & LocalStorage (for portfolios/watchlists)
- **Data Fetching:** Fetch API with centralized client (`lib/api.ts`)
- **Charting:** Recharts

## Structure
- `app/` - Next.js routes (Dashboard, Markets, Stocks, Portfolio, Backtesting, Chatbot)
- `components/` - Reusable UI components for forms, charts, tables, and navigation
- `lib/` - Formatting, Market utilities, API definitions
""",
    "USER_WORKFLOW.md": """# User Workflow
StockSense AI provides a structured, user-driven workflow:

1. **Market Selection:** User navigates to `/markets` and selects a target exchange (e.g., PSX, NASDAQ).
2. **Security Exploration:** User clicks on a specific security (e.g., ENGRO, AAPL).
3. **Analysis:** The stock detail page `/stocks/[securityId]` presents interactive charts, technical analysis, fundamental ratios, and AI predictions.
4. **Portfolio Actions:** User can add the security to their portfolio or watchlist.
5. **Backtesting:** User navigates to `/backtesting` to simulate strategies over historical data.
6. **Risk Management:** User monitors Value at Risk (VaR) and performs stress tests in `/portfolio/risk`.
7. **Query Assistant:** The user can ask the floating StockSense AI chatbot to explain metrics or terminology at any time.

*The user remains in full control at every step. There is no autonomous trading.*
""",
    "DASHBOARD.md": """# Main Dashboard
The Main Dashboard (`/dashboard`) is the central hub for the user's selected market.

## Features
- **Market Status:** Current active market, exchange, timezone, and currency.
- **Data Freshness:** Indicates when historical and live data was last synced.
- **Major Movers:** Displays top active securities and major indices for the selected market.
- **Cross-Market Compatibility:** Instantly adapts when switching between Pakistan (PSX) and US/International markets.
""",
    "STOCK_ANALYSIS.md": """# Stock Analysis UI
The Universal Stock Detail Page (`/stocks/[securityId]`) is the core analytical view for any supported security.

## Tabs
1. **Interactive Chart:** Price history, volume, and technical overlays.
2. **AI Prediction:** ML-driven 7-day direction predictions with conformal prediction intervals and explainability bars.
3. **Fundamentals:** Multi-market ratios, profitability, valuation multiples, and Piotroski score.
4. **Technicals:** Multi-timeframe oscillators (RSI, MACD, ATR, Bollinger Bands).
5. **Backtest:** Instantly execute point-in-time historical backtests.
6. **News:** Recent company filings and market news.
""",
    "BACKTESTING_UI.md": """# Backtesting Studio
The Backtesting Studio (`/backtesting`) provides event-driven quantitative simulations.

## Features
- **Configuration Form:** Configure market, start/end dates, initial capital, and strategy (AI Prediction, Momentum, Mean Reversion).
- **Performance Metrics:** CAGR, Sharpe Ratio, Sortino Ratio, Max Drawdown, Win Rate.
- **Visualizations:** Equity Curve vs Benchmark, Monthly Compounded Returns Heatmap.
- **Trade Log:** Detailed tabular view of all executed trades, slippage, and fees.
- **Run History:** Persisted records of all past backtests.
""",
    "PORTFOLIO_UI.md": """# Portfolio Management UI
The Portfolio Dashboard (`/portfolio`) provides manual tracking and multi-currency ledger capabilities.

## Features
- **Holdings Table:** Tracks shares, entry price, current price, native value, and unrealized P&L.
- **Consolidated Base Value:** Converts multi-currency holdings into a single base currency (e.g., USD).
- **Record Position:** Manual entry form for adding new holdings with investment theses.
- **Optimization Workspace:** (`/portfolio/optimize`) - Provides Markowitz Mean-Variance and Risk Parity suggestions. Does not automatically execute trades.
""",
    "RISK_UI.md": """# Risk Engine UI
The Portfolio Risk Dashboard (`/portfolio/risk`) provides quantitative risk and tail analytics.

## Tabs
1. **Risk Metrics & Limits:** Daily VaR (95%), Expected Shortfall (CVaR), Beta, Volatility, and pre-trade constraint gates.
2. **Historical Stress Tests:** Simulates portfolio impact during real crises (e.g., 2008 Lehman Shock, 2020 COVID Crash).
3. **Monte Carlo Simulation:** Bootstrapped forward simulations (500 iterations) projecting 252-day terminal wealth and drawdown probabilities.
""",
    "CHATBOT.md": """# Query Chatbot
The StockSense AI Chatbot (`/api/chat`) is a specialized financial assistant integrated into the global UI.

## Capabilities
- Explains financial terminology (e.g., "What is RSI?").
- Interprets dashboard metrics and AI predictions based on the current context.
- Maintains strict guardrails: It is an informational assistant, not an autonomous agent.
- Automatically appends financial disclaimers to predictions.
""",
    "FRONTEND_API_INTEGRATION.md": """# Frontend API Integration
The frontend communicates with the FastAPI backend strictly through centralized functions in `lib/api.ts`.

## Structure
- All endpoints are nested under `/api/v1/`.
- **Data Fetching:** Standard `fetch` with error handling and fallback dummy data where applicable for UI demonstration.
- **Type Safety:** Comprehensive TypeScript interfaces (`LiveQuote`, `FundamentalsData`, `MLPrediction`, `BacktestResponse`) map exactly to backend Pydantic DTOs.
- **CORS:** Controlled by backend `CORS_ORIGINS`.
"""
}

os.makedirs(DOCS_DIR, exist_ok=True)
for filename, content in docs.items():
    path = os.path.join(DOCS_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

# Update PROJECT_STATUS.md
status_content = """# StockSense AI — Project Implementation Status

**Last Updated:** Prompt 9 (Frontend Integration & Final Verification) Completed  
**Current Milestone:** Complete StockSense AI Manual Financial Platform

---

## 1. Status Overview

| Component / Milestone | Description | Status |
| :--- | :--- | :--- |
| **Phase 1 Foundation** | Core Scaffolding, DB Models (8 Schemas), Docker Compose, FastAPI & Next.js 14 | **COMPLETED** |
| **Prompt 3 Multi-Market Platform** | Generic Market/Exchange Layer, PSX & US Providers, ETL, Trading Calendars, Quality Engine | **COMPLETED** |
| **Phase 3/4/5 Machine Learning & Backend** | Direction Classifier, AI Explainability, Reporting, Risk Engines | **COMPLETED** |
| **Prompt 8/9 Frontend Integration** | Full Next.js Dashboard, Chatbot, Portfolios, Backtesting, Risk | **COMPLETED** |

---

## 2. Completed in Prompt 9 (End-to-End Integration)

- [x] **Global Market Selector**: Market -> Exchange -> Security flow implemented across UI.
- [x] **Main Dashboard**: Cross-market data and freshness indicators.
- [x] **Universal Stock Detail Page**: Interactive charts, Technicals, Fundamentals, AI Predictions, and Explainability tabs.
- [x] **Backtesting Studio**: Event-driven simulations, heatmaps, equity curves, and history logs.
- [x] **Portfolio Management**: Manual record keeping, native-currency tracking, and Markowitz Optimization UI.
- [x] **Risk Dashboard**: VaR, CVaR, Monte Carlo simulations, and historical stress tests.
- [x] **Query Chatbot**: Strictly informational, non-agentic AI assistant securely proxying requests.
- [x] **Type Safety**: Fully typed interfaces mapping to backend endpoints (`tsc --noEmit` verified).
- [x] **Documentation**: Full suite of architectural and UI documentation added.

---

## 3. Critical Architecture Rule
**StockSense AI is a manual financial analysis platform.**
No autonomous trading, decision-making, or portfolio execution agents are implemented. The user is entirely in control.
"""

status_path = r"c:\Users\User\Desktop\Ahmad\Stock-Price_Predictor\PROJECT_STATUS.md"
with open(status_path, "w", encoding="utf-8") as f:
    f.write(status_content)

print("Documentation generated successfully.")
