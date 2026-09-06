"""
StockSense AI — Technical Volatility Features
Calculates ATR, Bollinger Bands, Realized Volatility, Parkinson Volatility, and Garman-Klass.
"""

from __future__ import annotations
import numpy as np
import pandas as pd
from app.features.base import BaseFeatureExtractor, FeatureMetadata, FeatureCategory, FeatureContext


class VolatilityFeatureExtractor(BaseFeatureExtractor):
    def __init__(self):
        super().__init__(
            FeatureMetadata(
                name="technical_volatility",
                category=FeatureCategory.TECHNICAL,
                description="ATR, Bollinger Bands, Realized Vol, Parkinson & Garman-Klass",
                lookback_periods=252,
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
        close = df["close"].astype(float)
        high = df["high"].astype(float)
        low = df["low"].astype(float)

        # 1. Average True Range (ATR 14)
        tr1 = high - low
        tr2 = (high - close.shift(1)).abs()
        tr3 = (low - close.shift(1)).abs()
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        res["atr_14"] = tr.rolling(14, min_periods=5).mean()
        res["natr_14"] = (res["atr_14"] / close.replace(0, np.nan)) * 100.0

        # 2. Bollinger Bands (20, 2 std)
        bb_middle = close.rolling(20, min_periods=5).mean()
        bb_std = close.rolling(20, min_periods=5).std()
        res["bb_upper"] = bb_middle + (2.0 * bb_std)
        res["bb_middle"] = bb_middle
        res["bb_lower"] = bb_middle - (2.0 * bb_std)
        res["bb_width"] = (res["bb_upper"] - res["bb_lower"]) / bb_middle.replace(0, np.nan)
        res["bb_pct_b"] = (close - res["bb_lower"]) / (res["bb_upper"] - res["bb_lower"]).replace(0, np.nan)

        # 3. Realized Volatility (Annualized rolling std of log returns: 20D, 60D)
        log_ret = np.log(close / close.shift(1).replace(0, np.nan))
        res["realized_vol_20d"] = log_ret.rolling(20, min_periods=5).std() * np.sqrt(252) * 100.0
        res["realized_vol_60d"] = log_ret.rolling(60, min_periods=10).std() * np.sqrt(252) * 100.0

        # 4. Parkinson Volatility (20D): sqrt( 1/(4*ln(2)) * mean(ln(H/L)^2) ) * sqrt(252)
        hl_ratio = np.log(high / low.replace(0, np.nan))
        parkinson_var = (hl_ratio ** 2) / (4.0 * np.log(2))
        res["parkinson_vol_20d"] = np.sqrt(parkinson_var.rolling(20, min_periods=5).mean()) * np.sqrt(252) * 100.0

        # 5. Garman-Klass Volatility (20D)
        # GK = 0.5 * ln(H/L)^2 - (2*ln(2) - 1) * ln(C/O)^2
        co_ratio = np.log(close / open_p.replace(0, np.nan))
        gk_var = 0.5 * (hl_ratio ** 2) - (2.0 * np.log(2) - 1.0) * (co_ratio ** 2)
        res["garman_klass_vol_20d"] = np.sqrt(np.maximum(0.0, gk_var.rolling(20, min_periods=5).mean())) * np.sqrt(252) * 100.0

        # 6. 252-day Volatility Percentile Rank
        res["volatility_percentile_252d"] = res["realized_vol_20d"].rolling(252, min_periods=20).apply(
            lambda s: pd.Series(s).rank(pct=True).iloc[-1] * 100.0 if len(s) > 0 else 50.0,
            raw=False
        )

        return res
