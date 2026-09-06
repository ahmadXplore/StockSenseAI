"""
StockSense AI — Market Benchmark & Relative Strength Features
Calculates beta, correlation, excess returns, and relative strength vs benchmark.
"""

from __future__ import annotations
import numpy as np
import pandas as pd
from app.features.base import BaseFeatureExtractor, FeatureMetadata, FeatureCategory, FeatureContext
from app.features.registry import feature_registry


BENCHMARK_DEFAULTS = {
    "PK": "KSE100",
    "US": "SPY",
    "GB": "FTSE100",
    "JP": "N225",
    "HK": "HSI",
    "IN": "NIFTY50",
}


class MarketRelativeFeatureExtractor(BaseFeatureExtractor):
    def __init__(self):
        super().__init__(
            FeatureMetadata(
                name="market_relative",
                category=FeatureCategory.MARKET,
                description="Beta, correlation, and excess return vs market benchmark",
                lookback_periods=60,
                required_columns=["close"],
                version="1.0.0"
            )
        )

    def compute(self, context: FeatureContext) -> pd.DataFrame:
        df = context.price_df
        if not self.validate_inputs(df):
            return pd.DataFrame()

        res = pd.DataFrame(index=df.index)
        stock_ret = df["close"].astype(float).pct_change()

        bench_df = context.benchmark_df
        if bench_df is not None and not bench_df.empty and "close" in bench_df.columns:
            bench_ret = bench_df["close"].astype(float).pct_change().reindex(df.index)
        else:
            # Neutral fallback if benchmark not provided
            bench_ret = pd.Series(0.0, index=df.index)

        # 1. Excess Returns
        res["excess_return_1d"] = stock_ret - bench_ret
        res["excess_return_21d"] = df["close"].astype(float).pct_change(21) - bench_ret.rolling(21, min_periods=5).sum()

        # 2. Rolling Beta & Correlation (60D)
        cov_60d = stock_ret.rolling(60, min_periods=20).cov(bench_ret)
        bench_var_60d = bench_ret.rolling(60, min_periods=20).var().replace(0, np.nan)
        res["rolling_beta_60d"] = (cov_60d / bench_var_60d).fillna(1.0)
        res["rolling_correlation_60d"] = stock_ret.rolling(60, min_periods=20).corr(bench_ret).fillna(0.5)

        # 3. Relative Strength Indicator (Stock 21D Return - Benchmark 21D Return)
        res["relative_strength_21d"] = res["excess_return_21d"]

        return res


market_relative_extractor = MarketRelativeFeatureExtractor()
feature_registry.register(market_relative_extractor)
