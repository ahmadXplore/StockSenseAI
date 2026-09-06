"""
StockSense AI — Generic Market Data Provider Abstraction
Defines interface, capability declarations, and health monitoring contracts.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from enum import Enum
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from typing import Optional, List, Dict, Any

from app.data.canonical.market import MarketDTO, ExchangeDTO
from app.data.canonical.security import SecurityDTO
from app.data.canonical.price import CanonicalPriceDTO
from app.data.canonical.corporate_action import CorporateActionDTO


class ProviderStatus(str, Enum):
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    DOWN = "DOWN"
    RATE_LIMITED = "RATE_LIMITED"


@dataclass
class ProviderCapabilities:
    """Capability declaration flags for a MarketDataProvider."""
    historical_prices: bool = True
    intraday_prices: bool = False
    corporate_actions: bool = False
    delisted_securities: bool = False
    fundamentals: bool = False
    news: bool = False
    realtime_quotes: bool = False
    search: bool = True


@dataclass
class ProviderHealth:
    provider_name: str
    status: ProviderStatus
    latency_ms: float
    last_checked: datetime
    error_count: int = 0
    rate_limit_remaining: Optional[int] = None
    message: Optional[str] = None


class MarketDataProvider(ABC):
    """
    Abstract interface for all market data providers (PSX, US, International).
    No downstream application layer should ever call external APIs directly.
    """

    def __init__(
        self,
        name: str,
        capabilities: ProviderCapabilities,
        supported_markets: List[str],
        supported_exchanges: List[str],
    ):
        self.name = name
        self.capabilities = capabilities
        self.supported_markets = [m.upper() for m in supported_markets]
        self.supported_exchanges = [e.upper() for e in supported_exchanges]
        self._error_count = 0
        self._last_checked = datetime.now(timezone.utc)
        self._status = ProviderStatus.HEALTHY

    @abstractmethod
    async def get_market_metadata(self, market_code: str) -> Optional[MarketDTO]:
        """Fetches market metadata if supported."""
        pass

    @abstractmethod
    async def get_exchange_metadata(self, exchange_code: str) -> Optional[ExchangeDTO]:
        """Fetches exchange metadata if supported."""
        pass

    @abstractmethod
    async def get_security_list(
        self, market_code: str, exchange_code: str
    ) -> List[SecurityDTO]:
        """Returns security master list for the specified exchange."""
        pass

    @abstractmethod
    async def search_securities(
        self, query: str, market_code: Optional[str] = None, exchange_code: Optional[str] = None
    ) -> List[SecurityDTO]:
        """Searches securities across supported markets/exchanges."""
        pass

    @abstractmethod
    async def get_security_metadata(
        self, symbol: str, market_code: str, exchange_code: str
    ) -> Optional[SecurityDTO]:
        """Retrieves point-in-time metadata for a specific security."""
        pass

    @abstractmethod
    async def get_historical_prices(
        self,
        symbol: str,
        market_code: str,
        exchange_code: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> List[CanonicalPriceDTO]:
        """Retrieves raw or provider historical prices, normalized to CanonicalPriceDTO."""
        pass

    @abstractmethod
    async def get_latest_prices(
        self, symbols: List[str], market_code: str, exchange_code: str
    ) -> Dict[str, CanonicalPriceDTO]:
        """Retrieves latest quote / daily candle for a batch of symbols."""
        pass

    async def get_corporate_actions(
        self,
        symbol: str,
        market_code: str,
        exchange_code: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> List[CorporateActionDTO]:
        """Retrieves corporate actions (splits, dividends) if supported by provider."""
        return []

    async def get_data_availability(
        self, symbol: str, market_code: str, exchange_code: str
    ) -> Dict[str, Any]:
        """Returns earliest and latest available dates for the security."""
        return {
            "symbol": symbol,
            "market": market_code,
            "exchange": exchange_code,
            "provider": self.name,
            "available": True,
        }

    async def get_provider_health(self) -> ProviderHealth:
        """Returns current operational health of the provider."""
        return ProviderHealth(
            provider_name=self.name,
            status=self._status,
            latency_ms=0.0,
            last_checked=datetime.now(timezone.utc),
            error_count=self._error_count,
        )
