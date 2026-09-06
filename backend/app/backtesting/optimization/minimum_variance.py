"""
StockSense AI — Minimum Variance Optimization
Finds the global minimum variance portfolio weights regardless of expected returns.
"""

from typing import Tuple
import numpy as np
from scipy.optimize import minimize


def optimize_minimum_variance(
    cov_matrix: np.ndarray,
    min_weight: float = 0.0,
    max_weight: float = 0.50,
) -> np.ndarray:
    """
    Minimizes w^T * Cov * w subject to sum(w) == 1 and individual weight bounds.
    """
    n = cov_matrix.shape[0]
    if n == 1:
        return np.array([1.0])

    def portfolio_variance(w):
        return np.dot(w.T, np.dot(cov_matrix, w))

    cons = ({'type': 'eq', 'fun': lambda w: np.sum(w) - 1.0})
    bounds = tuple((min_weight, max_weight) for _ in range(n))
    init_w = np.array([1.0 / n] * n)

    res = minimize(portfolio_variance, init_w, method='SLSQP', bounds=bounds, constraints=cons)

    if res.success:
        opt_w = np.clip(res.x, 0.0, 1.0)
        return opt_w / np.sum(opt_w)
    return init_w
