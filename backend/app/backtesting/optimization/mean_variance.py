"""
StockSense AI — Mean-Variance Portfolio Optimization
Markowitz efficient frontier solver, target return optimization, and quadratic portfolio variance minimization.
"""

from typing import List, Dict, Tuple, Optional
import numpy as np
from scipy.optimize import minimize


def optimize_mean_variance(
    expected_returns: np.ndarray,
    cov_matrix: np.ndarray,
    risk_free_rate: float = 0.045,
    min_weight: float = 0.0,
    max_weight: float = 0.40,
) -> Tuple[np.ndarray, float, float, float]:
    """
    Optimizes portfolio weights for Maximum Sharpe Ratio.
    Returns: (optimal_weights, expected_return, expected_volatility, sharpe_ratio)
    """
    n = len(expected_returns)
    if n == 1:
        w = np.array([1.0])
        ret = float(expected_returns[0])
        vol = float(np.sqrt(cov_matrix[0, 0]))
        sharpe = (ret - risk_free_rate) / max(0.0001, vol)
        return w, ret, vol, sharpe

    # Negative Sharpe Objective function
    def neg_sharpe(w):
        port_ret = np.sum(w * expected_returns)
        port_vol = np.sqrt(np.dot(w.T, np.dot(cov_matrix, w)))
        if port_vol <= 0.00001:
            return 1e6
        return -(port_ret - risk_free_rate) / port_vol

    # Constraints: sum(w) == 1.0
    cons = ({'type': 'eq', 'fun': lambda w: np.sum(w) - 1.0})
    # Bounds: min_weight <= w_i <= max_weight
    bounds = tuple((min_weight, max_weight) for _ in range(n))

    init_w = np.array([1.0 / n] * n)
    res = minimize(neg_sharpe, init_w, method='SLSQP', bounds=bounds, constraints=cons)

    if res.success:
        opt_w = np.clip(res.x, 0.0, 1.0)
        opt_w = opt_w / np.sum(opt_w)
    else:
        opt_w = init_w

    exp_ret = float(np.sum(opt_w * expected_returns))
    exp_vol = float(np.sqrt(np.dot(opt_w.T, np.dot(cov_matrix, opt_w))))
    sharpe = float((exp_ret - risk_free_rate) / max(0.0001, exp_vol))

    return opt_w, exp_ret, exp_vol, sharpe
