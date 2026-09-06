"""
Unit Tests for Direction Classifier Model
"""

import pytest
import pandas as pd
import numpy as np
from app.ml.models.direction import DirectionClassifier


def test_direction_classifier_fit_predict():
    np.random.seed(42)
    n = 100
    X = pd.DataFrame({
        "rsi_14": np.random.uniform(20, 80, n),
        "sma_20": np.random.uniform(90, 110, n),
        "atr_14": np.random.uniform(1, 5, n)
    })
    y = pd.Series(np.random.choice([0, 1], size=n))

    clf = DirectionClassifier(horizon="30d")
    clf.fit(X, y)

    assert clf.is_fitted is True
    
    preds = clf.predict(X)
    assert len(preds) == n
    assert set(preds).issubset({0, 1})

    probs = clf.predict_proba(X)
    assert probs.shape == (n, 2)
    assert np.allclose(probs.sum(axis=1), 1.0)
