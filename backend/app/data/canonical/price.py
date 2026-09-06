"""
StockSense AI — Canonical Historical Price & Raw Record Models
Defines internal canonical representation for OHLCV data across all markets.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, date, timezone
from typing import Optional, Dict, Any, List
from decimal import Decimal


@dataclass
class CanonicalPriceDTO:
    security_id: str
    ticker: str
    timestamp: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    adj_close: Decimal
    volume: int
    vwap: Optional[Decimal] = None
    currency: str = "USD"
    
    # Corporate action factors
    split_factor: Decimal = Decimal("1.0")
    dividend_amount: Decimal = Decimal("0.0")
    
    # Provenance & Quality
    source_id: Optional[str] = None
    data_source: str = "unknown"
    is_adjusted: bool = True
    quality_flag: str = "ok"         # 'ok', 'suspect', 'gap', 'flagged_move', 'zero_volume'
    retrieved_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def is_geometrically_valid(self) -> bool:
        """
        Validates internal OHLC structural integrity:
        high >= max(open, close, low) and low <= min(open, close, high).
        """
        max_oc = max(self.open, self.close)
        min_oc = min(self.open, self.close)
        if self.high < max_oc or self.high < self.low:
            return False
        if self.low > min_oc or self.low > self.high:
            return False
        if self.volume < 0:
            return False
        if self.open < 0 or self.high < 0 or self.low < 0 or self.close < 0:
            return False
        return True


@dataclass
class RawMarketRecordDTO:
    source: str
    provider: str
    retrieval_timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    original_reference: Optional[str] = None
    checksum: Optional[str] = None
    raw_payload: Optional[str] = None
    record_count: int = 0
    schema_version: str = "1.0"
    ingested: bool = False
