# StockSense AI — Multi-Market Machine Learning Guide

## 1. Unified Multi-Market Paradigm
StockSense AI strictly maintains a single, generic machine learning platform where Pakistan (PSX) and international markets (US, UK, Japan, HK, India) are first-class citizens executing through identical pipelines:

```
  PK.PSX.ENGRO (PKR)  ──┐
  US.NASDAQ.AAPL (USD) ──┼──> Feature Engineering ──> Dataset Builder ──> ML Models ──> Prediction
  GB.LSE.AZN (GBP)    ──┘
```

---

## 2. Market-Aware Parameters
While the code execution path is shared, the following contextual parameters adapt per market:
- **Trading Calendars**: PSX Friday Jummah split session vs US Federal holidays.
- **Benchmark Indices**: KSE-100 for PSX, S&P 500 / NASDAQ for US, FTSE 100 for UK, Nikkei 225 for Japan, NIFTY 50 for India.
- **Native Currencies**: Preserved without destructive cross-currency arithmetic.
- **Macro Drivers**: Policy rates and sovereign yield curves mapped to country code.
