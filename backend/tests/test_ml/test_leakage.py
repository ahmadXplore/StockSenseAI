"""
Unit Tests for Look-Ahead Leakage & Target Contamination Detection
"""

import pytest
import pandas as pd
import numpy as np
from datetime import date
from app.features.validation.leakage import check_feature_matrix_leakage


def test_leakage_detection_blocks_future_data():
    dates = pd.date_range("2024-04-10", "2024-04-20", freq="B")
    feat_df = pd.DataFrame({"sma_20": [100.0] * len(dates)}, index=dates)

    # Scans as_of_date = 2024-04-15
    res = check_feature_matrix_leakage(feat_df, as_of_date=date(2024, 4, 15))
    assert res.has_leakage is True
    assert res.status == "BLOCKED_LEAKAGE_DETECTED"


def test_leakage_detection_target_correlation():
    dates = pd.date_range("2024-01-01", periods=50, freq="B")
    target = pd.Series(np.random.randn(50), index=dates)
    
    # Feature identical to target (100% correlation)
    feat_df = pd.DataFrame({"leaked_feature": target.values}, index=dates)

    res = check_feature_matrix_leakage(feat_df, target_series=target)
    assert res.has_leakage is True
    assert res.status == "BLOCKED_LEAKAGE_DETECTED"
