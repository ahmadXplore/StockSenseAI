"""
StockSense AI — Walk-Forward Time-Series Validation Engine
Executes multi-period expanding/rolling out-of-sample evaluations with purged CV.
"""

from __future__ import annotations
import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

from app.ml.datasets.splits import PurgedTimeSeriesSplit
from app.ml.models.direction import DirectionClassifier
from app.ml.models.return_forecaster import ReturnForecaster


@dataclass
class WalkForwardResult:
    n_folds: int
    avg_directional_accuracy: float
    std_directional_accuracy: float
    avg_mae: float
    fold_metrics: List[Dict[str, Any]] = field(default_factory=list)
    is_validated: bool = True


class WalkForwardValidator:
    """
    Evaluates models across historical walk-forward folds without look-ahead bias.
    """

    def __init__(self, n_splits: int = 4, purge_window: int = 21):
        self.n_splits = n_splits
        self.purge_window = purge_window

    def validate(
        self,
        X: pd.DataFrame,
        y_direction: pd.Series,
        y_return: pd.Series,
        horizon: str = "30d",
        market_code: str = "US",
        exchange_code: str = "NASDAQ"
    ) -> WalkForwardResult:
        splitter = PurgedTimeSeriesSplit(n_splits=self.n_splits, purge_window=self.purge_window)
        
        fold_results = []
        accuracies = []
        maes = []

        fold_idx = 1
        for train_idx, test_idx in splitter.split(X):
            X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
            y_dir_train, y_dir_test = y_direction.iloc[train_idx], y_direction.iloc[test_idx]
            y_ret_train, y_ret_test = y_return.iloc[train_idx], y_return.iloc[test_idx]

            # Fit directional classifier
            clf = DirectionClassifier(horizon=horizon, market_code=market_code, exchange_code=exchange_code)
            clf.fit(X_train, y_dir_train)
            dir_preds = clf.predict(X_test)
            acc = float(np.mean(dir_preds == y_dir_test.values) * 100.0)
            accuracies.append(acc)

            # Fit return regressor
            reg = ReturnForecaster(horizon=horizon, market_code=market_code, exchange_code=exchange_code)
            reg.fit(X_train, y_ret_train)
            ret_preds = reg.predict(X_test)
            mae = float(np.mean(np.abs(ret_preds - y_ret_test.values)) * 100.0)
            maes.append(mae)

            fold_results.append({
                "fold": fold_idx,
                "train_samples": len(train_idx),
                "test_samples": len(test_idx),
                "directional_accuracy_pct": round(acc, 2),
                "mae_pct": round(mae, 4)
            })
            fold_idx += 1

        avg_acc = float(np.mean(accuracies)) if accuracies else 50.0
        std_acc = float(np.std(accuracies)) if accuracies else 0.0
        avg_mae = float(np.mean(maes)) if maes else 0.0

        return WalkForwardResult(
            n_folds=len(fold_results),
            avg_directional_accuracy=round(avg_acc, 2),
            std_directional_accuracy=round(std_acc, 2),
            avg_mae=round(avg_mae, 4),
            fold_metrics=fold_results,
            is_validated=len(fold_results) > 0
        )
