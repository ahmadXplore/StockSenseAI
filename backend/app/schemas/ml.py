"""
StockSense AI — Machine Learning Pydantic API Schemas
"""

from __future__ import annotations
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import date, datetime


class BuildFeaturesRequest(BaseModel):
    security_id: str
    as_of_date: Optional[date] = None
    impute_missing: bool = True


class FeaturesResponse(BaseModel):
    security_id: str
    feature_version: str
    config_hash: str
    row_count: int
    column_count: int
    feature_names: List[str]
    leakage_status: str


class BuildDatasetRequest(BaseModel):
    security_id: str
    horizon: str = "30d"
    as_of_date: Optional[date] = None


class DatasetResponse(BaseModel):
    dataset_id: str
    security_id: str
    market_code: str
    exchange_code: str
    horizon: str
    sample_count: int
    feature_count: int
    is_sufficient: bool
    status: str
    reason: Optional[str] = None


class TrainModelRequest(BaseModel):
    security_id: str
    horizon: str = "30d"
    algorithm: str = "hist_gb"
    calibrate: bool = True
    run_walk_forward: bool = True


class TrainModelResponse(BaseModel):
    model_id: str
    security_id: str
    market_code: str
    exchange_code: str
    horizon: str
    status: str
    directional_accuracy: float
    mae: float
    rmse: float
    brier_score: float
    ece: float
    conformal_coverage_pct: float
    walk_forward_accuracy: Optional[float] = None


class PredictSecurityRequest(BaseModel):
    horizon: str = "30d"
    as_of_date: Optional[date] = None


class PredictionResponse(BaseModel):
    security_id: str
    horizon: str
    direction: str
    probability_up: float
    probability_down: float
    expected_return_pct: float
    lower_bound_pct: float
    upper_bound_pct: float
    predicted_volatility: float
    confidence_score: float
    model_version: str
    feature_version: str
    prediction_timestamp: datetime
    top_positive_features: List[Dict[str, Any]]
    top_negative_features: List[Dict[str, Any]]
    diagnostics: Dict[str, Any]


class ModelMetadataResponse(BaseModel):
    model_id: str
    model_type: str
    model_name: str
    market_code: str
    exchange_code: str
    horizon: str
    status: str
    is_deployed: bool
    feature_version: str
    metrics: Dict[str, Any]
    artifact_hash: str
    created_at: datetime


class DriftCheckResponse(BaseModel):
    model_id: str
    check_date: date
    drifted_features_count: int
    total_features_checked: int
    is_overall_drifting: bool
    requires_retrain: bool
    feature_reports: List[Dict[str, Any]]
