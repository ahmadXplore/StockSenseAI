"""
StockSense AI — Canonical Market & Exchange Entities & DTOs
Defines global markets, exchanges, MIC codes, timezones, and currencies.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List


@dataclass
class MarketDTO:
    id: str                         # 'PK', 'US', 'GB', 'JP', 'HK', 'IN'
    code: str                       # 'PK', 'US', 'GB', 'JP', 'HK', 'IN'
    name: str                       # 'Pakistan', 'United States', 'United Kingdom'
    country: str                    # 'Pakistan', 'United States', 'United Kingdom'
    default_currency: str           # 'PKR', 'USD', 'GBP', 'JPY', 'HKD', 'INR'
    timezone: str                   # 'Asia/Karachi', 'America/New_York', 'Europe/London'
    status: str = "ACTIVE"          # 'ACTIVE', 'INACTIVE'
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExchangeDTO:
    id: str                         # 'PSX', 'NASDAQ', 'NYSE', 'LSE', 'TSE', 'HKEX', 'NSE', 'BSE'
    market_id: str                  # 'PK', 'US', 'GB', 'JP', 'HK', 'IN'
    code: str                       # 'PSX', 'NASDAQ', 'NYSE'
    name: str                       # 'Pakistan Stock Exchange', 'NASDAQ Stock Market'
    country: str                    # 'Pakistan', 'United States'
    currency: str                   # 'PKR', 'USD'
    timezone: str                   # 'Asia/Karachi', 'America/New_York'
    mic_code: Optional[str] = None  # 'XKAR', 'XNAS', 'XNYS', 'XLON', 'XJPX', 'XHKG', 'XNSE', 'XBOM'
    website: Optional[str] = None
    status: str = "ACTIVE"
    trading_calendar_id: str = "DEFAULT"


# ─────────────────────────────────────────────────────────
# Predefined Global Markets & Exchanges Registry
# ─────────────────────────────────────────────────────────

SUPPORTED_MARKETS: Dict[str, MarketDTO] = {
    "PK": MarketDTO(
        id="PK",
        code="PK",
        name="Pakistan",
        country="Pakistan",
        default_currency="PKR",
        timezone="Asia/Karachi",
        status="ACTIVE",
        metadata={"region": "South Asia", "emerging_market": True},
    ),
    "US": MarketDTO(
        id="US",
        code="US",
        name="United States",
        country="United States",
        default_currency="USD",
        timezone="America/New_York",
        status="ACTIVE",
        metadata={"region": "North America", "developed_market": True},
    ),
    "GB": MarketDTO(
        id="GB",
        code="GB",
        name="United Kingdom",
        country="United Kingdom",
        default_currency="GBP",
        timezone="Europe/London",
        status="ACTIVE",
        metadata={"region": "Western Europe", "developed_market": True},
    ),
}

SUPPORTED_EXCHANGES: Dict[str, ExchangeDTO] = {
    "PSX": ExchangeDTO(
        id="PSX",
        market_id="PK",
        code="PSX",
        name="Pakistan Stock Exchange",
        country="Pakistan",
        currency="PKR",
        timezone="Asia/Karachi",
        mic_code="XKAR",
        website="https://www.psx.com.pk",
        status="ACTIVE",
        trading_calendar_id="PSX",
    ),
    "NASDAQ": ExchangeDTO(
        id="NASDAQ",
        market_id="US",
        code="NASDAQ",
        name="NASDAQ Stock Market",
        country="United States",
        currency="USD",
        timezone="America/New_York",
        mic_code="XNAS",
        website="https://www.nasdaq.com",
        status="ACTIVE",
        trading_calendar_id="US",
    ),
    "NYSE": ExchangeDTO(
        id="NYSE",
        market_id="US",
        code="NYSE",
        name="New York Stock Exchange",
        country="United States",
        currency="USD",
        timezone="America/New_York",
        mic_code="XNYS",
        website="https://www.nyse.com",
        status="ACTIVE",
        trading_calendar_id="US",
    ),
    "LSE": ExchangeDTO(
        id="LSE",
        market_id="GB",
        code="LSE",
        name="London Stock Exchange",
        country="United Kingdom",
        currency="GBP",
        timezone="Europe/London",
        mic_code="XLON",
        website="https://www.londonstockexchange.com",
        status="ACTIVE",
        trading_calendar_id="GB",
    ),
}


def build_security_id(market_code: str, exchange_code: str, symbol: str) -> str:
    """
    Constructs canonical globally unique security_id.
    Example: build_security_id('PK', 'PSX', 'ENGRO') -> 'PK.PSX.ENGRO'
             build_security_id('US', 'NASDAQ', 'AAPL') -> 'US.NASDAQ.AAPL'
    """
    clean_m = market_code.strip().upper()
    clean_e = exchange_code.strip().upper()
    clean_s = symbol.strip().upper().replace("/", "_").replace(".", "_")
    return f"{clean_m}.{clean_e}.{clean_s}"


def parse_security_id(security_id: str) -> tuple[str, str, str]:
    """
    Parses canonical security_id into (market_code, exchange_code, symbol).
    """
    parts = security_id.split(".")
    if len(parts) >= 3:
        return parts[0], parts[1], ".".join(parts[2:])
    elif len(parts) == 2:
        return "UNKNOWN", parts[0], parts[1]
    return "UNKNOWN", "UNKNOWN", security_id
