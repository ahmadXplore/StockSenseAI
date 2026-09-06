"""
StockSense AI — Price Gaps & Candle Structure Features
Calculates overnight gap %, intraday session returns, and body-to-shadow ratios.
"""

from __future__ import annotations
import numpy as np
import pandas as pd
from app.features.base import BaseFeatureExtractor, FeatureMetadata, FeatureCategory, FeatureContext
from app.features.registry import feature_registry


class PriceGapsFeatureExtractor(BaseFeatureExtractor):
    def __init__(self):
        super().__init__(
            FeatureMetadata(
                name="price_gaps",
                category=FeatureCategory.PRICE,
                description="Overnight gap %, intraday move %, candle body-to-range ratios",
                lookback_periods=20,
                required_columns=["open", "high", "low", "close"],
                version="1.0.0"
            )
        )

    def compute(self, context: FeatureContext) -> pd.DataFrame:
        df = context.price_df
        if not self.validate_inputs(df):
            return pd.DataFrame()

        res = pd.DataFrame(index=df.index)
        open_p = df["open"].astype(float)
        high = df["high"].astype(float)
        low = df["low"].astype(float)
        close = df["close"].astype(float)
        prev_close = close.shift(1)

        # 1. Overnight Gap %: (Open_t - Close_{t-1}) / Close_{t-1}
        res["gap_pct"] = ((open_p - prev_close) / prev_close.replace(0, np.nan)) * 100.0

        # 2. Intraday Session Return %: (Close_t - Open_t) / Open_t
        res["intraday_return_pct"] = ((close - open_p) / open_p.replace(0, np.nan)) * 100.0

        # 3. High-Low Candle Range %: (High_t - Low_t) / Close_{t-1}
        res["high_low_range_pct"] = ((high - low) / prev_close.replace(0, np.nan)) * 100.0

        # 4. Upper Shadow and Lower Shadow Ratios
        body = (close - open_p).abs()
        total_range = (high - low).replace(0, np.nan)
        res["body_to_range_ratio"] = body / total_range
        res["upper_shadow_ratio"] = (high - np.maximum(open_p, close)) / total_range
        res["lower_shadow_ratio"] = (np.minimum(open_p, close) - low) / total_range

        return res


price_gaps_extractor = PriceGapsFeatureExtractor()
feature_registry.register(price_gaps_extractor)
