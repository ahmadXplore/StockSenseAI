"""
Unit Tests for Feature & Model Drift Monitoring
"""

import pytest
import numpy as np
import pandas as pd
from app.ml.monitoring.drift import DriftMonitor


def test_psi_calculation_no_drift():
    np.random.seed(42)
    ref = np.random.normal(0, 1, 1000)
    cur = np.random.normal(0, 1, 1000) # Same distribution

    psi = DriftMonitor.compute_psi(ref, cur)
    assert psi < 0.10 # No significant shift


def test_psi_calculation_with_drift():
    np.random.seed(42)
    ref = np.random.normal(0, 1, 1000)
    cur = np.random.normal(3.0, 2.0, 1000) # Large mean & std shift

    psi = DriftMonitor.compute_psi(ref, cur)
    assert psi >= 0.20 # Significant drift detected


def test_dataset_drift_monitor():
    monitor = DriftMonitor()
    baseline = pd.DataFrame({"rsi": np.random.uniform(30, 70, 100)})
    shifted = pd.DataFrame({"rsi": np.random.uniform(75, 95, 100)}) # Shifted into overbought

    summary = monitor.monitor_dataset_drift("model_test", baseline, shifted)
    assert summary.is_overall_drifting is True
    assert summary.drifted_features_count > 0
