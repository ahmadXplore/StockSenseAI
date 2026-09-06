"""
StockSense AI — Canonical Security Master & Symbol History
Defines security identity, life cycle status, and historical ticker transitions.
"""

from __future__ import annotations
from enum import Enum
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from typing import Optional, Dict, Any, List


class SecurityStatus(str, Enum):
    ACTIVE = "ACTIVE"
    DELISTED = "DELISTED"
    SUSPENDED = "SUSPENDED"
    MERGED = "MERGED"
    ACQUIRED = "ACQUIRED"
    INACTIVE = "INACTIVE"


class SecurityType(str, Enum):
    COMMON_STOCK = "COMMON_STOCK"
    ETF = "ETF"
    INDEX = "INDEX"
    PREFERRED = "PREFERRED"
    ADR = "ADR"
    MUTUAL_FUND = "MUTUAL_FUND"
    RIGHTS = "RIGHTS"
    FUTURE = "FUTURE"


@dataclass
class SymbolHistoryDTO:
    security_id: str
    old_symbol: str
    new_symbol: str
    effective_from: date
    effective_to: Optional[date] = None
    reason: Optional[str] = None


@dataclass
class SecurityDTO:
    security_id: str                   # e.g., 'PK.PSX.ENGRO', 'US.NASDAQ.AAPL'
    exchange_id: str                   # 'PSX', 'NASDAQ', 'NYSE'
    market_id: str                     # 'PK', 'US'
    symbol: str                        # 'ENGRO', 'AAPL'
    company_name: str
    legal_name: Optional[str] = None
    country: str = "USA"
    currency: str = "USD"
    sector: Optional[str] = None
    industry: Optional[str] = None
    security_type: SecurityType = SecurityType.COMMON_STOCK
    status: SecurityStatus = SecurityStatus.ACTIVE
    listing_date: Optional[date] = None
    delisting_date: Optional[date] = None
    delisting_reason: Optional[str] = None
    primary_exchange: Optional[str] = None
    
    # Provider & Regulatory Identifiers
    cik: Optional[str] = None
    isin: Optional[str] = None
    cusip: Optional[str] = None
    sedol: Optional[str] = None
    figi: Optional[str] = None
    provider_security_id: Optional[str] = None
    
    symbol_history: List[SymbolHistoryDTO] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def is_active_on(self, as_of: date) -> bool:
        """
        Determines whether security was actively listed on a given historical date.
        Guards against survivorship bias in backtests.
        """
        if self.listing_date and as_of < self.listing_date:
            return False
        if self.delisting_date and as_of > self.delisting_date:
            return False
        return True
