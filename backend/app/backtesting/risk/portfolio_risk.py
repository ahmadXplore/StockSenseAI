"""
StockSense AI — Portfolio Risk Metrics Calculator
Computes volatility, downside deviation, Sharpe, Sortino, Calmar, Beta, and tail risk metrics.
"""

from typing import List, Optional, Tuple
import numpy as np
from scipy import stats
from app.backtesting.schemas import RiskMetricsReport
from app.backtesting.risk.var import compute_var
from app.backtesting.risk.cvar import compute_cvar


def calculate_portfolio_risk_report(
    daily_returns: List[float],
    benchmark_returns: Optional[List[float]] = None,
    risk_free_rate: float = 0.045,
    portfolio_value: float = 100000.0,
) -> RiskMetricsReport:
    """
    Computes a comprehensive institutional risk report from timeseries daily returns.
    """
    if len(daily_returns) < 2:
        return RiskMetricsReport(
            portfolio_volatility=0.0,
            downside_deviation=0.0,
            var_95_daily=0.0,
            var_99_daily=0.0,
            cvar_95_daily=0.0,
            cvar_99_daily=0.0,
            var_95_annualized=0.0,
            cvar_95_annualized=0.0,
            skewness=0.0,
            kurtosis=0.0,
            tail_ratio=1.0,
        )

    arr = np.array(daily_returns)
    daily_rf = risk_free_rate / 252.0

    # 1. Volatility
    daily_vol = float(np.std(arr, ddof=1))
    annual_vol = daily_vol * np.sqrt(252.0)

    # 2. Downside Deviation
    downside_diffs = arr[arr < daily_rf] - daily_rf
    if len(downside_diffs) > 0:
        downside_dev = float(np.sqrt(np.mean(downside_diffs ** 2)) * np.sqrt(252.0))
    else:
        downside_dev = 0.0001

    # 3. Value at Risk & CVaR
    var95_d, _ = compute_var(daily_returns, confidence_level=0.95, portfolio_value=portfolio_value, annualize=False)
    var99_d, _ = compute_var(daily_returns, confidence_level=0.99, portfolio_value=portfolio_value, annualize=False)
    cvar95_d, _ = compute_cvar(daily_returns, confidence_level=0.95, portfolio_value=portfolio_value, annualize=False)
    cvar99_d, _ = compute_cvar(daily_returns, confidence_level=0.99, portfolio_value=portfolio_value, annualize=False)

    var95_a, _ = compute_var(daily_returns, confidence_level=0.95, portfolio_value=portfolio_value, annualize=True)
    cvar95_a, _ = compute_cvar(daily_returns, confidence_level=0.95, portfolio_value=portfolio_value, annualize=True)

    # 4. Tail Risk Statistics
    skew = float(stats.skew(arr)) if len(arr) > 3 else 0.0
    kurt = float(stats.kurtosis(arr)) if len(arr) > 3 else 0.0

    # Tail Ratio: 95th percentile / abs(5th percentile)
    p95 = np.percentile(arr, 95)
    p5 = abs(np.percentile(arr, 5))
    tail_ratio = float(p95 / p5) if p5 > 0 else 1.0

    # 5. Benchmark Comparison Metrics (Beta, Alpha, Correlation, Tracking Error)
    beta = None
    alpha = None
    corr = None
    tracking_err = None

    if benchmark_returns and len(benchmark_returns) == len(daily_returns):
        bm_arr = np.array(benchmark_returns)
        bm_var = float(np.var(bm_arr, ddof=1))
        
        if bm_var > 0.0000001:
            cov = float(np.cov(arr, bm_arr)[0, 1])
            beta = round(cov / bm_var, 4)
            corr = round(float(np.corrcoef(arr, bm_arr)[0, 1]), 4)
            
            # Alpha annualized: R_p - [R_f + Beta * (R_m - R_f)]
            port_mean_ann = float(np.mean(arr) * 252.0)
            bm_mean_ann = float(np.mean(bm_arr) * 252.0)
            alpha = round(port_mean_ann - (risk_free_rate + beta * (bm_mean_ann - risk_free_rate)), 4)
            
            # Tracking error
            tracking_diffs = arr - bm_arr
            tracking_err = round(float(np.std(tracking_diffs, ddof=1) * np.sqrt(252.0)), 4)

    return RiskMetricsReport(
        portfolio_volatility=round(annual_vol, 4),
        downside_deviation=round(downside_dev, 4),
        beta_to_benchmark=beta,
        alpha_annualized=alpha,
        correlation_to_benchmark=corr,
        tracking_error=tracking_err,
        var_95_daily=var95_d,
        var_99_daily=var99_d,
        cvar_95_daily=cvar95_d,
        cvar_99_daily=cvar99_d,
        var_95_annualized=var95_a,
        cvar_95_annualized=cvar95_a,
        skewness=round(skew, 4),
        kurtosis=round(kurt, 4),
        tail_ratio=round(tail_ratio, 4),
    )
