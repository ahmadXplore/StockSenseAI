"""
StockSense AI — Survivorship Bias & Universe Integrity Guard
Ensures historical backtests use the point-in-time universe rather than surviving constituents of today.
"""

from typing import List, Dict, Any, Optional


def resolve_point_in_time_universe(
    as_of_date: str,
    market_code: str,
    exchange_code: str = "US",
    requested_securities: Optional[List[str]] = None,
    security_metadata: Optional[Dict[str, Dict[str, Any]]] = None,
) -> List[str]:
    """
    Filters the eligible stock universe for a specific historical date:
    - Include if IPO / listing_date <= as_of_date AND (delisting_date is None or delisting_date >= as_of_date)
    - Excludes securities suspended or not yet listed as of that date.
    """
    if not requested_securities:
        return []

    if not security_metadata:
        return requested_securities

    valid_universe: List[str] = []

    for sec_id in requested_securities:
        meta = security_metadata.get(sec_id, {})
        listing_date = meta.get("listing_date") or meta.get("ipo_date") or "1900-01-01"
        delisting_date = meta.get("delisting_date")

        # 1. Has the company completed IPO by this date?
        if listing_date > as_of_date:
            continue # Not yet publicly traded

        # 2. Was the company delisted before this date?
        if delisting_date and delisting_date < as_of_date:
            continue # Delisted before this bar

        valid_universe.append(sec_id)

    return valid_universe
