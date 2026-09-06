"""
Unit Tests for Feature Versioning & Configuration Hashes
"""

import pytest
from app.features.versioning import FeatureVersionConfig
from app.features.registry import feature_registry


def test_feature_version_config_hashing():
    cfg1 = FeatureVersionConfig(
        feature_set_id="US_NASDAQ_AAPL",
        version="1.0.0",
        feature_names=["sma_20", "rsi_14", "atr_14"],
        extractor_parameters={"lookback": 20}
    )

    cfg2 = FeatureVersionConfig(
        feature_set_id="US_NASDAQ_AAPL",
        version="1.0.0",
        feature_names=["rsi_14", "sma_20", "atr_14"], # Same features, different order
        extractor_parameters={"lookback": 20}
    )

    cfg3 = FeatureVersionConfig(
        feature_set_id="US_NASDAQ_AAPL",
        version="2.0.0", # Different version
        feature_names=["sma_20", "rsi_14"],
        extractor_parameters={"lookback": 50}
    )

    # Order-independent deterministic hash
    assert cfg1.config_hash == cfg2.config_hash
    assert cfg1.config_hash != cfg3.config_hash


def test_feature_registry_lookup():
    extractors = feature_registry.list_extractors()
    assert len(extractors) >= 5

    trend = feature_registry.get_extractor("technical_trend")
    assert trend is not None
    assert trend.metadata.name == "technical_trend"
