"""
StockSense AI — Model & Feature Drift Monitoring Engine
Computes Population Stability Index (PSI), Kolmogorov-Smirnov (KS) statistics, and triggers retraining alerts.
"""

from __future__ import annotations
import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from typing import Dict, Any, List, Optional
from scipy.stats import ks_2samp


@dataclass
class FeatureDriftReport:
    feature_name: str
    psi_score: float
    ks_statistic: float
    ks_p_value: float
    is_drifting: bool


@dataclass
class ModelDriftSummary:
    model_id: str
    check_date: date
    drifted_features_count: int
    total_features_checked: int
    is_overall_drifting: bool
    requires_retrain: bool
    feature_reports: List[FeatureDriftReport] = field(default_factory=list)
    diagnostics: Dict[str, Any] = field(default_factory=dict)


class DriftMonitor:
    """
    Monitors data distribution shifts and model degradation over time.
    """

    def __init__(self, psi_threshold: float = 0.20, ks_p_threshold: float = 0.05):
        self.psi_threshold = psi_threshold
        self.ks_p_threshold = ks_p_threshold

    @staticmethod
    def compute_psi(reference: np.ndarray, current: np.ndarray, num_buckets: int = 10) -> float:
        """
        Population Stability Index (PSI):
        PSI < 0.10: No significant shift
        0.10 <= PSI < 0.20: Moderate shift
        PSI >= 0.20: Significant distribution drift
        """
        ref_clean = np.asarray(reference).ravel()
        cur_clean = np.asarray(current).ravel()
        
        # Remove NaNs
        ref_clean = ref_clean[~np.isnan(ref_clean)]
        cur_clean = cur_clean[~np.isnan(cur_clean)]

        if len(ref_clean) < 10 or len(cur_clean) < 10:
            return 0.0

        # Create buckets based on reference percentiles
        percentiles = np.linspace(0, 100, num_buckets + 1)
        bucket_bounds = np.percentile(ref_clean, percentiles)
        bucket_bounds[0] = -np.inf
        bucket_bounds[-1] = np.inf

        ref_counts = np.histogram(ref_clean, bins=bucket_bounds)[0]
        cur_counts = np.histogram(cur_clean, bins=bucket_bounds)[0]

        # Convert to percentages with small epsilon smoothing
        ref_pct = (ref_counts + 1e-4) / (len(ref_clean) + 1e-3)
        cur_pct = (cur_counts + 1e-4) / (len(cur_clean) + 1e-3)

        psi = np.sum((cur_pct - ref_pct) * np.log(cur_pct / ref_pct))
        return float(max(0.0, psi))

    def evaluate_feature_drift(
        self,
        reference_series: pd.Series,
        current_series: pd.Series,
        feature_name: str
    ) -> FeatureDriftReport:
        ref_vals = reference_series.dropna().values
        cur_vals = current_series.dropna().values

        psi = self.compute_psi(ref_vals, cur_vals)

        if len(ref_vals) > 5 and len(cur_vals) > 5:
            ks_res = ks_2samp(ref_vals, cur_vals)
            ks_stat = float(ks_res.statistic)
            ks_p = float(ks_res.pvalue)
        else:
            ks_stat = 0.0
            ks_p = 1.0

        is_drifting = (psi >= self.psi_threshold) or (ks_p < self.ks_p_threshold and ks_stat > 0.3)

        return FeatureDriftReport(
            feature_name=feature_name,
            psi_score=round(psi, 4),
            ks_statistic=round(ks_stat, 4),
            ks_p_value=round(ks_p, 4),
            is_drifting=is_drifting
        )

    def monitor_dataset_drift(
        self,
        model_id: str,
        baseline_X: pd.DataFrame,
        current_X: pd.DataFrame
    ) -> ModelDriftSummary:
        reports = []
        drifted_count = 0

        common_cols = [c for c in baseline_X.columns if c in current_X.columns]
        for col in common_cols:
            if not np.issubdtype(baseline_X[col].dtype, np.number):
                continue
            rep = self.evaluate_feature_drift(baseline_X[col], current_X[col], feature_name=col)
            reports.append(rep)
            if rep.is_drifting:
                drifted_count += 1

        total_checked = len(reports)
        drift_ratio = (drifted_count / total_checked) if total_checked > 0 else 0.0
        requires_retrain = drift_ratio > 0.25 # If > 25% of features drifted

        return ModelDriftSummary(
            model_id=model_id,
            check_date=date.today(),
            drifted_features_count=drifted_count,
            total_features_checked=total_checked,
            is_overall_drifting=(drifted_count > 0),
            requires_retrain=requires_retrain,
            feature_reports=reports,
            diagnostics={"drift_feature_ratio": round(drift_ratio, 4)}
        )


drift_monitor = DriftMonitor()
