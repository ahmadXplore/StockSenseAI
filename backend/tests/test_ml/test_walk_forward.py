"""
Unit Tests for Walk-Forward Validation Engine
"""

import pytest
import pandas as pd
import numpy as np
from app.ml.training.walk_forward import WalkForwardValidator


def test_walk_forward_execution():
    np.random.seed(42)
    n = 150
    dates = pd.date_range("2023-01-01", periods=n, freq="B")
    X = pd.DataFrame({
        "feat1": np.random.randn(n),
        "feat2": np.random.randn(n),
        "feat3": np.random.randn(n)
    }, index=dates)
    
    y_dir = pd.Series(np.random.choice([0, 1], size=n), index=dates)
    y_ret = pd.Series(np.random.randn(n) * 0.05, index=dates)

    validator = WalkForwardValidator(n_splits=3, purge_window=5)
    res = validator.validate(X, y_dir, y_ret, horizon="30d")

    assert res.is_validated is True
    assert res.n_folds > 0
    assert len(res.fold_metrics) == res.n_folds
    assert 0.0 <= res.avg_directional_accuracy <= 100.0
