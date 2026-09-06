"""
StockSense AI — International Market Data Validator
Sanitizes and checks raw responses from international free APIs (yfinance, Stooq, AV).
"""

from __future__ import annotations
from decimal import Decimal, InvalidOperation
from typing import Dict, Any, Tuple, Optional


def sanitize_international_candle(
    ticker: str,
    timestamp_str: str,
    raw_open: Any,
    raw_high: Any,
    raw_low: Any,
    raw_close: Any,
    raw_adj_close: Any,
    raw_volume: Any,
    currency: str = "USD"
) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """
    Sanitizes international daily OHLCV bar.
    """
    clean_sym = ticker.strip().upper()
    if not clean_sym:
        return None, "Empty ticker"

    try:
        o = Decimal(str(raw_open))
        h = Decimal(str(raw_high))
        l = Decimal(str(raw_low))
        c = Decimal(str(raw_close))
        adj_c = Decimal(str(raw_adj_close)) if raw_adj_close is not None else c
        v = int(float(str(raw_volume or 0)))
    except (InvalidOperation, ValueError, TypeError) as e:
        return None, f"Numeric parse error: {e}"

    if v < 0:
        v = 0

    if o <= 0 or h <= 0 or l <= 0 or c <= 0:
        return None, "Non-positive price values"

    # Enforce geometric bounding
    h = max(h, o, c, l)
    l = min(l, o, c, h)

    return {
        "ticker": clean_sym,
        "timestamp": timestamp_str,
        "open": o,
        "high": h,
        "low": l,
        "close": c,
        "adj_close": adj_c,
        "volume": v,
        "currency": currency.upper()
    }, None
