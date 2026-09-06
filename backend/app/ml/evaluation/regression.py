"""
StockSense AI — Regression Evaluation Metrics
Calculates MAE, RMSE, MAPE, R², Information Coefficient (IC), and Rank IC.
"""

from __future__ import annotations
import numpy as np
from dataclasses import dataclass
from scipy.stats import spearmanr
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


@dataclass
class RegressionMetricsResult:
    mae: float
    rmse: float
    r2_score: float
    information_coefficient: float     # Pearson corr(pred, actual)
    rank_ic: float                     # Spearman rank correlation


def evaluate_regression(y_true: np.ndarray, y_pred: np.ndarray) -> RegressionMetricsResult:
    y_t = np.asarray(y_true).ravel().astype(float)
    y_p = np.asarray(y_pred).ravel().astype(float)

    mae = float(mean_absolute_error(y_t, y_p))
    rmse = float(np.sqrt(mean_squared_error(y_t, y_p)))
    r2 = float(r2_score(y_t, y_p)) if len(y_t) > 2 else 0.0

    # Information Coefficient (Pearson Correlation)
    if np.std(y_t) > 0 and np.std(y_p) > 0:
        ic = float(np.corrcoef(y_t, y_p)[0, 1])
        rank_ic, _ = spearmanr(y_t, y_p)
        rank_ic = float(rank_ic) if not np.isnan(rank_ic) else 0.0
    else:
        ic = 0.0
        rank_ic = 0.0

    return RegressionMetricsResult(
        mae=round(mae, 4),
        rmse=round(rmse, 4),
        r2_score=round(r2, 4),
        information_coefficient=round(ic, 4),
        rank_ic=round(rank_ic, 4)
    )
