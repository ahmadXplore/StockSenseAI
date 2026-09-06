"""
StockSense AI — Technical Momentum Features
Calculates RSI, Stochastic Oscillator, Williams %R, ROC, CCI, and MFI.
"""

from __future__ import annotations
import numpy as np
import pandas as pd
from app.features.base import BaseFeatureExtractor, FeatureMetadata, FeatureCategory, FeatureContext


class MomentumFeatureExtractor(BaseFeatureExtractor):
    def __init__(self):
        super().__init__(
            FeatureMetadata(
                name="technical_momentum",
                category=FeatureCategory.TECHNICAL,
                description="RSI, Stochastic, Williams %R, ROC, CCI, MFI",
                lookback_periods=30,
                required_columns=["close", "high", "low", "volume"],
                version="1.0.0"
            )
        )

    def compute(self, context: FeatureContext) -> pd.DataFrame:
        df = context.price_df
        if not self.validate_inputs(df):
            return pd.DataFrame()

        res = pd.DataFrame(index=df.index)
        close = df["close"].astype(float)
        high = df["high"].astype(float)
        low = df["low"].astype(float)
        volume = df["volume"].astype(float)

        # 1. RSI (14)
        delta = close.diff()
        gain = (delta.where(delta > 0, 0.0)).rolling(window=14, min_periods=5).mean()
        loss = (-delta.where(delta < 0, 0.0)).rolling(window=14, min_periods=5).mean()
        rs = gain / loss.replace(0, np.nan)
        res["rsi_14"] = 100.0 - (100.0 / (1.0 + rs))
        res["rsi_14"] = res["rsi_14"].fillna(50.0)

        # 2. Stochastic Oscillator (14, 3)
        lowest_low_14 = low.rolling(14, min_periods=5).min()
        highest_high_14 = high.rolling(14, min_periods=5).max()
        denom = (highest_high_14 - lowest_low_14).replace(0, np.nan)
        res["stoch_k_14"] = 100.0 * ((close - lowest_low_14) / denom)
        res["stoch_k_14"] = res["stoch_k_14"].fillna(50.0)
        res["stoch_d_3"] = res["stoch_k_14"].rolling(3, min_periods=1).mean()

        # 3. Williams %R (14)
        res["williams_r_14"] = -100.0 * ((highest_high_14 - close) / denom)
        res["williams_r_14"] = res["williams_r_14"].fillna(-50.0)

        # 4. Rate of Change (ROC 10, ROC 21)
        res["roc_10"] = close.pct_change(10) * 100.0
        res["roc_21"] = close.pct_change(21) * 100.0

        # 5. Commodity Channel Index (CCI 20)
        tp = (high + low + close) / 3.0
        tp_sma = tp.rolling(20, min_periods=5).mean()
        tp_mad = tp.rolling(20, min_periods=5).apply(lambda x: np.mean(np.abs(x - np.mean(x))), raw=True)
        res["cci_20"] = (tp - tp_sma) / (0.015 * tp_mad.replace(0, np.nan))
        res["cci_20"] = res["cci_20"].fillna(0.0)

        # 6. Money Flow Index (MFI 14)
        raw_money_flow = tp * volume
        pos_mf = np.where(tp > tp.shift(1), raw_money_flow, 0.0)
        neg_mf = np.where(tp < tp.shift(1), raw_money_flow, 0.0)
        pos_mf_sum = pd.Series(pos_mf, index=df.index).rolling(14, min_periods=5).sum()
        neg_mf_sum = pd.Series(neg_mf, index=df.index).rolling(14, min_periods=5).sum()
        mfr = pos_mf_sum / neg_mf_sum.replace(0, np.nan)
        res["mfi_14"] = 100.0 - (100.0 / (1.0 + mfr))
        res["mfi_14"] = res["mfi_14"].fillna(50.0)

        return res
