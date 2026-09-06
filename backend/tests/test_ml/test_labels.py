"""
Unit Tests for ML Labels Generation
"""

import pytest
import pandas as pd
import numpy as np
from app.ml.datasets.labels import generate_time_series_labels, HORIZON_TRADING_DAYS


def test_label_generation_30d():
    dates = pd.date_range("2024-01-01", periods=100, freq="B")
    p_df = pd.DataFrame({"close": 100.0 + np.cumsum(np.random.randn(100))}, index=dates)

    labels = generate_time_series_labels(p_df, horizon="30d")
    
    assert "target_return_30d" in labels.columns
    assert "target_direction_30d" in labels.columns
    assert "target_volatility_30d" in labels.columns

    # Check that last 21 rows are NaN for future target
    assert labels["target_return_30d"].iloc[-21:].isna().all()
    # Check that earlier rows have non-null targets
    assert not labels["target_return_30d"].iloc[:-21].isna().any()
