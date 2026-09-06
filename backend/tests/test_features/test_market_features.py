"""
Unit Tests for Market Relative & Cross-Sectional Features
"""

import pytest
import pandas as pd
import numpy as np
from app.features.base import FeatureContext
from app.features.market.relative_strength import MarketRelativeFeatureExtractor
from app.features.market.cross_sectional import CrossSectionalFeatureExtractor


def test_market_relative_features():
    dates = pd.date_range("2024-01-01", periods=80, freq="B")
    stock_p = pd.DataFrame({"close": 100.0 + np.cumsum(np.random.randn(80) * 2.0)}, index=dates)
    bench_p = pd.DataFrame({"close": 400.0 + np.cumsum(np.random.randn(80) * 1.0)}, index=dates)

    ctx = FeatureContext("US.NASDAQ.AAPL", "AAPL", "US", "NASDAQ", price_df=stock_p, benchmark_df=bench_p)
    extractor = MarketRelativeFeatureExtractor()
    df = extractor.compute(ctx)

    assert "excess_return_1d" in df.columns
    assert "rolling_beta_60d" in df.columns
    assert "rolling_correlation_60d" in df.columns
    assert len(df) == 80


def test_cross_sectional_features():
    dates = pd.date_range("2024-01-01", periods=30, freq="B")
    stock_p = pd.DataFrame({"close": [100.0] * 30}, index=dates)

    ctx = FeatureContext("PK.PSX.ENGRO", "ENGRO", "PK", "PSX", price_df=stock_p)
    extractor = CrossSectionalFeatureExtractor()
    df = extractor.compute(ctx)

    assert "cross_sectional_mom_rank_21d" in df.columns
    assert (df["cross_sectional_mom_rank_21d"] >= 0.0).all()
