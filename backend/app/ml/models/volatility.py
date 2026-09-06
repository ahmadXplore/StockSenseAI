"""
StockSense AI — Volatility Forecaster Model
Forecasts future annualized realized volatility using tree ensembles and historical baselines.
"""

from __future__ import annotations
import numpy as np
import pandas as pd
from typing import Dict, Any, List
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.preprocessing import StandardScaler

from app.ml.models.base import BaseStockModel, ModelType


class VolatilityForecaster(BaseStockModel):
    """
    Predicts annualized realized volatility over the target horizon.
    """

    def __init__(
        self,
        model_id: str = "volatility_forecaster_default",
        name: str = "HistGradientBoosting_Volatility",
        horizon: str = "30d",
        market_code: str = "US",
        exchange_code: str = "NASDAQ",
        random_state: int = 42
    ):
        super().__init__(
            model_id=model_id,
            model_type=ModelType.VOLATILITY_FORECASTER,
            name=name,
            horizon=horizon,
            market_code=market_code,
            exchange_code=exchange_code
        )
        self.random_state = random_state
        self.scaler = StandardScaler()
        self._model = HistGradientBoostingRegressor(
            max_iter=80,
            max_depth=4,
            random_state=random_state,
            min_samples_leaf=10
        )

    def fit(self, X: pd.DataFrame, y: pd.Series) -> VolatilityForecaster:
        self.feature_names = list(X.columns)
        X_clean = X.fillna(0.0).values
        y_clean = np.maximum(0.0, y.values.astype(float))

        X_scaled = self.scaler.fit_transform(X_clean)
        self._model.fit(X_scaled, y_clean)
        self.is_fitted = True
        return self

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        if not self.is_fitted:
            raise RuntimeError("Model must be fitted before predict()")
        X_scaled = self.scaler.transform(X[self.feature_names].fillna(0.0).values)
        preds = self._model.predict(X_scaled)
        return np.maximum(5.0, preds) # Enforce positive non-zero floor for annualized vol
