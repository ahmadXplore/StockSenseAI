"""
StockSense AI — Brokerage & Commission Models
Computes broker commissions based on share count, trade value, market conventions, or minimum fees.
"""

from typing import Optional


def calculate_commission(
    trade_value: float,
    shares: float,
    market_code: str,
    commission_pct: float = 0.001,
    commission_per_share: float = 0.0,
    min_commission: float = 0.0,
) -> float:
    """
    Computes brokerage commissions across markets.
    - If commission_per_share > 0: uses per-share model (common in US, e.g. $0.005/share).
    - Otherwise: uses percentage of trade value (e.g. 0.1% or 0.15% in PSX, UK, IN).
    """
    if trade_value <= 0 or shares <= 0:
        return 0.0

    fee = 0.0
    market = market_code.upper()

    if commission_per_share > 0:
        fee = shares * commission_per_share
    elif commission_pct > 0:
        fee = trade_value * commission_pct
    else:
        # Default market baselines if zero configuration
        if market == "US":
            fee = max(0.0, shares * 0.005) # $0.005 per share
        elif market == "PK":
            fee = trade_value * 0.0015 # 0.15% standard PSX retail brokerage
        elif market == "UK":
            fee = max(5.0, trade_value * 0.001)
        elif market == "IN":
            fee = min(20.0, trade_value * 0.0005)
        else:
            fee = trade_value * 0.001

    if min_commission > 0:
        fee = max(min_commission, fee)

    return round(fee, 4)
