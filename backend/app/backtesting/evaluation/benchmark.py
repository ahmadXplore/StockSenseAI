"""
StockSense AI — Market-Aware Benchmark Comparison
Calculates relative returns, excess return, Alpha, Beta, Information Ratio, and tracking error against market indices.
"""

from typing import Dict, List, Any, Optional
import numpy as np


# Market default benchmark index mapping
DEFAULT_MARKET_BENCHMARKS: Dict[str, str] = {
    "PK": "KSE100",
    "US": "SPY",
    "UK": "FTSE100",
    "JP": "N225",
    "HK": "HSI",
    "IN": "NIFTY50",
}


def compute_benchmark_comparison(
    portfolio_daily_returns: List[float],
    benchmark_daily_returns: List[float],
    risk_free_rate: float = 0.045,
) -> Dict[str, Any]:
    """
    Computes comparative statistics between strategy returns and benchmark index returns.
    """
    n = min(len(portfolio_daily_returns), len(benchmark_daily_returns))
    if n < 5:
        return {
            "excess_return_pct": 0.0,
            "beta": 1.0,
            "alpha_annualized": 0.0,
            "correlation": 0.0,
            "tracking_error_pct": 0.0,
            "information_ratio": 0.0,
        }

    p_rets = np.array(portfolio_daily_returns[:n])
    b_rets = np.array(benchmark_daily_returns[:n])

    p_cum = (np.prod(1.0 + p_rets) - 1.0) * 100.0
    b_cum = (np.prod(1.0 + b_rets) - 1.0) * 100.0
    excess_ret = p_cum - b_cum

    b_var = np.var(b_rets, ddof=1)
    if b_var > 1e-7:
        cov = np.cov(p_rets, b_rets)[0, 1]
        beta = cov / b_var
        corr = np.corrcoef(p_rets, b_rets)[0, 1]
    else:
        beta = 1.0
        corr = 0.0

    p_ann = np.mean(p_rets) * 252.0
    b_ann = np.mean(b_rets) * 252.0
    alpha = p_ann - (risk_free_rate + beta * (b_ann - risk_free_rate))

    diff = p_rets - b_rets
    tracking_err = float(np.std(diff, ddof=1) * np.sqrt(252.0) * 100.0)
    info_ratio = (p_ann - b_ann) / (tracking_err / 100.0) if tracking_err > 0.001 else 0.0

    return {
        "portfolio_total_return_pct": round(float(p_cum), 4),
        "benchmark_total_return_pct": round(float(b_cum), 4),
        "excess_return_pct": round(float(excess_ret), 4),
        "beta": round(float(beta), 4),
        "alpha_annualized": round(float(alpha * 100.0), 4),
        "correlation": round(float(corr), 4),
        "tracking_error_pct": round(float(tracking_err), 4),
        "information_ratio": round(float(info_ratio), 4),
    }
