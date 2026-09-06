"""
StockSense AI — Probability Calibration Engine
Implements Platt Scaling and Isotonic Regression with Brier Score and ECE evaluation.
"""

from __future__ import annotations
import numpy as np
import pandas as pd
from dataclasses import dataclass
from typing import Tuple, Dict, Any
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression


@dataclass
class CalibrationMetrics:
    brier_score_uncalibrated: float
    brier_score_calibrated: float
    expected_calibration_error: float # ECE
    calibration_method: str
    is_calibrated: bool = True


class ProbabilityCalibrator:
    """
    Calibrates raw ML model probabilities on an out-of-sample calibration dataset.
    """

    def __init__(self, method: str = "isotonic"):
        self.method = method # 'isotonic' or 'platt'
        self.is_fitted = False
        if method == "platt":
            self._calibrator = LogisticRegression()
        else:
            self._calibrator = IsotonicRegression(out_of_bounds="clip", y_min=0.0, y_max=1.0)

    def fit(self, raw_probabilities: np.ndarray, y_true: np.ndarray) -> ProbabilityCalibrator:
        p_clean = np.asarray(raw_probabilities).ravel()
        y_clean = np.asarray(y_true).ravel().astype(int)

        if self.method == "platt":
            self._calibrator.fit(p_clean.reshape(-1, 1), y_clean)
        else:
            self._calibrator.fit(p_clean, y_clean)

        self.is_fitted = True
        return self

    def calibrate(self, raw_probabilities: np.ndarray) -> np.ndarray:
        if not self.is_fitted:
            return raw_probabilities

        p_clean = np.asarray(raw_probabilities).ravel()
        if self.method == "platt":
            cal_probs = self._calibrator.predict_proba(p_clean.reshape(-1, 1))[:, 1]
        else:
            cal_probs = self._calibrator.predict(p_clean)

        return np.clip(cal_probs, 0.01, 0.99)

    @staticmethod
    def compute_brier_score(probabilities: np.ndarray, y_true: np.ndarray) -> float:
        """Brier Score = mean( (p - y)^2 ). Lower is better (0.0 is perfect)."""
        p = np.asarray(probabilities).ravel()
        y = np.asarray(y_true).ravel()
        return float(np.mean((p - y) ** 2))

    @staticmethod
    def compute_ece(probabilities: np.ndarray, y_true: np.ndarray, n_bins: int = 10) -> float:
        """
        Expected Calibration Error (ECE) across n_bins.
        """
        p = np.asarray(probabilities).ravel()
        y = np.asarray(y_true).ravel()
        bin_limits = np.linspace(0.0, 1.0, n_bins + 1)
        ece = 0.0
        n_samples = len(p)

        if n_samples == 0:
            return 0.0

        for i in range(n_bins):
            bin_mask = (p >= bin_limits[i]) & (p < bin_limits[i + 1]) if i < n_bins - 1 else (p >= bin_limits[i]) & (p <= bin_limits[i + 1])
            if np.sum(bin_mask) > 0:
                bin_acc = np.mean(y[bin_mask])
                bin_conf = np.mean(p[bin_mask])
                bin_weight = np.sum(bin_mask) / n_samples
                ece += bin_weight * abs(bin_acc - bin_conf)

        return float(ece)

    def evaluate_calibration(
        self,
        raw_probabilities: np.ndarray,
        calibrated_probabilities: np.ndarray,
        y_true: np.ndarray
    ) -> CalibrationMetrics:
        brier_uncal = self.compute_brier_score(raw_probabilities, y_true)
        brier_cal = self.compute_brier_score(calibrated_probabilities, y_true)
        ece = self.compute_ece(calibrated_probabilities, y_true)

        return CalibrationMetrics(
            brier_score_uncalibrated=round(brier_uncal, 4),
            brier_score_calibrated=round(brier_cal, 4),
            expected_calibration_error=round(ece, 4),
            calibration_method=self.method,
            is_calibrated=True
        )
