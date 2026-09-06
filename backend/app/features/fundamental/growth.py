"""
StockSense AI — Fundamental Features Suite
Extracts growth, profitability, leverage, and valuation features with strict point-in-time safety.
"""

from __future__ import annotations
import numpy as np
import pandas as pd
from datetime import date
from typing import Optional
from app.features.base import BaseFeatureExtractor, FeatureMetadata, FeatureCategory, FeatureContext
from app.features.registry import feature_registry
from app.features.fundamental.point_in_time import filter_fundamentals_point_in_time


class FundamentalFeaturesExtractor(BaseFeatureExtractor):
    def __init__(self):
        super().__init__(
            FeatureMetadata(
                name="fundamental_features",
                category=FeatureCategory.FUNDAMENTAL,
                description="Point-in-time financial ratios: growth, profitability, leverage, valuation",
                lookback_periods=4,
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

        # Baseline default fundamental features
        res["revenue_growth_yoy"] = np.nan
        res["net_income_growth_yoy"] = np.nan
        res["roe"] = np.nan
        res["roa"] = np.nan
        res["gross_margin"] = np.nan
        res["operating_margin"] = np.nan
        res["net_margin"] = np.nan
        res["debt_to_equity"] = np.nan
        res["current_ratio"] = np.nan
        res["pe_ratio"] = np.nan
        res["pb_ratio"] = np.nan

        f_df = context.fundamentals_df
        if f_df is None or f_df.empty:
            return res

        # For each row in price_df, resolve point-in-time fundamentals
        for idx in p_df.index:
            row_date = idx.date() if hasattr(idx, "date") else idx
            if not isinstance(row_date, date):
                try:
                    row_date = pd.to_datetime(idx).date()
                except Exception:
                    continue

            # Point-in-time filter
            pit_f = filter_fundamentals_point_in_time(f_df, as_of_date=row_date)
            if pit_f is None or pit_f.empty:
                continue

            # Pick latest available statement
            latest = pit_f.iloc[-1]
            res.loc[idx, "roe"] = latest.get("roe", np.nan)
            res.loc[idx, "roa"] = latest.get("roa", np.nan)
            res.loc[idx, "gross_margin"] = latest.get("gross_margin", np.nan)
            res.loc[idx, "operating_margin"] = latest.get("operating_margin", np.nan)
            res.loc[idx, "net_margin"] = latest.get("net_margin", np.nan)
            res.loc[idx, "debt_to_equity"] = latest.get("debt_to_equity", np.nan)
            res.loc[idx, "current_ratio"] = latest.get("current_ratio", np.nan)
            res.loc[idx, "pe_ratio"] = latest.get("pe_ratio", np.nan)
            res.loc[idx, "pb_ratio"] = latest.get("pb_ratio", np.nan)
            res.loc[idx, "revenue_growth_yoy"] = latest.get("revenue_growth", np.nan)
            res.loc[idx, "net_income_growth_yoy"] = latest.get("net_income_growth", np.nan)

        return res


fundamental_extractor = FundamentalFeaturesExtractor()
feature_registry.register(fundamental_extractor)
