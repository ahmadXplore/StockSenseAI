"""
StockSense AI — Technical Volume Features
Calculates Volume SMA, Relative Volume, OBV, and Volume Momentum.
"""

from __future__ import annotations
import numpy as np
import pandas as pd
from app.features.base import BaseFeatureExtractor, FeatureMetadata, FeatureCategory, FeatureContext


class VolumeFeatureExtractor(BaseFeatureExtractor):
    def __init__(self):
        super().__init__(
            FeatureMetadata(
                name="technical_volume",
                category=FeatureCategory.TECHNICAL,
                description="Volume SMA, Relative Volume, OBV, and Volume Momentum",
                lookback_periods=50,
                required_columns=["close", "volume"],
                version="1.0.0"
            )
        )

    def compute(self, context: FeatureContext) -> pd.DataFrame:
        df = context.price_df
        if not self.validate_inputs(df):
            return pd.DataFrame()

        res = pd.DataFrame(index=df.index)
        close = df["close"].astype(float)
        volume = df["volume"].astype(float)

        # 1. Volume Moving Averages
        res["volume_sma_20"] = volume.rolling(20, min_periods=5).mean()
        res["volume_sma_50"] = volume.rolling(50, min_periods=10).mean()

        # 2. Relative Volume (RVOL)
        res["relative_volume_20d"] = volume / res["volume_sma_20"].replace(0, np.nan)
        res["relative_volume_20d"] = res["relative_volume_20d"].fillna(1.0)

        # 3. On-Balance Volume (OBV)
        direction = np.sign(close.diff().fillna(0.0))
        res["obv"] = (direction * volume).cumsum()
        res["obv_ema_20"] = res["obv"].ewm(span=20, adjust=False).mean()
        res["obv_slope_5d"] = res["obv"].pct_change(5)

        # 4. Volume Momentum (5D & 10D change)
        res["volume_mom_5d"] = volume.pct_change(5)
        res["volume_mom_10d"] = volume.pct_change(10)

        return res
