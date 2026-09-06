"""
StockSense AI — Mergers, Acquisitions & Stock Swaps
Handles corporate reorganizations where existing shares are converted into cash, acquiring shares, or delisted.
"""

from typing import Tuple, Optional


def apply_merger_acquisition(
    current_shares: float,
    cash_per_share: float = 0.0,
    swap_ratio: float = 0.0,
    acquirer_price: Optional[float] = None,
) -> Tuple[float, float]:
    """
    Computes cash proceeds and/or replacement acquirer shares from an M&A corporate action.
    Returns:
    - (total_cash_proceeds, new_acquirer_shares)
    """
    if current_shares <= 0:
        return 0.0, 0.0

    cash_proceeds = current_shares * cash_per_share
    new_shares = current_shares * swap_ratio if swap_ratio > 0 else 0.0

    return round(cash_proceeds, 4), round(new_shares, 6)
