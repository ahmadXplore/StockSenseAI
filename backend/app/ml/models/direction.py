"""
StockSense AI — Direction Classifier Model
Predicts binary price direction (Up vs Down) with calibrated probabilities and class weighting.
"""

from __future__ import annotations
import numpy as np
import pandas as pd
from typing import Optional, Dict, Any, List
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

from app.ml.models.base import BaseStockModel, ModelType


class DirectionClassifier(BaseStockModel):
    """
    Direction classification model predicting probability of positive return over horizon.
    """

    def __init__(
        self,
        model_id: str = "direction_default",
        name: str = "HistGradientBoosting_Direction",
        horizon: str = "30d",
        market_code: str = "US",
        exchange_code: str = "NASDAQ",
        algorithm: str = "hist_gb", # 'hist_gb', 'rf', 'logistic'
        class_weight: str = "balanced",
        random_state: int = 42
    ):
        super().__init__(
            model_id=model_id,
            model_type=ModelType.DIRECTION_CLASSIFIER,
            name=name,
            horizon=horizon,
            market_code=market_code,
            exchange_code=exchange_code
        )
        self.algorithm = algorithm
        self.random_state = random_state
        self.class_weight = class_weight
        self.scaler = StandardScaler()
        
        if algorithm == "logistic":
            self._model = LogisticRegression(class_weight=class_weight, random_state=random_state, max_iter=1000)
        elif algorithm == "rf":
            self._model = RandomForestClassifier(n_estimators=100, max_depth=6, class_weight=class_weight, random_state=random_state, n_jobs=-1)
        else:
            self._model = HistGradientBoostingClassifier(
                max_iter=100,
                max_depth=5,
                class_weight=class_weight,
                random_state=random_state,
                min_samples_leaf=10
            )

    def fit(self, X: pd.DataFrame, y: pd.Series) -> DirectionClassifier:
        self.feature_names = list(X.columns)
        X_clean = np.nan_to_num(X.values.astype(float), nan=0.0, posinf=1e4, neginf=-1e4)
        y_clean = y.values.astype(int)

        # Scale features
        X_scaled = self.scaler.fit_transform(X_clean)
        self._model.fit(X_scaled, y_clean)
        self.is_fitted = True
        return self

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        if not self.is_fitted:
            raise RuntimeError("Model must be fitted before predict()")
        X_vals = np.nan_to_num(X[self.feature_names].values.astype(float), nan=0.0, posinf=1e4, neginf=-1e4)
        X_scaled = self.scaler.transform(X_vals)
        return self._model.predict(X_scaled)

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """
        Returns array of [P(Down), P(Up)] for each sample.
        """
        if not self.is_fitted:
            raise RuntimeError("Model must be fitted before predict_proba()")
        X_vals = np.nan_to_num(X[self.feature_names].values.astype(float), nan=0.0, posinf=1e4, neginf=-1e4)
        X_scaled = self.scaler.transform(X_vals)
        if hasattr(self._model, "predict_proba"):
            probs = self._model.predict_proba(X_scaled)
            if probs.shape[1] == 2:
                return probs
            elif probs.shape[1] == 1:
                # Single class edge case
                p = probs[:, 0]
                return np.column_stack([1.0 - p, p])
        return np.column_stack([0.5 * np.ones(len(X)), 0.5 * np.ones(len(X))])

    def get_feature_importances(self) -> Dict[str, float]:
        if not self.is_fitted:
            return {}
        if hasattr(self._model, "feature_importances_"):
            return dict(zip(self.feature_names, [float(v) for v in self._model.feature_importances_]))
        elif hasattr(self._model, "coef_"):
            coefs = np.abs(self._model.coef_[0])
            total = coefs.sum() if coefs.sum() > 0 else 1.0
            return dict(zip(self.feature_names, [float(v / total) for v in coefs]))
        return {}
