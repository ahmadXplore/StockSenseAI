"""
StockSense AI — Feature Missingness & Imputation Utility
Analyzes missing value rates and applies safe forward-fill or median imputations.
"""

from __future__ import annotations
import numpy as np
import pandas as pd
from typing import Tuple, Dict, Any


def impute_features_safely(
    df: pd.DataFrame,
    max_allowed_missing_ratio: float = 0.50
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Cleans and imputes missing feature values:
    1. Drops columns exceeding max_allowed_missing_ratio (default 50%).
    2. Applies forward-fill (carrying past values forward).
    3. Fills remaining leading NaNs with column medians or 0.0.
    """
    if df is None or df.empty:
        return df, {"dropped_columns": [], "missing_stats": {}}

    missing_ratios = df.isna().mean()
    dropped_cols = list(missing_ratios[missing_ratios > max_allowed_missing_ratio].index)
    
    cleaned = df.drop(columns=dropped_cols)

    # Replace infinities with NaN for consistent imputation
    cleaned = cleaned.replace([np.inf, -np.inf], np.nan)

    # Forward fill time-series observations
    imputed = cleaned.ffill()

    # Fill remaining NaNs with median of each column or 0.0
    for col in imputed.columns:
        if np.issubdtype(imputed[col].dtype, np.number):
            med = imputed[col].median()
            val = med if (not np.isnan(med) and not np.isinf(med)) else 0.0
            imputed[col] = imputed[col].fillna(val)
        else:
            imputed[col] = imputed[col].fillna(0.0)

    # Final sweep replacing any residual infs or nans
    imputed = imputed.replace([np.inf, -np.inf], 0.0).fillna(0.0)

    stats = {
        "initial_columns": len(df.columns),
        "kept_columns": len(imputed.columns),
        "dropped_columns": dropped_cols,
        "max_missing_ratio": float(missing_ratios.max()) if not missing_ratios.empty else 0.0
    }

    return imputed, stats
