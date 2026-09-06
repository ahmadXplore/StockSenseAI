"""
Unit Tests for Return Forecaster Model
"""

import pytest
import pandas as pd
import numpy as np
from app.ml.models.return_forecaster import ReturnForecaster


def test_return_forecaster_fit_predict():
    np.random.seed(42)
    n = 100
    X = pd.DataFrame({
        "momentum_10d": np.random.randn(n),
        "volatility_20d": np.random.uniform(10, 30, n)
    })
    y = pd.Series(np.random.randn(n) * 0.05)

    forecaster = ReturnForecaster(horizon="30d")
    forecaster.fit(X, y)

    assert forecaster.is_fitted is True

    preds = forecaster.predict(X)
    assert len(preds) == n
    assert isinstance(preds[0], float)
