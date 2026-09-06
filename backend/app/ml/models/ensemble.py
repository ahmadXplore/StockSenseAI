"""
StockSense AI — Master Multi-Model Ensemble Predictor
Blends direction, return regression, volatility, and conformal bounds into a unified structured prediction.
"""

from __future__ import annotations
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from app.ml.models.base import BaseStockModel, ModelType, PredictionResult
from app.ml.models.direction import DirectionClassifier
from app.ml.models.return_forecaster import ReturnForecaster
from app.ml.models.volatility import VolatilityForecaster


class StockSenseEnsemble(BaseStockModel):
    """
    Ensemble model integrating direction classification, return regression, and volatility forecasting.
    """

    def __init__(
        self,
        model_id: str = "ensemble_default",
        name: str = "StockSense_Master_Ensemble",
        horizon: str = "30d",
        market_code: str = "US",
        exchange_code: str = "NASDAQ",
        version: str = "1.0.0"
    ):
        super().__init__(
            model_id=model_id,
            model_type=ModelType.ENSEMBLE,
            name=name,
            horizon=horizon,
            market_code=market_code,
            exchange_code=exchange_code,
            version=version
        )
        self.direction_model = DirectionClassifier(horizon=horizon, market_code=market_code, exchange_code=exchange_code)
        self.return_model = ReturnForecaster(horizon=horizon, market_code=market_code, exchange_code=exchange_code)
        self.volatility_model = VolatilityForecaster(horizon=horizon, market_code=market_code, exchange_code=exchange_code)
        self.conformal_q_score: float = 5.0 # Baseline conformal nonconformity threshold

    def fit(self, X: pd.DataFrame, y_dict: Dict[str, pd.Series]) -> StockSenseEnsemble:
        """
        Fits all sub-models with appropriate target columns:
        y_dict requires 'y_direction', 'y_return', and 'y_volatility'.
        """
        self.feature_names = list(X.columns)

        if "y_direction" in y_dict:
            self.direction_model.fit(X, y_dict["y_direction"])
        if "y_return" in y_dict:
            self.return_model.fit(X, y_dict["y_return"])
        if "y_volatility" in y_dict:
            self.volatility_model.fit(X, y_dict["y_volatility"])

        self.is_fitted = True
        return self

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        return self.return_model.predict(X)

    def predict_structured(
        self,
        security_id: str,
        X: pd.DataFrame,
        feature_version: str = "1.0.0"
    ) -> PredictionResult:
        """
        Generates complete structured PredictionResult for the latest row of X.
        """
        if not self.is_fitted:
            raise RuntimeError("Ensemble must be fitted before predict_structured()")

        latest_row = X.iloc[[-1]] if len(X) > 0 else X
        
        # 1. Direction & Calibrated Probabilities
        probs = self.direction_model.predict_proba(latest_row)[0]
        prob_up = float(probs[1])
        prob_down = float(probs[0])
        direction = "UP" if prob_up >= 0.50 else "DOWN"

        # 2. Return Forecast (%)
        exp_ret = float(self.return_model.predict(latest_row)[0] * 100.0)

        # 3. Volatility Forecast (%)
        pred_vol = float(self.volatility_model.predict(latest_row)[0])

        # 4. Conformal (1-alpha) Prediction Interval Bounds
        lower_bound = round(exp_ret - self.conformal_q_score, 2)
        upper_bound = round(exp_ret + self.conformal_q_score, 2)

        # 5. Confidence Score (0-100)
        # Scaled by probability distance from 0.5 and inverse volatility penalty
        prob_margin = abs(prob_up - 0.5) * 2.0 # [0.0, 1.0]
        vol_penalty = min(0.3, pred_vol / 100.0)
        conf_score = round(max(30.0, min(95.0, (prob_margin * 60.0 + 35.0) - (vol_penalty * 20.0))), 1)

        # 6. Extract Top Influential Drivers
        importances = self.direction_model.get_feature_importances()
        sorted_feats = sorted(importances.items(), key=lambda x: x[1], reverse=True)
        top_pos = [{"feature": f, "importance": round(imp, 4)} for f, imp in sorted_feats[:5]]
        top_neg = [{"feature": f, "importance": round(imp, 4)} for f, imp in sorted_feats[5:10]]

        return PredictionResult(
            security_id=security_id,
            horizon=self.horizon,
            direction=direction,
            probability_up=round(prob_up, 4),
            probability_down=round(prob_down, 4),
            expected_return_pct=round(exp_ret, 2),
            lower_bound_pct=lower_bound,
            upper_bound_pct=upper_bound,
            predicted_volatility=round(pred_vol, 2),
            confidence_score=conf_score,
            model_version=self.version,
            feature_version=feature_version,
            prediction_timestamp=datetime.now(timezone.utc),
            top_positive_features=top_pos,
            top_negative_features=top_neg,
            diagnostics={"conformal_margin": self.conformal_q_score, "volatility_annualized": pred_vol}
        )
