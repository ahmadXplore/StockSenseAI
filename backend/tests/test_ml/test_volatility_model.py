"""
Unit Tests for Volatility Forecaster Model
"""

import pytest
import pandas as pd
import numpy as np
from app.ml.models.volatility import VolatilityForecaster


def test_volatility_forecaster():
    np.random.seed(42)
    n = 100
    X = pd.DataFrame({"atr_14": np.random.uniform(1, 5, n)})
    y = pd.Series(np.random.uniform(15, 35, n))

    model = VolatilityForecaster(horizon="30d")
    model.fit(X, y)

    assert model.is_fitted is True
    preds = model.predict(X)
    assert len(preds) == n
    assert (preds >= 5.0).all() # Enforce positive non-zero floor
