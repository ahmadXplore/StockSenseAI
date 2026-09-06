"""
StockSense AI — Bid/Ask Spread Modeling
Estimates or applies point-in-time bid/ask spreads across global exchanges.
"""

from typing import Optional


def estimate_bid_ask_spread(
    price: float,
    market_code: str,
    exchange_code: str = "US",
    volume: Optional[float] = None
) -> float:
    """
    Estimates the effective dollar spread per share based on exchange and liquidity tiers.
    """
    if price <= 0:
        return 0.01

    market = market_code.upper()

    if market == "US":
        # Highly liquid US mega-caps have tight pennies spreads, small caps wider
        if volume and volume > 5_000_000:
            return 0.01
        elif volume and volume > 500_000:
            return 0.03
        else:
            return max(0.02, price * 0.0005)

    elif market == "PK":
        # Pakistan Stock Exchange (PSX) tick size & spread dynamics (PKR)
        if price < 100:
            return 0.05
        elif price < 500:
            return 0.25
        else:
            return max(0.50, price * 0.001)

    elif market in ("UK", "LSE"):
        return max(0.01, price * 0.0008)

    elif market in ("JP", "TSE"):
        return max(0.5, price * 0.0005)

    elif market in ("IN", "NSE", "BSE"):
        return max(0.05, price * 0.0006)

    return max(0.01, price * 0.001)
