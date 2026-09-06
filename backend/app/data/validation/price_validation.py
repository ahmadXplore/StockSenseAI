"""
StockSense AI — Canonical Price Validation Engine
Validates OHLC bounding, non-negativity, timestamps, and volume constraints.
"""

from __future__ import annotations
from typing import List, Tuple, Set, Dict, Any
from datetime import datetime
from decimal import Decimal

from app.data.canonical.price import CanonicalPriceDTO


def validate_ohlcv_record(price: CanonicalPriceDTO) -> Tuple[bool, List[str]]:
    """
    Validates a single CanonicalPriceDTO against geometric and logical constraints.
    """
    errors: List[str] = []

    # 1. Non-negativity
    if price.open < 0:
        errors.append(f"Negative open price: {price.open}")
    if price.high < 0:
        errors.append(f"Negative high price: {price.high}")
    if price.low < 0:
        errors.append(f"Negative low price: {price.low}")
    if price.close < 0:
        errors.append(f"Negative close price: {price.close}")
    if price.volume < 0:
        errors.append(f"Negative volume: {price.volume}")

    # 2. Geometric bounds
    if price.high < price.low:
        errors.append(f"High ({price.high}) is lower than Low ({price.low})")
    if price.high < max(price.open, price.close):
        errors.append(f"High ({price.high}) is less than max(open, close)")
    if price.low > min(price.open, price.close):
        errors.append(f"Low ({price.low}) is greater than min(open, close)")

    is_valid = len(errors) == 0
    return is_valid, errors


def validate_price_series(prices: List[CanonicalPriceDTO]) -> Tuple[List[CanonicalPriceDTO], List[CanonicalPriceDTO], List[str]]:
    """
    Validates and deduplicates a series of CanonicalPriceDTO records.
    Returns: (accepted_records, rejected_records, log_messages)
    """
    accepted: List[CanonicalPriceDTO] = []
    rejected: List[CanonicalPriceDTO] = []
    logs: List[str] = []

    seen_keys: Set[Tuple[str, datetime]] = set()

    for p in sorted(prices, key=lambda x: (x.security_id, x.timestamp)):
        # Key on (security_id, timestamp) so multiple stocks on the same date are preserved
        key = (p.security_id, p.timestamp)
        if key in seen_keys:
            rejected.append(p)
            logs.append(f"Duplicate timestamp detected for {p.security_id} at {p.timestamp}")
            continue

        is_valid, errs = validate_ohlcv_record(p)
        if not is_valid:
            rejected.append(p)
            logs.extend([f"{p.security_id} {p.timestamp.date()}: {e}" for e in errs])
        else:
            seen_keys.add(key)
            accepted.append(p)

    return accepted, rejected, logs
