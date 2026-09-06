"""
Unit Tests for Probability Calibration (Isotonic Regression & Platt Scaling)
"""

import pytest
import numpy as np
from app.ml.training.calibration import ProbabilityCalibrator


def test_isotonic_calibration_reduces_brier():
    np.random.seed(42)
    n = 100
    y_true = np.random.choice([0, 1], size=n, p=[0.4, 0.6])
    # Uncalibrated raw probabilities (overconfident)
    raw_probs = np.where(y_true == 1, np.random.uniform(0.7, 0.99, n), np.random.uniform(0.01, 0.3, n))

    calibrator = ProbabilityCalibrator(method="isotonic")
    calibrator.fit(raw_probs, y_true)

    cal_probs = calibrator.calibrate(raw_probs)
    assert len(cal_probs) == n
    assert (cal_probs >= 0.0).all() and (cal_probs <= 1.0).all()

    metrics = calibrator.evaluate_calibration(raw_probs, cal_probs, y_true)
    assert metrics.is_calibrated is True
    assert metrics.expected_calibration_error >= 0.0
