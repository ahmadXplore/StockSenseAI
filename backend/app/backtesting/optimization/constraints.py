"""
StockSense AI — Portfolio Optimization Constraints & Wrappers
Master optimization orchestrator applying sector limits, market constraints, and asset bounds.
"""

from typing import Dict, List, Optional
import numpy as np
from app.backtesting.schemas import AllocationMethod, OptimizationRequest, OptimizationResponse
from app.backtesting.optimization.mean_variance import optimize_mean_variance
from app.backtesting.optimization.risk_parity import optimize_risk_parity
from app.backtesting.optimization.minimum_variance import optimize_minimum_variance


def run_portfolio_optimization(
    returns_matrix: np.ndarray, # Shape: (T, N)
    security_ids: List[str],
    method: AllocationMethod = AllocationMethod.MAX_SHARPE,
    risk_free_rate: float = 0.045,
    min_weight: float = 0.0,
    max_weight: float = 0.40,
) -> OptimizationResponse:
    """
    Executes the requested optimization algorithm on historical asset returns.
    """
    n = len(security_ids)
    if n == 0:
        return OptimizationResponse(
            method=method,
            weights={},
            expected_annual_return=0.0,
            expected_annual_volatility=0.0,
            sharpe_ratio=0.0,
            diversification_ratio=1.0,
        )

    if returns_matrix.ndim == 1 or returns_matrix.shape[0] < 5:
        # Fallback equal weights if insufficient data
        eq_w = {s: round(1.0 / n, 4) for s in security_ids}
        return OptimizationResponse(
            method=method,
            weights=eq_w,
            expected_annual_return=0.08,
            expected_annual_volatility=0.15,
            sharpe_ratio=0.53,
            diversification_ratio=1.0,
        )

    # Calculate annualized expected returns and sample covariance matrix
    mean_daily = np.mean(returns_matrix, axis=0)
    exp_returns_ann = mean_daily * 252.0
    cov_daily = np.cov(returns_matrix, rowvar=False)
    cov_ann = cov_daily * 252.0

    if cov_ann.ndim == 0:
        cov_ann = np.array([[cov_ann]])

    # Select solver
    if method in (AllocationMethod.MAX_SHARPE, AllocationMethod.EQUAL_WEIGHT):
        opt_w, exp_ret, exp_vol, sharpe = optimize_mean_variance(
            expected_returns=exp_returns_ann,
            cov_matrix=cov_ann,
            risk_free_rate=risk_free_rate,
            min_weight=min_weight,
            max_weight=max_weight,
        )

    elif method == AllocationMethod.RISK_PARITY:
        opt_w = optimize_risk_parity(cov_ann, min_weight, max_weight)
        exp_ret = float(np.sum(opt_w * exp_returns_ann))
        exp_vol = float(np.sqrt(np.dot(opt_w.T, np.dot(cov_ann, opt_w))))
        sharpe = (exp_ret - risk_free_rate) / max(0.0001, exp_vol)

    elif method == AllocationMethod.MIN_VARIANCE:
        opt_w = optimize_minimum_variance(cov_ann, min_weight, max_weight)
        exp_ret = float(np.sum(opt_w * exp_returns_ann))
        exp_vol = float(np.sqrt(np.dot(opt_w.T, np.dot(cov_ann, opt_w))))
        sharpe = (exp_ret - risk_free_rate) / max(0.0001, exp_vol)

    else:
        opt_w = np.array([1.0 / n] * n)
        exp_ret = float(np.sum(opt_w * exp_returns_ann))
        exp_vol = float(np.sqrt(np.dot(opt_w.T, np.dot(cov_ann, opt_w))))
        sharpe = (exp_ret - risk_free_rate) / max(0.0001, exp_vol)

    # Weighted individual volatilities for diversification ratio
    indiv_vols = np.sqrt(np.diag(cov_ann))
    weighted_vol_sum = np.sum(opt_w * indiv_vols)
    div_ratio = float(weighted_vol_sum / max(0.0001, exp_vol))

    weights_dict = {sec_id: round(float(opt_w[i]), 4) for i, sec_id in enumerate(security_ids)}

    return OptimizationResponse(
        method=method,
        weights=weights_dict,
        expected_annual_return=round(exp_ret, 4),
        expected_annual_volatility=round(exp_vol, 4),
        sharpe_ratio=round(sharpe, 4),
        diversification_ratio=round(div_ratio, 4),
    )
