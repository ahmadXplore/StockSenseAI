"""
Unit Tests for Technical Features (Trend, Momentum, Volatility, Volume)
"""

import pytest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from app.features.base import FeatureContext
from app.features.technical.trend import TrendFeatureExtractor
from app.features.technical.momentum import MomentumFeatureExtractor
from app.features.technical.volatility import VolatilityFeatureExtractor
from app.features.technical.volume import VolumeFeatureExtractor
from app.features.technical.indicators import ComprehensiveTechnicalExtractor


@pytest.fixture
def sample_price_df():
    dates = pd.date_range("2024-01-01", periods=100, freq="B")
    np.random.seed(42)
    close = 100.0 + np.cumsum(np.random.randn(100) * 1.5)
    high = close + np.random.uniform(0.5, 2.0, 100)
    low = close - np.random.uniform(0.5, 2.0, 100)
    open_p = (high + low) / 2.0
    volume = np.random.randint(100000, 500000, 100)
    return pd.DataFrame({
        "open": open_p, "high": high, "low": low, "close": close, "volume": volume
    }, index=dates)


def test_trend_features(sample_price_df):
    ctx = FeatureContext("US.NASDAQ.AAPL", "AAPL", "US", "NASDAQ", price_df=sample_price_df)
    extractor = TrendFeatureExtractor()
    df = extractor.compute(ctx)

    assert "sma_20" in df.columns
    assert "sma_50" in df.columns
    assert "macd_line" in df.columns
    assert "macd_signal" in df.columns
    assert "adx_14" in df.columns
    assert "aroon_oscillator" in df.columns
    assert len(df) == 100


def test_momentum_features(sample_price_df):
    ctx = FeatureContext("PK.PSX.ENGRO", "ENGRO", "PK", "PSX", price_df=sample_price_df)
    extractor = MomentumFeatureExtractor()
    df = extractor.compute(ctx)

    assert "rsi_14" in df.columns
    assert "stoch_k_14" in df.columns
    assert "williams_r_14" in df.columns
    assert "roc_10" in df.columns
    assert "mfi_14" in df.columns
    # RSI bounded in [0, 100]
    assert (df["rsi_14"] >= 0.0).all() and (df["rsi_14"] <= 100.0).all()


def test_volatility_features(sample_price_df):
    ctx = FeatureContext("US.NASDAQ.AAPL", "AAPL", "US", "NASDAQ", price_df=sample_price_df)
    extractor = VolatilityFeatureExtractor()
    df = extractor.compute(ctx)

    assert "atr_14" in df.columns
    assert "bb_upper" in df.columns
    assert "bb_lower" in df.columns
    assert "realized_vol_20d" in df.columns
    assert "parkinson_vol_20d" in df.columns
    assert (df["atr_14"].dropna() > 0).all()


def test_volume_features(sample_price_df):
    ctx = FeatureContext("PK.PSX.ENGRO", "ENGRO", "PK", "PSX", price_df=sample_price_df)
    extractor = VolumeFeatureExtractor()
    df = extractor.compute(ctx)

    assert "volume_sma_20" in df.columns
    assert "relative_volume_20d" in df.columns
    assert "obv" in df.columns


def test_comprehensive_technical_extractor(sample_price_df):
    ctx = FeatureContext("US.NASDAQ.AAPL", "AAPL", "US", "NASDAQ", price_df=sample_price_df)
    extractor = ComprehensiveTechnicalExtractor()
    df = extractor.compute(ctx)

    assert len(df.columns) >= 20
    assert "sma_20" in df.columns
    assert "rsi_14" in df.columns
    assert "atr_14" in df.columns
    assert "relative_volume_20d" in df.columns
