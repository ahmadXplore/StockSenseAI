"""
StockSense AI — Consolidated Technical Indicators Suite
Wraps trend, momentum, volatility, and volume into a unified high-performance extractor.
"""

from __future__ import annotations
import pandas as pd
from app.features.base import BaseFeatureExtractor, FeatureMetadata, FeatureCategory, FeatureContext
from app.features.registry import feature_registry
from app.features.technical.trend import TrendFeatureExtractor
from app.features.technical.momentum import MomentumFeatureExtractor
from app.features.technical.volatility import VolatilityFeatureExtractor
from app.features.technical.volume import VolumeFeatureExtractor


class ComprehensiveTechnicalExtractor(BaseFeatureExtractor):
    """
    Consolidated technical indicator extractor that executes all technical sub-extractors.
    """

    def __init__(self):
        super().__init__(
            FeatureMetadata(
                name="technical_comprehensive",
                category=FeatureCategory.TECHNICAL,
                description="Complete technical indicator suite (trend, momentum, volatility, volume)",
                lookback_periods=252,
                required_columns=["open", "high", "low", "close", "volume"],
                version="1.0.0"
            )
        )
        self.trend = TrendFeatureExtractor()
        self.momentum = MomentumFeatureExtractor()
        self.volatility = VolatilityFeatureExtractor()
        self.volume = VolumeFeatureExtractor()

    def compute(self, context: FeatureContext) -> pd.DataFrame:
        df = context.price_df
        if not self.validate_inputs(df):
            return pd.DataFrame()

        t_df = self.trend.compute(context)
        m_df = self.momentum.compute(context)
        v_df = self.volatility.compute(context)
        vol_df = self.volume.compute(context)

        combined = pd.concat([t_df, m_df, v_df, vol_df], axis=1)
        return combined.loc[:, ~combined.columns.duplicated()]


# Register all technical extractors into global registry
trend_extractor = TrendFeatureExtractor()
momentum_extractor = MomentumFeatureExtractor()
volatility_extractor = VolatilityFeatureExtractor()
volume_extractor = VolumeFeatureExtractor()
technical_comprehensive_extractor = ComprehensiveTechnicalExtractor()

feature_registry.register(trend_extractor)
feature_registry.register(momentum_extractor)
feature_registry.register(volatility_extractor)
feature_registry.register(volume_extractor)
feature_registry.register(technical_comprehensive_extractor)
