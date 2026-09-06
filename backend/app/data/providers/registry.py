"""
StockSense AI — Provider Registry & Fallback Orchestration Engine
Routes market data requests to appropriate market providers with transparent fallback.
"""

from __future__ import annotations
from typing import Dict, List, Optional
from datetime import date
from decimal import Decimal

from app.data.canonical.market import MarketDTO, ExchangeDTO, parse_security_id
from app.data.canonical.security import SecurityDTO
from app.data.canonical.price import CanonicalPriceDTO
from app.data.canonical.corporate_action import CorporateActionDTO
from app.data.providers.base import MarketDataProvider, ProviderHealth
from app.data.providers.psx.provider import PSXMarketDataProvider
from app.data.providers.international.provider import InternationalMarketDataProvider


class ProviderRegistry:
    """
    Central provider registry managing multi-market routing and primary/secondary failover.
    """

    def __init__(self):
        self._providers: Dict[str, MarketDataProvider] = {}
        self._market_routing: Dict[str, List[str]] = {} # Market -> List[Provider Name]

        # Register default implementations
        self.register_provider(PSXMarketDataProvider())
        self.register_provider(InternationalMarketDataProvider())

    def register_provider(self, provider: MarketDataProvider):
        """Registers a data provider and updates market routing tables."""
        self._providers[provider.name] = provider
        for market in provider.supported_markets:
            if market not in self._market_routing:
                self._market_routing[market] = []
            if provider.name not in self._market_routing[market]:
                self._market_routing[market].append(provider.name)

    def get_providers_for_market(self, market_code: str) -> List[MarketDataProvider]:
        """Returns ordered list of providers for a market (primary, secondary)."""
        names = self._market_routing.get(market_code.upper(), [])
        return [self._providers[n] for n in names if n in self._providers]

    async def get_historical_prices(
        self,
        symbol: str,
        market_code: str,
        exchange_code: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> List[CanonicalPriceDTO]:
        """
        Attempts primary provider first; cascades to secondary on empty or failure.
        """
        providers = self.get_providers_for_market(market_code)
        if not providers:
            # Fallback to international provider if not mapped
            providers = [self._providers.get("international_data_provider")]

        for p in providers:
            if p is None:
                continue
            try:
                prices = await p.get_historical_prices(
                    symbol=symbol,
                    market_code=market_code,
                    exchange_code=exchange_code,
                    start_date=start_date,
                    end_date=end_date,
                )
                if prices:
                    return prices
            except Exception:
                continue

        return []

    async def get_historical_ohlcv(
        self,
        security_id: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> List[CanonicalPriceDTO]:
        """
        Retrieves historical OHLCV data using canonical security ID (e.g. PK.PSX.ENGRO, US.NASDAQ.AAPL).
        """
        market_code, exchange_code, symbol = parse_security_id(security_id)
        return await self.get_historical_prices(
            symbol=symbol,
            market_code=market_code,
            exchange_code=exchange_code,
            start_date=start_date,
            end_date=end_date,
        )

    async def search_all_markets(self, query: str) -> List[SecurityDTO]:
        """Searches across all registered providers simultaneously."""
        results: List[SecurityDTO] = []
        for provider in self._providers.values():
            try:
                res = await provider.search_securities(query=query)
                results.extend(res)
            except Exception:
                continue
        return results

    async def get_all_provider_health(self) -> List[ProviderHealth]:
        """Returns health summaries for all registered providers."""
        healths = []
        for provider in self._providers.values():
            healths.append(await provider.get_provider_health())
        return healths


# Global singleton registry instance
provider_registry = ProviderRegistry()
