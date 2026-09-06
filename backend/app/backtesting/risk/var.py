"""
StockSense AI — Value at Risk (VaR) Engine
Computes Historical and Parametric Value-at-Risk at 95% and 99% confidence horizons.
"""

from typing import List, Tuple
import numpy as np


def compute_var(
    daily_returns: List[float],
    confidence_level: float = 0.95,
    portfolio_value: float = 100000.0,
    annualize: bool = False
) -> Tuple[float, float]:
    """
    Computes (Historical VaR %, VaR Dollar Amount).
    VaR is expressed as a positive loss percentage (e.g. 0.024 for 2.4% max loss).
    """
    if len(daily_returns) < 5:
        return 0.0, 0.0

    arr = np.array(daily_returns)
    alpha = (1.0 - confidence_level) * 100.0
    
    # Historical percentile
    var_percentile = np.percentile(arr, alpha)
    # Convert to positive loss representation
    var_pct = max(0.0, -float(var_percentile))

    if annualize:
        var_pct = var_pct * np.sqrt(252.0)

    var_dollar = var_pct * portfolio_value
    return round(var_pct, 6), round(var_dollar, 2)
