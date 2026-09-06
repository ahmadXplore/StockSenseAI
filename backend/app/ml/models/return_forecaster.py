"""
StockSense AI — Return Forecaster Model
Predicts expected percentage return over horizon using Ridge / HistGradientBoostingRegressor.
"""

from __future__ import annotations
import numpy as np
import pandas as pd
from typing import Dict, Any, List
from sklearn.ensemble import HistGradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.preprocessing import RobustScaler

from app.ml.models.base import BaseStockModel, ModelType


class ReturnForecaster(BaseStockModel):
    """
    Regression model estimating point forecast of expected return over horizon.
    """

    def __init__(
        self,
        model_id: str = "return_forecaster_default",
        name: str = "HistGradientBoosting_Return",
        horizon: str = "30d",
        market_code: str = "US",
        exchange_code: str = "NASDAQ",
        algorithm: str = "hist_gb", # 'hist_gb', 'ridge', 'rf'
        random_state: int = 42
    ):
        super().__init__(
            model_id=model_id,
            model_type=ModelType.RETURN_FORECASTER,
            name=name,
            horizon=horizon,
            market_code=market_code,
            exchange_code=exchange_code
        )
        self.algorithm = algorithm
        self.random_state = random_state
        self.scaler = RobustScaler()

        if algorithm == "ridge":
            self._model = Ridge(alpha=1.0, random_state=random_state)
        elif algorithm == "rf":
            self._model = RandomForestRegressor(n_estimators=100, max_depth=6, random_state=random_state, n_jobs=-1)
        else:
            self._model = HistGradientBoostingRegressor(
                max_iter=100,
                max_depth=5,
                random_state=random_state,
                min_samples_leaf=10
            )

    def fit(self, X: pd.DataFrame, y: pd.Series) -> ReturnForecaster:
        self.feature_names = list(X.columns)
        X_clean = np.nan_to_num(X.values.astype(float), nan=0.0, posinf=1e4, neginf=-1e4)
        y_clean = np.nan_to_num(y.values.astype(float), nan=0.0, posinf=1.0, neginf=-1.0)

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

    def get_feature_importances(self) -> Dict[str, float]:
        if not self.is_fitted:
            return {}
        if hasattr(self._model, "feature_importances_"):
            return dict(zip(self.feature_names, [float(v) for v in self._model.feature_importances_]))
        elif hasattr(self._model, "coef_"):
            coefs = np.abs(self._model.coef_)
            total = coefs.sum() if coefs.sum() > 0 else 1.0
            return dict(zip(self.feature_names, [float(v / total) for v in coefs]))
        return {}
