"""
StockSense AI — Price Returns Features
Calculates multi-timeframe log returns, rolling momentum, and cumulative returns.
"""

from __future__ import annotations
import numpy as np
import pandas as pd
from app.features.base import BaseFeatureExtractor, FeatureMetadata, FeatureCategory, FeatureContext
from app.features.registry import feature_registry


class PriceReturnsFeatureExtractor(BaseFeatureExtractor):
    def __init__(self):
        super().__init__(
            FeatureMetadata(
                name="price_returns",
                category=FeatureCategory.PRICE,
                description="Log returns and rolling returns (1D, 5D, 10D, 21D, 63D)",
                lookback_periods=63,
                required_columns=["close"],
                version="1.0.0"
            )
        )

    def compute(self, context: FeatureContext) -> pd.DataFrame:
        df = context.price_df
        if not self.validate_inputs(df):
            return pd.DataFrame()

        res = pd.DataFrame(index=df.index)
        close = df["close"].astype(float)

        # 1. Log Returns
        log_ret_1d = np.log(close / close.shift(1).replace(0, np.nan))
        res["log_return_1d"] = log_ret_1d
        res["log_return_5d"] = np.log(close / close.shift(5).replace(0, np.nan))
        res["log_return_10d"] = np.log(close / close.shift(10).replace(0, np.nan))
        res["log_return_21d"] = np.log(close / close.shift(21).replace(0, np.nan))
        res["log_return_63d"] = np.log(close / close.shift(63).replace(0, np.nan))

        # 2. Arithmetic Percentage Returns
        res["return_1d_pct"] = close.pct_change(1) * 100.0
        res["return_5d_pct"] = close.pct_change(5) * 100.0
        res["return_21d_pct"] = close.pct_change(21) * 100.0

        # 3. Rolling Skewness and Kurtosis (60D)
        res["returns_skew_60d"] = log_ret_1d.rolling(60, min_periods=20).skew()
        res["returns_kurt_60d"] = log_ret_1d.rolling(60, min_periods=20).kurt()

        return res


price_returns_extractor = PriceReturnsFeatureExtractor()
feature_registry.register(price_returns_extractor)
