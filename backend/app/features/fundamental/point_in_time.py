"""
StockSense AI — Point-in-Time Fundamental Statement Alignment Engine
Enforces strict 25-day mandatory filing lag and SEC EDGAR / PSX disclosure dates.
"""

from __future__ import annotations
import pandas as pd
import numpy as np
from datetime import date, datetime, timedelta
from typing import Optional


def filter_fundamentals_point_in_time(
    df: Optional[pd.DataFrame],
    as_of_date: date,
    default_filing_lag_days: int = 25
) -> Optional[pd.DataFrame]:
    """
    Filters a fundamentals DataFrame to exclude financial statements whose public filing date
    (or filing lag buffer) is strictly after as_of_date.

    Guarantees zero look-ahead leakage in historical backtests and feature matrices.
    """
    if df is None or df.empty:
        return None

    filtered_rows = []
    for _, row in df.iterrows():
        # Check explicit filing_date or data_available_date
        filing_dt = row.get("data_available_date") or row.get("filing_date")
        
        if filing_dt is not None:
            if isinstance(filing_dt, (datetime, pd.Timestamp)):
                filing_d = filing_dt.date()
            elif isinstance(filing_dt, str):
                filing_d = datetime.strptime(filing_dt.split(" ")[0], "%Y-%m-%d").date()
            else:
                filing_d = filing_dt
        else:
            # Fallback: Enforce mandatory 25-day reporting lag after period_end
            period_end = row.get("period_end") or row.get("fiscal_date") or row.get("date")
            if period_end is not None:
                if isinstance(period_end, (datetime, pd.Timestamp)):
                    p_end = period_end.date()
                elif isinstance(period_end, str):
                    p_end = datetime.strptime(period_end.split(" ")[0], "%Y-%m-%d").date()
                else:
                    p_end = period_end
                filing_d = p_end + timedelta(days=default_filing_lag_days)
            else:
                continue

        # Point-in-time gate
        if filing_d <= as_of_date:
            filtered_rows.append(row)

    if not filtered_rows:
        return pd.DataFrame()

    return pd.DataFrame(filtered_rows)
