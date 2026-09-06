"""
Unit Tests for Fundamental Features & Point-in-Time Protection
Verifies Section 4 & Section 41: Disclosures after prediction date must NOT be visible.
"""

import pytest
import pandas as pd
from datetime import date
from app.features.base import FeatureContext
from app.features.fundamental.point_in_time import filter_fundamentals_point_in_time
from app.features.fundamental.growth import FundamentalFeaturesExtractor


def test_point_in_time_fundamental_filtering():
    """
    CRITICAL LOOK-AHEAD TEST:
    Prediction date: 2024-04-15
    Statement 1: period_end = 2023-12-31, data_available_date = 2024-02-15 (AVAILABLE)
    Statement 2: period_end = 2024-03-31, data_available_date = 2024-04-25 (UNAVAILABLE)
    """
    raw_statements = pd.DataFrame([
        {
            "period_end": date(2023, 12, 31),
            "data_available_date": date(2024, 2, 15),
            "roe": 0.22,
            "net_margin": 0.18,
            "pe_ratio": 15.4
        },
        {
            "period_end": date(2024, 3, 31),
            "data_available_date": date(2024, 4, 25),
            "roe": 0.35,
            "net_margin": 0.25,
            "pe_ratio": 22.1
        }
    ])

    # On 2024-04-15, only Statement 1 should be visible
    as_of = date(2024, 4, 15)
    filtered = filter_fundamentals_point_in_time(raw_statements, as_of_date=as_of)

    assert len(filtered) == 1
    assert filtered.iloc[0]["roe"] == 0.22

    # On 2024-04-26, Statement 2 should become visible
    filtered_after = filter_fundamentals_point_in_time(raw_statements, as_of_date=date(2024, 4, 26))
    assert len(filtered_after) == 2
    assert filtered_after.iloc[-1]["roe"] == 0.35


def test_fundamental_feature_extractor_point_in_time():
    dates = pd.date_range("2024-04-10", "2024-04-20", freq="B")
    p_df = pd.DataFrame({
        "open": [100.0] * len(dates),
        "high": [105.0] * len(dates),
        "low": [95.0] * len(dates),
        "close": [102.0] * len(dates),
        "volume": [100000] * len(dates)
    }, index=dates)

    raw_statements = pd.DataFrame([
        {
            "period_end": date(2023, 12, 31),
            "data_available_date": date(2024, 2, 15),
            "roe": 0.22,
            "pe_ratio": 15.0
        },
        {
            "period_end": date(2024, 3, 31),
            "data_available_date": date(2024, 4, 25), # Disclosed after dates in p_df
            "roe": 0.35,
            "pe_ratio": 25.0
        }
    ])

    ctx = FeatureContext("US.NASDAQ.AAPL", "AAPL", "US", "NASDAQ", price_df=p_df, fundamentals_df=raw_statements)
    extractor = FundamentalFeaturesExtractor()
    feat_df = extractor.compute(ctx)

    # For all dates in April 10-20, roe must equal 0.22 (never 0.35)
    assert (feat_df["roe"] == 0.22).all()
    assert not (feat_df["roe"] == 0.35).any()
