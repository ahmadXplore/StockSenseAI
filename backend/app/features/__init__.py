"""
StockSense AI — Master Feature Engineering Exports
"""

from app.features.base import (
    BaseFeatureExtractor, FeatureMetadata, FeatureCategory, FeatureContext
)
from app.features.registry import FeatureRegistry, feature_registry
from app.features.versioning import FeatureVersionConfig
from app.features.pipeline import FeaturePipeline, feature_pipeline
from app.features.technical import (
    TrendFeatureExtractor, MomentumFeatureExtractor,
    VolatilityFeatureExtractor, VolumeFeatureExtractor, ComprehensiveTechnicalExtractor
)
from app.features.price import (
    PriceReturnsFeatureExtractor, PriceGapsFeatureExtractor, PriceRangesFeatureExtractor
)
from app.features.fundamental import (
    FundamentalFeaturesExtractor, filter_fundamentals_point_in_time
)
from app.features.market import (
    MarketRelativeFeatureExtractor, CrossSectionalFeatureExtractor
)
from app.features.macro import MacroRegimeFeatureExtractor
from app.features.sentiment import NewsSentimentFeatureExtractor
from app.features.validation import (
    LeakageCheckResult, check_feature_matrix_leakage, impute_features_safely
)

__all__ = [
    "BaseFeatureExtractor",
    "FeatureMetadata",
    "FeatureCategory",
    "FeatureContext",
    "FeatureRegistry",
    "feature_registry",
    "FeatureVersionConfig",
    "FeaturePipeline",
    "feature_pipeline",
    "TrendFeatureExtractor",
    "MomentumFeatureExtractor",
    "VolatilityFeatureExtractor",
    "VolumeFeatureExtractor",
    "ComprehensiveTechnicalExtractor",
    "PriceReturnsFeatureExtractor",
    "PriceGapsFeatureExtractor",
    "PriceRangesFeatureExtractor",
    "FundamentalFeaturesExtractor",
    "filter_fundamentals_point_in_time",
    "MarketRelativeFeatureExtractor",
    "CrossSectionalFeatureExtractor",
    "MacroRegimeFeatureExtractor",
    "NewsSentimentFeatureExtractor",
    "LeakageCheckResult",
    "check_feature_matrix_leakage",
    "impute_features_safely",
]
