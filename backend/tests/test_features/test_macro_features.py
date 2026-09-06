"""
Unit Tests for Macroeconomic & Sentiment Features
Verifies Section 42: Future news published after as_of_date is never leaked.
"""

import pytest
import pandas as pd
from datetime import date, datetime
from app.features.base import FeatureContext
from app.features.macro.regime import MacroRegimeFeatureExtractor
from app.features.sentiment.news_sentiment import NewsSentimentFeatureExtractor


def test_macro_regime_features():
    dates = pd.date_range("2024-01-01", periods=10, freq="B")
    p_df = pd.DataFrame({"close": [100.0] * 10}, index=dates)
    macro_df = pd.DataFrame({
        "vix": [15.5] * 10,
        "yield_curve_10y2y": [0.45] * 10,
        "interest_rate": [5.25] * 10
    }, index=dates)

    ctx = FeatureContext("US.NASDAQ.AAPL", "AAPL", "US", "NASDAQ", price_df=p_df, macro_df=macro_df)
    extractor = MacroRegimeFeatureExtractor()
    res = extractor.compute(ctx)

    assert "macro_vix_level" in res.columns
    assert "macro_regime_is_bull" in res.columns
    assert (res["macro_vix_level"] == 15.5).all()


def test_future_news_sentiment_leakage_protection():
    """
    CRITICAL FUTURE-NEWS TEST:
    Prediction date: 2024-04-15
    News 1: published_at = 2024-04-10 (sentiment = +0.8) -> VISIBLE
    News 2: published_at = 2024-04-20 (sentiment = -0.9) -> MUST NOT BE VISIBLE
    """
    dates = pd.date_range("2024-04-10", "2024-04-16", freq="B")
    p_df = pd.DataFrame({"close": [100.0] * len(dates)}, index=dates)

    news_df = pd.DataFrame([
        {
            "published_at": pd.Timestamp("2024-04-10"),
            "sentiment_score": 0.8
        },
        {
            "published_at": pd.Timestamp("2024-04-20"), # Future news
            "sentiment_score": -0.9
        }
    ])

    ctx = FeatureContext("PK.PSX.ENGRO", "ENGRO", "PK", "PSX", price_df=p_df, news_df=news_df)
    extractor = NewsSentimentFeatureExtractor()
    res = extractor.compute(ctx)

    # For all dates in April 10-16, sentiment_score_7d should be positive (+0.8), never -0.9
    assert (res["sentiment_score_7d"] >= 0.0).all()
