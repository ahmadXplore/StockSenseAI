"""
Unit Tests for Purged Time-Series Cross-Validation
"""

import pytest
import pandas as pd
import numpy as np
from app.ml.datasets.splits import PurgedTimeSeriesSplit


def test_purged_split_separates_train_and_test():
    dates = pd.date_range("2020-01-01", periods=300, freq="B")
    df = pd.DataFrame({"val": np.arange(300)}, index=dates)

    splitter = PurgedTimeSeriesSplit(n_splits=3, purge_window=21, min_train_size=100)
    splits = list(splitter.split(df))

    assert len(splits) == 3
    for train_idx, test_idx in splits:
        # Check that max train index is strictly before min test index - purge_window
        assert train_idx[-1] <= test_idx[0] - 21
        # Check no overlap between train and test
        assert len(set(train_idx).intersection(set(test_idx))) == 0
