"""
StockSense AI — Stock Splits & Reverse Splits Adjustments
Adjusts position share count and average entry cost basis without corrupting historical accounting.
"""

from typing import Tuple


def apply_stock_split(
    current_shares: float,
    current_avg_price: float,
    split_ratio: float, # e.g. 2.0 for 2-for-1 forward split, 0.1 for 1-for-10 reverse split
) -> Tuple[float, float]:
    """
    Adjusts shares and cost basis:
    - New Shares = Old Shares * Split Ratio
    - New Avg Price = Old Avg Price / Split Ratio
    - Total Cost Basis remains invariant: (New Shares * New Avg Price) == (Old Shares * Old Avg Price)
    """
    if split_ratio <= 0 or current_shares <= 0:
        return current_shares, current_avg_price

    new_shares = current_shares * split_ratio
    new_avg_price = current_avg_price / split_ratio

    return round(new_shares, 6), round(new_avg_price, 6)
