"""
StockSense AI — PSX Data Sanitizer & Validator
Specialized sanitization for PSX CSV records (LDCP handling, untraded days, symbol normalization).
"""

from __future__ import annotations
from decimal import Decimal, InvalidOperation
from typing import Dict, Any, Tuple, Optional


def sanitize_psx_row(row: Dict[str, Any]) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """
    Sanitizes raw row from PSX CSV / Feed.
    Returns: (cleaned_dict, error_message)
    """
    raw_symbol = str(row.get("SYMBOL", "")).strip().upper()
    if not raw_symbol or raw_symbol in ("SYMBOL", "DATE"):
        return None, "Empty or header symbol"

    date_str = str(row.get("DATE", "")).strip()
    if not date_str or len(date_str) < 10:
        return None, f"Invalid date: {date_str}"

    try:
        ldcp = Decimal(str(row.get("LDCP", "0")).replace(",", ""))
        c_open = Decimal(str(row.get("OPEN", "0")).replace(",", ""))
        c_high = Decimal(str(row.get("HIGH", "0")).replace(",", ""))
        c_low = Decimal(str(row.get("LOW", "0")).replace(",", ""))
        c_close = Decimal(str(row.get("CLOSE", "0")).replace(",", ""))
        volume = int(float(str(row.get("VOLUME", "0")).replace(",", "")))
    except (InvalidOperation, ValueError) as e:
        return None, f"Numeric parse failure: {e}"

    # Handle untraded session: If open, high, low are 0 but close > 0, carry close
    if c_open == 0 and c_high == 0 and c_low == 0 and c_close > 0:
        c_open = c_close
        c_high = c_close
        c_low = c_close

    # If close is 0 but LDCP > 0 and volume == 0 (no trades occurred)
    if c_close == 0 and ldcp > 0:
        c_close = ldcp
        c_open = ldcp
        c_high = ldcp
        c_low = ldcp

    # Ensure non-negative
    if volume < 0:
        volume = 0

    # Ensure geometry validity
    if c_close > 0:
        c_high = max(c_high, c_open, c_close, c_low)
        c_low = min(c_low, c_open, c_close, c_high)
        if c_low <= 0:
            c_low = min(c_open, c_close)

    return {
        "date": date_str,
        "symbol": raw_symbol,
        "ldcp": ldcp,
        "open": c_open,
        "high": c_high,
        "low": c_low,
        "close": c_close,
        "volume": volume,
    }, None
