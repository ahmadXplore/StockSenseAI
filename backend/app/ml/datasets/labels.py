"""
StockSense AI — Trading-Calendar Aware ML Label Generation
Generates directional, return, and volatility targets across 7D, 30D, 3M, 6M, 1Y, and 3Y horizons.
"""

from __future__ import annotations
import numpy as np
import pandas as pd
from typing import Dict, List, Optional
from datetime import date

from app.data.calendars.base import TradingCalendar
from app.data.calendars.registry import get_trading_calendar


# Trading days mapping per horizon (assumes ~21 trading days/month, ~252/year)
HORIZON_TRADING_DAYS: Dict[str, int] = {
    "7d": 5,      # 1 calendar week ~ 5 trading days
    "30d": 21,    # 1 month ~ 21 trading days
    "3m": 63,     # 1 quarter ~ 63 trading days
    "6m": 126,    # half year ~ 126 trading days
    "1y": 252,    # 1 year ~ 252 trading days
    "3y": 756,    # 3 years ~ 756 trading days
}


def generate_time_series_labels(
    price_df: pd.DataFrame,
    horizon: str = "30d",
    return_threshold_pct: float = 0.0,
    calendar: Optional[TradingCalendar] = None
) -> pd.DataFrame:
    """
    Generates forward-looking targets for ML models from price series:
    1. 'target_return': Forward return (Close_{t+h} - Close_t) / Close_t
    2. 'target_direction': Binary 1 if target_return > threshold else 0
    3. 'target_volatility': Forward realized volatility over horizon window
    """
    if price_df is None or price_df.empty or "close" not in price_df.columns:
        return pd.DataFrame()

    h_key = horizon.lower()
    shift_periods = HORIZON_TRADING_DAYS.get(h_key, 21)

    res = pd.DataFrame(index=price_df.index)
    close = price_df["close"].astype(float)

    # Future price shifted backwards to align target with current observation timestamp
    future_close = close.shift(-shift_periods)
    
    # 1. Target Future Return
    target_ret = (future_close - close) / close.replace(0, np.nan)
    res[f"target_return_{h_key}"] = target_ret

    # 2. Target Direction (Binary classification: 1 = Positive return, 0 = Non-positive)
    res[f"target_direction_{h_key}"] = np.where(target_ret > (return_threshold_pct / 100.0), 1, 0)
    # Set trailing NaN for rows without future data
    res.loc[future_close.isna(), f"target_direction_{h_key}"] = np.nan

    # 3. Target Future Realized Volatility
    log_ret = np.log(close / close.shift(1).replace(0, np.nan))
    # Rolling forward std
    future_vol = (
        log_ret.iloc[::-1]
        .rolling(shift_periods, min_periods=max(3, shift_periods // 3))
        .std()
        .iloc[::-1]
        * np.sqrt(252)
        * 100.0
    )
    res[f"target_volatility_{h_key}"] = future_vol

    return res
