"""
StockSense AI — Conditional Value at Risk (CVaR / Expected Shortfall)
Computes Expected Shortfall: the expected tail loss given that the loss exceeds the VaR threshold.
"""

from typing import List, Tuple
import numpy as np


def compute_cvar(
    daily_returns: List[float],
    confidence_level: float = 0.95,
    portfolio_value: float = 100000.0,
    annualize: bool = False
) -> Tuple[float, float]:
    """
    Computes (CVaR %, CVaR Dollar Amount).
    """
    if len(daily_returns) < 5:
        return 0.0, 0.0

    arr = np.array(daily_returns)
    alpha = (1.0 - confidence_level) * 100.0
    var_threshold = np.percentile(arr, alpha)
    
    # Select returns in the tail beyond the VaR threshold
    tail_losses = arr[arr <= var_threshold]
    if len(tail_losses) == 0:
        cvar_pct = max(0.0, -float(var_threshold))
    else:
        cvar_pct = max(0.0, -float(np.mean(tail_losses)))

    if annualize:
        cvar_pct = cvar_pct * np.sqrt(252.0)

    cvar_dollar = cvar_pct * portfolio_value
    return round(cvar_pct, 6), round(cvar_dollar, 2)
