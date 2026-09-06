"""
StockSense AI — Cash & Stock Dividends
Processes dividend declarations on ex-dates, either crediting cash or reinvesting into additional shares (DRIP).
"""

from typing import Tuple


def apply_cash_dividend(
    shares: float,
    dividend_per_share: float,
    current_market_price: float,
    reinvest: bool = True,
    withholding_tax_pct: float = 0.0,
) -> Tuple[float, float, float]:
    """
    Computes net dividend proceeds.
    Returns:
    - (net_cash_payout, additional_shares_purchased, new_cash_balance_change)
    """
    if shares <= 0 or dividend_per_share <= 0:
        return 0.0, 0.0, 0.0

    gross_dividend = shares * dividend_per_share
    tax_amount = gross_dividend * (withholding_tax_pct / 100.0)
    net_dividend = gross_dividend - tax_amount

    if reinvest and current_market_price > 0:
        new_shares = net_dividend / current_market_price
        return round(net_dividend, 4), round(new_shares, 6), 0.0
    else:
        # Credit cash to portfolio
        return round(net_dividend, 4), 0.0, round(net_dividend, 4)
