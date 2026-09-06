"""
StockSense AI — Canonical Security Master Validation
Validates security identifier format, exchange linkage, and listing date logic.
"""

from __future__ import annotations
from typing import List, Tuple
from app.data.canonical.security import SecurityDTO


def validate_security_record(sec: SecurityDTO) -> Tuple[bool, List[str]]:
    """
    Validates a SecurityDTO entity.
    """
    errors: List[str] = []

    if not sec.security_id or "." not in sec.security_id:
        errors.append(f"Invalid security_id format: {sec.security_id}. Must be <MARKET>.<EXCHANGE>.<SYMBOL>")

    if not sec.symbol:
        errors.append("Security symbol is empty")

    if not sec.market_id:
        errors.append("Market ID is missing")

    if not sec.exchange_id:
        errors.append("Exchange ID is missing")

    if not sec.currency:
        errors.append("Currency is missing")

    if sec.listing_date and sec.delisting_date:
        if sec.delisting_date < sec.listing_date:
            errors.append(f"Delisting date ({sec.delisting_date}) is prior to listing date ({sec.listing_date})")

    return len(errors) == 0, errors
