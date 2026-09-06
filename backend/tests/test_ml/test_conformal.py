"""
Unit Tests for Split Conformal Prediction Intervals
"""

import pytest
import numpy as np
from app.ml.training.conformal import SplitConformalPredictor


def test_conformal_prediction_coverage():
    np.random.seed(42)
    n = 100
    y_cal_true = np.random.randn(n) * 10.0
    y_cal_pred = y_cal_true + np.random.normal(0, 2.0, n)

    conformal = SplitConformalPredictor(confidence_level=0.90)
    conformal.calibrate(y_cal_true, y_cal_pred)

    assert conformal.is_calibrated is True
    assert conformal.q_hat > 0

    # Test prediction interval
    interval = conformal.predict_interval(point_prediction=5.0)
    assert interval.lower_bound == round(5.0 - conformal.q_hat, 2)
    assert interval.upper_bound == round(5.0 + conformal.q_hat, 2)

    # Test coverage evaluation
    y_test_true = np.random.randn(50) * 10.0
    y_test_pred = y_test_true + np.random.normal(0, 2.0, 50)
    cov = conformal.evaluate_coverage(y_test_true, y_test_pred)
    assert cov["empirical_coverage_pct"] >= 75.0 # Empirical coverage close to 90%
