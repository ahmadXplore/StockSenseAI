"""
StockSense AI — Provider Fallback & Registry Tests
Tests provider registration, market routing, and fallback behavior.
"""

import pytest
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Optional, List, Dict

from app.data.canonical.market import MarketDTO, ExchangeDTO
from app.data.canonical.security import SecurityDTO, SecurityStatus, SecurityType
from app.data.canonical.price import CanonicalPriceDTO
from app.data.providers.base import MarketDataProvider, ProviderCapabilities, ProviderHealth, ProviderStatus
from app.data.providers.registry import ProviderRegistry


class FailingMockProvider(MarketDataProvider):
    def __init__(self, name="failing_provider"):
        super().__init__(
            name=name,
            capabilities=ProviderCapabilities(),
            supported_markets=["US"],
            supported_exchanges=["NASDAQ"]
        )

    async def get_market_metadata(self, market_code): return None
    async def get_exchange_metadata(self, exchange_code): return None
    async def get_security_list(self, market_code, exchange_code): return []
    async def search_securities(self, query, market_code=None, exchange_code=None): return []
    async def get_security_metadata(self, symbol, market_code, exchange_code): return None
    async def get_historical_prices(self, symbol, market_code, exchange_code, start_date=None, end_date=None):
        raise ConnectionError("Primary provider connection timeout")
    async def get_latest_prices(self, symbols, market_code, exchange_code): return {}


class WorkingBackupProvider(MarketDataProvider):
    def __init__(self, name="working_backup_provider"):
        super().__init__(
            name=name,
            capabilities=ProviderCapabilities(),
            supported_markets=["US"],
            supported_exchanges=["NASDAQ"]
        )

    async def get_market_metadata(self, market_code): return None
    async def get_exchange_metadata(self, exchange_code): return None
    async def get_security_list(self, market_code, exchange_code): return []
    async def search_securities(self, query, market_code=None, exchange_code=None): return []
    async def get_security_metadata(self, symbol, market_code, exchange_code): return None
    async def get_historical_prices(self, symbol, market_code, exchange_code, start_date=None, end_date=None):
        return [
            CanonicalPriceDTO(
                security_id=f"US.NASDAQ.{symbol}",
                ticker=symbol,
                timestamp=datetime(2024, 1, 15, tzinfo=timezone.utc),
                open=Decimal("150.0"),
                high=Decimal("155.0"),
                low=Decimal("149.0"),
                close=Decimal("153.0"),
                adj_close=Decimal("153.0"),
                volume=1000000,
                currency="USD",
                data_source="backup_provider"
            )
        ]
    async def get_latest_prices(self, symbols, market_code, exchange_code): return {}


@pytest.mark.asyncio
async def test_provider_fallback_execution():
    registry = ProviderRegistry()
    registry._providers.clear()
    registry._market_routing.clear()

    primary = FailingMockProvider()
    secondary = WorkingBackupProvider()

    registry.register_provider(primary)
    registry.register_provider(secondary)

    # When primary fails, fallback to secondary should automatically succeed
    prices = await registry.get_historical_prices(
        symbol="AAPL",
        market_code="US",
        exchange_code="NASDAQ"
    )

    assert len(prices) == 1
    assert prices[0].data_source == "backup_provider"
    assert prices[0].close == Decimal("153.0")
