"""
StockSense AI — 52-Week Range & Price Extremes Features
Calculates distance from 52-week high, 52-week low, and channel percentile positions.
"""

from __future__ import annotations
import numpy as np
import pandas as pd
from app.features.base import BaseFeatureExtractor, FeatureMetadata, FeatureCategory, FeatureContext
from app.features.registry import feature_registry


class PriceRangesFeatureExtractor(BaseFeatureExtractor):
    def __init__(self):
        super().__init__(
            FeatureMetadata(
                name="price_ranges",
                category=FeatureCategory.PRICE,
                description="52-week high/low distances, channel position, and breakout indicators",
                lookback_periods=252,
                required_columns=["high", "low", "close"],
                version="1.0.0"
            )
        )

    def compute(self, context: FeatureContext) -> pd.DataFrame:
        df = context.price_df
        if not self.validate_inputs(df):
            return pd.DataFrame()

        res = pd.DataFrame(index=df.index)
        high = df["high"].astype(float)
        low = df["low"].astype(float)
        close = df["close"].astype(float)

        # 1. 52-week High and Low (252 periods)
        rolling_high_252 = high.rolling(252, min_periods=20).max()
        rolling_low_252 = low.rolling(252, min_periods=20).min()

        # 2. Distances from 52-week High & Low (%)
        res["dist_from_52w_high_pct"] = ((close - rolling_high_252) / rolling_high_252.replace(0, np.nan)) * 100.0
        res["dist_from_52w_low_pct"] = ((close - rolling_low_252) / rolling_low_252.replace(0, np.nan)) * 100.0

        # 3. Position within 52-week Range [0.0 = at low, 1.0 = at high]
        range_52w = (rolling_high_252 - rolling_low_252).replace(0, np.nan)
        res["pos_in_52w_range"] = (close - rolling_low_252) / range_52w
        res["pos_in_52w_range"] = res["pos_in_52w_range"].fillna(0.5)

        # 4. Donchian Channel (20D)
        res["donchian_high_20d"] = high.rolling(20, min_periods=5).max()
        res["donchian_low_20d"] = low.rolling(20, min_periods=5).min()
        res["donchian_channel_pos_20d"] = (close - res["donchian_low_20d"]) / (res["donchian_high_20d"] - res["donchian_low_20d"]).replace(0, np.nan)

        return res


price_ranges_extractor = PriceRangesFeatureExtractor()
feature_registry.register(price_ranges_extractor)
