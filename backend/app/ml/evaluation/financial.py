"""
StockSense AI — Financial Performance Evaluation Metrics
Calculates simulated Strategy Sharpe, Sortino, Maximum Drawdown, and Win Rate.
"""

from __future__ import annotations
import numpy as np
from dataclasses import dataclass


@dataclass
class FinancialMetricsResult:
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown_pct: float
    win_rate_pct: float
    cumulative_return_pct: float


def evaluate_financial_performance(
    actual_returns: np.ndarray,
    predicted_directions: np.ndarray,
    risk_free_rate: float = 0.04
) -> FinancialMetricsResult:
    rets = np.asarray(actual_returns).ravel().astype(float)
    signals = np.asarray(predicted_directions).ravel().astype(int)

    # Strategy returns: Long if signal == 1 else cash (0.0)
    strat_returns = np.where(signals == 1, rets, 0.0)
    
    if len(strat_returns) == 0:
        return FinancialMetricsResult(0.0, 0.0, 0.0, 0.0, 0.0)

    # Cumulative wealth path
    cum_wealth = np.cumprod(1.0 + strat_returns)
    peak = np.maximum.accumulate(cum_wealth)
    drawdowns = (cum_wealth - peak) / peak
    max_dd = float(np.min(drawdowns) * 100.0) if len(drawdowns) > 0 else 0.0

    # Win rate on active trades
    active_trades = strat_returns[signals == 1]
    win_rate = float((active_trades > 0).mean() * 100.0) if len(active_trades) > 0 else 50.0

    # Annualized Sharpe (assuming 12 periods/year for 30D horizon)
    mean_ret = np.mean(strat_returns) * 12.0
    vol = np.std(strat_returns) * np.sqrt(12)
    sharpe = float((mean_ret - risk_free_rate) / vol) if vol > 0 else 0.0

    # Downside volatility for Sortino
    downside = strat_returns[strat_returns < 0]
    downside_vol = np.std(downside) * np.sqrt(12) if len(downside) > 0 else 1e-6
    sortino = float((mean_ret - risk_free_rate) / downside_vol) if downside_vol > 0 else 0.0

    cum_ret = float((cum_wealth[-1] - 1.0) * 100.0) if len(cum_wealth) > 0 else 0.0

    return FinancialMetricsResult(
        sharpe_ratio=round(sharpe, 2),
        sortino_ratio=round(sortino, 2),
        max_drawdown_pct=round(max_dd, 2),
        win_rate_pct=round(win_rate, 2),
        cumulative_return_pct=round(cum_ret, 2)
    )
