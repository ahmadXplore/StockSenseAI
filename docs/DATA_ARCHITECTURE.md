# StockSense AI — Canonical Multi-Market Data Architecture

## 1. Architectural Overview

StockSense AI is built from the ground up as a **market-independent, multi-market financial data platform**. Downstream layers (Machine Learning, Feature Engineering, Technical Indicators, Portfolio Management, Backtesting) **never** interface directly with third-party APIs, vendor raw formats, Kaggle files, or CSVs. All data flows through an 8-stage canonical pipeline.

```
                         StockSense AI
                               |
                   Canonical Market Data Layer
                               |
         +---------------------+---------------------+
         |                                           |
   Pakistan (PK)                            International
         |                                           |
        PSX                               US / GB / JP / HK / IN
         |                                           |
         +---------------------+---------------------+
                               |
                        Provider Layer
                               |
              +----------------+----------------+
              |                                 |
      Historical Providers             Live / Realtime Providers
              |                                 |
              +----------------+----------------+
                               |
                   Raw Data Staging Layer
                               |
                     Normalization Engine
                               |
                   Data Quality & Validation
                               |
                     Canonical Data Model
                               |
                     PostgreSQL Authoritative
                               |
          +--------------------+--------------------+
          |                    |                    |
     ML & Features        Backtesting          Portfolios
```

---

## 2. Global Security Master & Identity

Securities are globally unique across all supported markets and exchanges. A symbol is never used as the sole primary key because ticker symbols collide across exchanges (e.g. `ABC` on PSX vs `ABC` on NASDAQ vs `ABC` on LSE).

### Canonical Security Identifier Format:
$$\text{security\_id} = \langle\text{MARKET\_CODE}\rangle.\langle\text{EXCHANGE\_CODE}\rangle.\langle\text{SYMBOL}\rangle$$

Examples:
- `PK.PSX.ENGRO` (Engro Corporation on Pakistan Stock Exchange in PKR)
- `US.NASDAQ.AAPL` (Apple Inc. on NASDAQ in USD)
- `US.NYSE.BRK_A` (Berkshire Hathaway Inc. on NYSE in USD)
- `GB.LSE.AZN` (AstraZeneca PLC on London Stock Exchange in GBP)
- `JP.TSE.7203` (Toyota Motor Corporation on Tokyo Stock Exchange in JPY)

### Symbol History & Alias Tracking
Securities track symbol mutations (e.g., $ABC \to XYZ$) via `SymbolHistory` to preserve the underlying corporate identity throughout corporate reorganizations.

---

## 3. Canonical OHLCV Model

All price records across every market conform to the identical `CanonicalPriceDTO` schema:

| Column | Type | Description |
| :--- | :--- | :--- |
| `security_id` | `VARCHAR(60)` | Globally unique master identifier |
| `ticker` | `VARCHAR(20)` | Exchange-local ticker symbol |
| `time` | `TIMESTAMPTZ` | Timestamp of the bar / trading session |
| `open` | `NUMERIC(12, 4)` | Opening price in native currency |
| `high` | `NUMERIC(12, 4)` | Highest price in native currency |
| `low` | `NUMERIC(12, 4)` | Lowest price in native currency |
| `close` | `NUMERIC(12, 4)` | Raw closing price in native currency |
| `adj_close` | `NUMERIC(12, 4)` | Split and dividend-adjusted closing price |
| `volume` | `BIGINT` | Total shares / units traded during session |
| `vwap` | `NUMERIC(12, 4)` | Volume-weighted average price (nullable) |
| `currency` | `VARCHAR(10)` | Native currency code (`PKR`, `USD`, `GBP`, etc.) |
| `split_factor` | `NUMERIC(10, 6)` | Cumulative split adjustment factor |
| `dividend_amount`| `NUMERIC(10, 6)` | Cash dividend on action date |
| `source_id` | `VARCHAR(100)` | Unique upstream source record identifier |
| `data_source` | `VARCHAR(50)` | Originating provider name |
| `is_adjusted` | `BOOLEAN` | Whether record reflects corporate action adjustment |
| `quality_flag` | `VARCHAR(20)` | `ok`, `suspect`, `gap`, `zero_volume`, `flagged_move` |

### Geometric Constraints:
$$\text{high} \ge \max(\text{open}, \text{close}, \text{low})$$
$$\text{low} \le \min(\text{open}, \text{close}, \text{high})$$
$$\text{volume} \ge 0,\quad \text{prices} \ge 0$$

---

## 4. Multi-Currency Support

Native price series are **never** destructively transformed to a different currency in database storage. The independent `CurrencyService` converts monetary amounts dynamically when aggregating cross-market portfolios or running multi-currency benchmarks.
