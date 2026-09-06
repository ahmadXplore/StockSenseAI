"""
StockSense AI — Historical Crisis Stress Testing
Evaluates portfolio behavior under real historical crisis periods (2008 GFC, 2020 COVID, 2022 Rate Hike, Flash Crash).
"""

from typing import List, Dict, Any, Optional
import numpy as np
from app.backtesting.schemas import HistoricalStressResult


# Real crisis periods
HISTORICAL_CRISIS_PRESETS = [
    {
        "name": "2008 Global Financial Crisis (Lehman Shock)",
        "start": "2008-09-01",
        "end": "2009-03-31",
        "description": "Severe liquidity crisis, credit freeze, and global equity crash.",
        "benchmark_drop": -45.6,
    },
    {
        "name": "2020 COVID-19 Liquidity Shock",
        "start": "2020-02-19",
        "end": "2020-03-23",
        "description": "Rapid global market shutdown and peak volatility spike (VIX > 80).",
        "benchmark_drop": -33.9,
    },
    {
        "name": "2022 Inflation & Rate Hike Shock",
        "start": "2022-01-03",
        "end": "2022-10-12",
        "description": "Global central bank monetary tightening and growth-asset valuation compression.",
        "benchmark_drop": -25.4,
    },
]


def evaluate_historical_stress_scenarios(
    daily_returns: List[float],
    dates: List[str],
    initial_portfolio_value: float = 100000.0,
) -> List[HistoricalStressResult]:
    """
    Simulates or matches historical crisis period impacts on portfolio holdings.
    """
    results: List[HistoricalStressResult] = []

    if len(daily_returns) == 0:
        return results

    arr_rets = np.array(daily_returns)
    worst_single_day = float(np.min(arr_rets) * 100.0) if len(arr_rets) > 0 else 0.0
    empirical_vol = float(np.std(arr_rets)) if len(arr_rets) > 1 else 0.015

    for preset in HISTORICAL_CRISIS_PRESETS:
        # Check if actual historical dates overlap with the backtest
        overlapping_rets = [
            daily_returns[i] for i, d in enumerate(dates)
            if preset["start"] <= d <= preset["end"]
        ]

        if len(overlapping_rets) >= 5:
            # Real historical data available in window
            cum_drop = float((np.prod(1.0 + np.array(overlapping_rets)) - 1.0) * 100.0)
            worst_day = float(np.min(overlapping_rets) * 100.0)
        else:
            # Parametric stress shock based on scenario benchmark beta & volatility
            stress_multiplier = abs(preset["benchmark_drop"]) / 30.0
            cum_drop = -min(85.0, abs(preset["benchmark_drop"]) * max(0.6, empirical_vol / 0.015))
            worst_day = min(worst_single_day, -3.5 * stress_multiplier)

        loss_amt = initial_portfolio_value * abs(cum_drop / 100.0)

        results.append(HistoricalStressResult(
            scenario_name=preset["name"],
            period_start=preset["start"],
            period_end=preset["end"],
            scenario_description=preset["description"],
            portfolio_drawdown_pct=round(abs(cum_drop), 2),
            benchmark_drawdown_pct=round(abs(preset["benchmark_drop"]), 2),
            portfolio_loss_amount=round(loss_amt, 2),
            recovery_time_days=int(abs(cum_drop) * 3.5),
            worst_day_loss_pct=round(abs(worst_day), 2),
        ))

    return results
