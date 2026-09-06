"""
StockSense AI — Base Stock Model Specification & Prediction Dataclasses
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np


class ModelType(str, Enum):
    DIRECTION_CLASSIFIER = "direction_classifier"
    RETURN_FORECASTER = "return_forecaster"
    VOLATILITY_FORECASTER = "volatility_forecaster"
    ENSEMBLE = "ensemble"


@dataclass
class PredictionResult:
    security_id: str
    horizon: str
    direction: str                     # 'UP', 'DOWN'
    probability_up: float              # Calibrated probability [0.0, 1.0]
    probability_down: float
    expected_return_pct: float         # Projected return % over horizon
    lower_bound_pct: float             # Conformal (1-alpha) lower bound
    upper_bound_pct: float             # Conformal (1-alpha) upper bound
    predicted_volatility: float
    confidence_score: float            # 0.0 to 100.0
    model_version: str
    feature_version: str
    prediction_timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    top_positive_features: List[Dict[str, Any]] = field(default_factory=list)
    top_negative_features: List[Dict[str, Any]] = field(default_factory=list)
    diagnostics: Dict[str, Any] = field(default_factory=dict)


class BaseStockModel(ABC):
    """
    Abstract interface for all StockSense AI predictive models.
    """

    def __init__(
        self,
        model_id: str,
        model_type: ModelType,
        name: str,
        horizon: str = "30d",
        market_code: str = "US",
        exchange_code: str = "NASDAQ",
        version: str = "1.0.0"
    ):
        self.model_id = model_id
        self.model_type = model_type
        self.name = name
        self.horizon = horizon
        self.market_code = market_code
        self.exchange_code = exchange_code
        self.version = version
        self.is_fitted = False
        self.feature_names: List[str] = []

    @abstractmethod
    def fit(self, X: pd.DataFrame, y: pd.Series) -> BaseStockModel:
        """Fits model parameters on training dataset."""
        pass

    @abstractmethod
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """Generates predictions."""
        pass

    def get_feature_importances(self) -> Dict[str, float]:
        """Returns feature importance mapping if supported."""
        return {}
