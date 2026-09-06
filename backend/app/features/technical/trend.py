"""
StockSense AI — Technical Trend Features
Calculates SMA, EMA, WMA, MACD, ADX, Aroon, moving-average ratios and slopes.
"""

from __future__ import annotations
import numpy as np
import pandas as pd
from app.features.base import BaseFeatureExtractor, FeatureMetadata, FeatureCategory, FeatureContext


class TrendFeatureExtractor(BaseFeatureExtractor):
    def __init__(self):
        super().__init__(
            FeatureMetadata(
                name="technical_trend",
                category=FeatureCategory.TECHNICAL,
                description="Moving averages, MACD, ADX, Aroon, and trend slopes",
                lookback_periods=200,
                required_columns=["close", "high", "low"],
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

        # 1. Simple Moving Averages
        res["sma_20"] = close.rolling(window=20, min_periods=5).mean()
        res["sma_50"] = close.rolling(window=50, min_periods=10).mean()
        res["sma_200"] = close.rolling(window=200, min_periods=20).mean()

        # 2. Exponential Moving Averages
        res["ema_12"] = close.ewm(span=12, adjust=False).mean()
        res["ema_26"] = close.ewm(span=26, adjust=False).mean()

        # 3. Weighted Moving Average (20)
        weights_20 = np.arange(1, 21)
        res["wma_20"] = close.rolling(20, min_periods=5).apply(
            lambda prices: np.dot(prices, weights_20[-len(prices):]) / weights_20[-len(prices):].sum(),
            raw=True
        )

        # 4. MACD
        res["macd_line"] = res["ema_12"] - res["ema_26"]
        res["macd_signal"] = res["macd_line"].ewm(span=9, adjust=False).mean()
        res["macd_histogram"] = res["macd_line"] - res["macd_signal"]

        # 5. Price to Moving Average Ratios
        res["price_to_sma20"] = close / res["sma_20"]
        res["price_to_sma50"] = close / res["sma_50"]
        res["price_to_sma200"] = close / res["sma_200"]
        res["sma20_to_sma50"] = res["sma_20"] / res["sma_50"]

        # 6. Moving Average Slopes (5-day return of SMA)
        res["sma20_slope_5d"] = res["sma_20"].pct_change(5)
        res["sma50_slope_5d"] = res["sma_50"].pct_change(5)

        # 7. Aroon Indicator (25 periods)
        rolling_high_idx = high.rolling(25, min_periods=5).apply(lambda s: float(np.argmax(s)), raw=True)
        rolling_low_idx = low.rolling(25, min_periods=5).apply(lambda s: float(np.argmin(s)), raw=True)
        res["aroon_up"] = (rolling_high_idx / 25.0) * 100.0
        res["aroon_down"] = (rolling_low_idx / 25.0) * 100.0
        res["aroon_oscillator"] = res["aroon_up"] - res["aroon_down"]

        # 8. ADX (Average Directional Index - 14 periods)
        tr1 = high - low
        tr2 = (high - close.shift(1)).abs()
        tr3 = (low - close.shift(1)).abs()
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr_14 = tr.rolling(14, min_periods=5).mean()

        up_move = high - high.shift(1)
        down_move = low.shift(1) - low
        plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
        minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)

        plus_di = 100.0 * (pd.Series(plus_dm, index=df.index).rolling(14, min_periods=5).mean() / atr_14)
        minus_di = 100.0 * (pd.Series(minus_dm, index=df.index).rolling(14, min_periods=5).mean() / atr_14)
        dx = 100.0 * ((plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan))
        res["adx_14"] = dx.rolling(14, min_periods=5).mean().fillna(0.0)
        res["plus_di_14"] = plus_di.fillna(0.0)
        res["minus_di_14"] = minus_di.fillna(0.0)

        return res
