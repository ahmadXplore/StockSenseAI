"""
StockSense AI — Cross-Sectional Ranking Features
Calculates cross-sectional momentum and volatility ranks within a universe.
"""

from __future__ import annotations
import numpy as np
import pandas as pd
from app.features.base import BaseFeatureExtractor, FeatureMetadata, FeatureCategory, FeatureContext
from app.features.registry import feature_registry


class CrossSectionalFeatureExtractor(BaseFeatureExtractor):
    def __init__(self):
        super().__init__(
            FeatureMetadata(
                name="market_cross_sectional",
                category=FeatureCategory.CROSS_SECTIONAL,
                description="Cross-sectional momentum and volatility percentile rankings",
                lookback_periods=21,
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
        ret_21d = close.pct_change(21)

        universe_prices = context.universe_prices
        if universe_prices and len(universe_prices) > 1:
            # Calculate rank across universe at each timestamp
            ranks = []
            for dt in df.index:
                universe_returns = []
                for sym, u_df in universe_prices.items():
                    if dt in u_df.index and "close" in u_df.columns:
                        try:
                            loc = u_df.index.get_loc(dt)
                            if loc >= 21:
                                r = (u_df["close"].iloc[loc] - u_df["close"].iloc[loc - 21]) / u_df["close"].iloc[loc - 21]
                                universe_returns.append(r)
                        except Exception:
                            continue
                
                if universe_returns:
                    curr_r = ret_21d.loc[dt] if dt in ret_21d.index else 0.0
                    pct_rank = (pd.Series(universe_returns) <= curr_r).mean() * 100.0
                    ranks.append(pct_rank)
                else:
                    ranks.append(50.0)
            res["cross_sectional_mom_rank_21d"] = ranks
        else:
            # Baseline neutral rank (50th percentile)
            res["cross_sectional_mom_rank_21d"] = 50.0

        return res


cross_sectional_extractor = CrossSectionalFeatureExtractor()
feature_registry.register(cross_sectional_extractor)
