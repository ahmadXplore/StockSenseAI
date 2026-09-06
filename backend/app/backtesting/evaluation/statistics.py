"""
StockSense AI — Monthly Heatmaps & Trade Return Statistics
Generates calendar year/month returns heatmap matrix and streak distributions.
"""

from typing import List, Dict
from datetime import datetime
from app.backtesting.schemas import EquityCurvePoint


def generate_monthly_returns_heatmap(equity_curve: List[EquityCurvePoint]) -> Dict[str, Dict[str, float]]:
    """
    Computes monthly return percentage matrix grouped by year and month.
    Example: {"2024": {"01": 3.2, "02": -1.1, ...}}
    """
    if len(equity_curve) < 2:
        return {}

    heatmap: Dict[str, Dict[str, float]] = {}
    month_starts: Dict[str, float] = {}
    month_ends: Dict[str, float] = {}

    for pt in equity_curve:
        dt = datetime.strptime(pt.date, "%Y-%m-%d")
        year_str = str(dt.year)
        month_str = f"{dt.month:02d}"
        ym_key = f"{year_str}-{month_str}"

        if ym_key not in month_starts:
            month_starts[ym_key] = pt.portfolio_value
        month_ends[ym_key] = pt.portfolio_value

    for ym_key, start_val in month_starts.items():
        year_str, month_str = ym_key.split("-")
        end_val = month_ends[ym_key]
        m_ret = ((end_val - start_val) / start_val) * 100.0 if start_val > 0 else 0.0

        if year_str not in heatmap:
            heatmap[year_str] = {}
        heatmap[year_str][month_str] = round(m_ret, 2)

    return heatmap


def generate_yearly_returns(heatmap: Dict[str, Dict[str, float]]) -> Dict[str, float]:
    """Computes total compounded return per year from the monthly matrix."""
    yearly: Dict[str, float] = {}
    for yr, months in heatmap.items():
        compounded = 1.0
        for m_ret in months.values():
            compounded *= (1.0 + (m_ret / 100.0))
        yearly[yr] = round((compounded - 1.0) * 100.0, 2)
    return yearly
