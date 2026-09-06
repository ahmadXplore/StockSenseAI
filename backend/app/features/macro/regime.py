"""
StockSense AI — Macroeconomic & Market Regime Features
Extracts interest rates, yield curve spread (10Y-2Y), VIX, inflation, and regime states.
"""

from __future__ import annotations
import numpy as np
import pandas as pd
from datetime import date
from typing import Optional
from app.features.base import BaseFeatureExtractor, FeatureMetadata, FeatureCategory, FeatureContext
from app.features.registry import feature_registry


class MacroRegimeFeatureExtractor(BaseFeatureExtractor):
    def __init__(self):
        super().__init__(
            FeatureMetadata(
                name="macro_regime",
                category=FeatureCategory.MACRO,
                description="Macro indicators: VIX, 10Y-2Y yield curve, Fed Funds / Policy rates, Inflation",
                lookback_periods=30,
                required_columns=[],
                version="1.0.0",
                is_point_in_time_safe=True
            )
        )

    def compute(self, context: FeatureContext) -> pd.DataFrame:
        p_df = context.price_df
        if p_df is None or p_df.empty:
            return pd.DataFrame()

        res = pd.DataFrame(index=p_df.index)

        # Baseline default macro values
        res["macro_vix_level"] = 18.0
        res["macro_yield_curve_10y2y"] = 0.50
        res["macro_rate_level"] = 5.25 if context.market_code == "US" else 19.5 # Policy rate baseline (US vs PK)
        res["macro_regime_is_bull"] = 1.0
        res["macro_regime_is_high_vol"] = 0.0

        macro_df = context.macro_df
        if macro_df is not None and not macro_df.empty:
            # Reindex macro values point-in-time to match price timestamps
            if "vix" in macro_df.columns:
                res["macro_vix_level"] = macro_df["vix"].reindex(p_df.index).ffill().fillna(18.0)
            if "yield_curve_10y2y" in macro_df.columns:
                res["macro_yield_curve_10y2y"] = macro_df["yield_curve_10y2y"].reindex(p_df.index).ffill().fillna(0.5)
            if "interest_rate" in macro_df.columns:
                res["macro_rate_level"] = macro_df["interest_rate"].reindex(p_df.index).ffill().fillna(5.0)

        # Classify regime
        res["macro_regime_is_high_vol"] = np.where(res["macro_vix_level"] > 25.0, 1.0, 0.0)
        res["macro_regime_is_bull"] = np.where(
            (res["macro_vix_level"] < 20.0) & (res["macro_yield_curve_10y2y"] > 0.0), 1.0, 0.0
        )

        return res


macro_regime_extractor = MacroRegimeFeatureExtractor()
feature_registry.register(macro_regime_extractor)
