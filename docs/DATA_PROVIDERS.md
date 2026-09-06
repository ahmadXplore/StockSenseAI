# StockSense AI — Data Providers & Abstraction Layer

## 1. Provider Abstraction Contract

The generic `MarketDataProvider` abstract base class defines the capability contract for all data providers:

```python
class MarketDataProvider(ABC):
    name: str
    capabilities: ProviderCapabilities
    supported_markets: List[str]
    supported_exchanges: List[str]

    async def get_market_metadata(self, market_code: str) -> Optional[MarketDTO]
    async def get_exchange_metadata(self, exchange_code: str) -> Optional[ExchangeDTO]
    async def get_security_list(self, market_code: str, exchange_code: str) -> List[SecurityDTO]
    async def search_securities(self, query: str, market_code: Optional[str], exchange_code: Optional[str]) -> List[SecurityDTO]
    async def get_security_metadata(self, symbol: str, market_code: str, exchange_code: str) -> Optional[SecurityDTO]
    async def get_historical_prices(self, symbol: str, market_code: str, exchange_code: str, start_date: Optional[date], end_date: Optional[date]) -> List[CanonicalPriceDTO]
    async def get_latest_prices(self, symbols: List[str], market_code: str, exchange_code: str) -> Dict[str, CanonicalPriceDTO]
    async def get_corporate_actions(self, symbol: str, market_code: str, exchange_code: str, start_date: Optional[date], end_date: Optional[date]) -> List[CorporateActionDTO]
    async def get_provider_health(self) -> ProviderHealth
```

---

## 2. Provider Implementations

### A. Pakistan Stock Exchange Provider (`psx_data_provider`)
- **Primary Source**: Validated Kaggle Pakistan Stock Market Historical Dataset 2017–2025 (`compiled_psx_historical_2017_2025.csv`).
- **Coverage**: 840,330 rows, 1,142 unique symbols across 2,183 trading days (2017-01-02 to 2025-10-24).
- **Capabilities**:
  - `historical_prices`: True
  - `corporate_actions`: True
  - `delisted_securities`: True
  - `intraday_prices`: False
  - `fundamentals`: False (integrated via SECP / scraping)
- **Delisted Securities**: Tracks 577 inactive/delisted symbols based on cessation of trading.

### B. International Market Data Provider (`international_data_provider`)
- **Primary Source**: Open-source `yfinance` multi-market daily OHLCV and corporate actions.
- **Secondary Fallback 1**: `Alpha Vantage` (free API key tier).
- **Secondary Fallback 2**: `Stooq` public CSV feeds.
- **Capabilities**:
  - `historical_prices`: True
  - `intraday_prices`: True
  - `corporate_actions`: True
  - `delisted_securities`: False
  - `fundamentals`: True
  - `news`: True
  - `realtime_quotes`: True
- **Supported Exchanges**: NASDAQ, NYSE, LSE, TSE, HKEX, NSE, BSE.

---

## 3. Provider Failover & Fallback Engine

When requesting historical data, `ProviderRegistry` executes the following fault-tolerant cascade:

```
Request(Symbol="AAPL", Market="US")
               │
               ▼
┌──────────────────────────────┐
│  Primary: yfinance (Direct)  │ ──► [Success] ──► Return Canonical Price List
└──────────────────────────────┘
               │ (Fails / Rate-limited)
               ▼
┌──────────────────────────────┐
│ Secondary: Alpha Vantage API │ ──► [Success] ──► Return Canonical Price List
└──────────────────────────────┘
               │ (Fails / Empty)
               ▼
┌──────────────────────────────┐
│ Tertiary: Stooq CSV Stream   │ ──► [Success] ──► Return Canonical Price List
└──────────────────────────────┘
```
