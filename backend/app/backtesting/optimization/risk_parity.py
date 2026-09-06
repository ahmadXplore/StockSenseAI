"""
StockSense AI — Risk Parity Optimization
Equal Risk Contribution (ERC) portfolio solver where each security contributes an equal share of portfolio risk.
"""

from typing import Tuple, Optional
import numpy as np
from scipy.optimize import minimize


def optimize_risk_parity(
    cov_matrix: np.ndarray,
    min_weight: float = 0.01,
    max_weight: Optional[float] = None,
) -> np.ndarray:
    """
    Optimizes portfolio weights so that Marginal Risk Contribution (MRC) is equal across all assets.
    """
    n = cov_matrix.shape[0]
    if n == 1:
        return np.array([1.0])

    effective_max_w = max_weight if max_weight is not None else 1.0

    def risk_budget_objective(w):
        w = np.array(w)
        port_vol = np.sqrt(np.dot(w.T, np.dot(cov_matrix, w)))
        if port_vol <= 1e-6:
            return 1e6
        # Marginal Risk Contribution = w * (Cov * w) / port_vol
        mrc = np.dot(cov_matrix, w) / port_vol
        rc = w * mrc
        target_rc = port_vol / n
        # Minimize sum of squared differences between individual RC and target RC
        return np.sum((rc - target_rc) ** 2)

    cons = ({'type': 'eq', 'fun': lambda w: np.sum(w) - 1.0})
    bounds = tuple((min_weight, effective_max_w) for _ in range(n))
    init_w = np.array([1.0 / n] * n)

    res = minimize(risk_budget_objective, init_w, method='SLSQP', bounds=bounds, constraints=cons)

    if res.success:
        opt_w = np.clip(res.x, 0.0, 1.0)
        return opt_w / np.sum(opt_w)
    return init_w
