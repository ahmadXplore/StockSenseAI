"""
StockSense AI — Historical Universe & Survivorship-Bias Free Resolver
Resolves constituents active on any historical point-in-time date.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import date
from typing import Optional, List, Dict, Any

from app.data.canonical.security import SecurityDTO, SecurityStatus


@dataclass
class HistoricalUniverseResult:
    market: str
    exchange: str
    as_of_date: date
    securities: List[SecurityDTO]
    total_count: int
    active_count: int
    delisted_included_count: int
    is_approximate: bool = False
    warning: Optional[str] = None


def resolve_historical_universe(
    market: str,
    exchange: str,
    as_of_date: date,
    securities: List[SecurityDTO],
    has_exact_constituent_history: bool = True
) -> HistoricalUniverseResult:
    """
    Returns the universe of securities listed and trading as of `as_of_date`.
    Ensures delisted securities are included for historical dates prior to their delisting,
    preventing survivorship bias in ML features and backtests.
    """
    eligible: List[SecurityDTO] = []
    delisted_count = 0
    active_count = 0

    for sec in securities:
        # Check market and exchange
        if market and sec.market_id.upper() != market.upper():
            continue
        if exchange and sec.exchange_id.upper() != exchange.upper():
            continue

        # Point-in-time lifecycle check
        if sec.listing_date and as_of_date < sec.listing_date:
            continue
        if sec.delisting_date and as_of_date > sec.delisting_date:
            continue

        eligible.append(sec)
        if sec.status == SecurityStatus.DELISTED or (sec.delisting_date and sec.delisting_date >= as_of_date):
            if sec.status == SecurityStatus.DELISTED:
                delisted_count += 1
            else:
                active_count += 1
        else:
            active_count += 1

    warning = None
    if not has_exact_constituent_history:
        warning = "CURRENT_UNIVERSE_APPROXIMATE: Point-in-time constituent weights are approximated."

    return HistoricalUniverseResult(
        market=market,
        exchange=exchange,
        as_of_date=as_of_date,
        securities=eligible,
        total_count=len(eligible),
        active_count=active_count,
        delisted_included_count=delisted_count,
        is_approximate=not has_exact_constituent_history,
        warning=warning
    )
