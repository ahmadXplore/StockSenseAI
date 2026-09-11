"""
StockSense AI — Brokerage & Commission Models
Computes broker commissions based on share count, trade value, market conventions, or minimum fees.

Market Commission Defaults (when commission_pct=0 and commission_per_share=0):
    US:    $0.005/share (Interactive Brokers style)
    PK:    0.15% of trade value (PSX standard retail brokerage)
    UK/GB: max(£5.00, 0.10% of trade value) (typical UK broker)
    IN:    min(₹20, 0.05% of trade value) (Zerodha / Groww style)
    JP:    max(¥550, 0.10% of trade value)
    HK:    max(HK$50, 0.25% of trade value) (typical HK broker)
"""

from typing import Optional


def calculate_commission(
    trade_value: float,
    shares: float,
    market_code: str,
    commission_pct: float = 0.001,
    commission_per_share: float = 0.0,
    min_commission: float = 0.0,
    enable_broker_commissions: bool = True,
) -> float:
    """
    Computes brokerage commissions across markets.

    Args:
        trade_value:             Executed trade value (price × shares)
        shares:                  Number of shares
        market_code:             Market identifier — US, PK, UK, GB, IN, JP, HK
        commission_pct:          Percentage commission (overrides market default if > 0)
        commission_per_share:    Per-share commission (highest priority if > 0)
        min_commission:          Minimum commission floor
        enable_broker_commissions: If False, returns 0 (useful for fee-free broker testing)
    """
    if trade_value <= 0 or shares <= 0 or not enable_broker_commissions:
        return 0.0

    market = market_code.upper()
    # GB and UK are synonymous
    if market == "GB":
        market = "UK"

    fee = 0.0

    # Per-share model takes highest priority
    if commission_per_share > 0:
        fee = shares * commission_per_share

    # Percentage model takes second priority
    elif commission_pct > 0:
        fee = trade_value * commission_pct

    # Market-default fallback when caller provides zero configuration
    else:
        if market == "US":
            fee = max(1.0, shares * 0.005)        # $0.005/share, min $1
        elif market == "PK":
            fee = trade_value * 0.0015             # 0.15% PSX retail brokerage
        elif market == "UK":
            fee = max(5.0, trade_value * 0.001)   # 0.10% min £5 (LSE typical)
        elif market == "IN":
            fee = min(20.0, trade_value * 0.0005) # 0.05% capped at ₹20
        elif market == "JP":
            fee = max(550.0, trade_value * 0.001) # 0.10% min ¥550
        elif market == "HK":
            fee = max(50.0, trade_value * 0.0025) # 0.25% min HK$50
        else:
            fee = trade_value * 0.001              # Generic 0.1% fallback

    # Apply minimum commission floor
    if min_commission > 0:
        fee = max(min_commission, fee)

    return round(fee, 4)
