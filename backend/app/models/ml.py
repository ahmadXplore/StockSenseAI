"""
StockSense AI — Machine Learning ORM Models (Schema: ml)
Model Registry, Feature Versioning, Drift Monitoring, and Outcome Tracking.
"""

import uuid
from datetime import datetime, date, timezone
from sqlalchemy import (
    Column, Integer, String, Numeric, Boolean, Date, DateTime, Text, ForeignKey, Index, ARRAY, JSON
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.db.base import Base
from app.models.enums import ModelStatus


class ModelMetadata(Base):
    __tablename__ = "model_metadata"
    __table_args__ = (
        Index("idx_model_ticker_horizon", "ticker", "horizon"),
        Index("idx_model_status", "status"),
        {"schema": "ml"}
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ticker = Column(String(10), ForeignKey("market_data.companies.ticker"), nullable=True) # NULL for universal ensemble
    model_name = Column(String(100), nullable=False)
    model_type = Column(String(50), nullable=False)  # 'xgboost_regressor', 'lightgbm', 'ensemble'
    model_version = Column(String(50), default="1.0.0", nullable=False)
    feature_version = Column(String(50), default="1.0.0", nullable=False)
    dataset_version = Column(String(50), default="1.0.0", nullable=False)
    horizon = Column(String(20), nullable=False)     # '7d', '30d', '3m', '6m', '1y', '3y'
    
    # Training & validation windows
    training_start_date = Column(Date)
    training_end_date = Column(Date)
    validation_start_date = Column(Date)
    validation_end_date = Column(Date)
    training_samples = Column(Integer)
    validation_samples = Column(Integer)
    feature_count = Column(Integer)
    feature_names = Column(ARRAY(Text).with_variant(JSON, "sqlite"))
    
    # Validation metrics
    val_directional_accuracy = Column(Numeric(6, 4))
    val_roc_auc = Column(Numeric(6, 4))
    val_calibration_error = Column(Numeric(6, 4))
    val_mae = Column(Numeric(12, 4))
    val_rmse = Column(Numeric(12, 4))
    val_sharpe_ratio = Column(Numeric(8, 4))
    val_win_rate = Column(Numeric(6, 4))
    
    # Walk-forward validation results
    wf_periods = Column(Integer)
    wf_avg_accuracy = Column(Numeric(6, 4))
    wf_std_accuracy = Column(Numeric(6, 4))
    wf_results_detail = Column(JSONB)
    
    # Calibration details
    is_calibrated = Column(Boolean, default=False)
    calibration_method = Column(String(30), default="isotonic")
    calibration_score = Column(Numeric(6, 4))
    regime_coverage_json = Column(JSONB)
    
    # Deployment status
    status = Column(String(30), default=ModelStatus.TRAINING.value, nullable=False)
    is_deployed = Column(Boolean, default=False, nullable=False)
    deployed_at = Column(DateTime(timezone=True), nullable=True)
    retired_at = Column(DateTime(timezone=True), nullable=True)
    retirement_reason = Column(Text, nullable=True)
    
    # Model binary artifacts
    model_file_path = Column(String(500))
    model_file_hash = Column(String(64))  # SHA-256 integrity hash
    hyperparameters = Column(JSONB)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    feature_importances = relationship("FeatureImportance", back_populates="model", cascade="all, delete-orphan")
    prediction_outcomes = relationship("PredictionOutcome", back_populates="model", cascade="all, delete-orphan")
    drift_checks = relationship("ModelDriftMonitoring", back_populates="model", cascade="all, delete-orphan")


class FeatureImportance(Base):
    __tablename__ = "feature_importance"
    __table_args__ = ({"schema": "ml"})

    id = Column(Integer, primary_key=True, autoincrement=True)
    model_id = Column(UUID(as_uuid=True), ForeignKey("ml.model_metadata.id"), nullable=False)
    feature_name = Column(String(100), nullable=False)
    importance_score = Column(Numeric(10, 6), nullable=False)
    rank = Column(Integer, nullable=False)
    importance_type = Column(String(30), default="shap")  # 'gain', 'shap', 'permutation'
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    model = relationship("ModelMetadata", back_populates="feature_importances")


class PredictionOutcome(Base):
    __tablename__ = "prediction_outcomes"
    __table_args__ = (
        Index("idx_pred_outcomes_pending", "target_date"),
        {"schema": "ml"}
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    prediction_id = Column(UUID(as_uuid=True), ForeignKey("analysis.predictions.id"), nullable=True)
    model_id = Column(UUID(as_uuid=True), ForeignKey("ml.model_metadata.id"), nullable=True)
    ticker = Column(String(10), nullable=False)
    prediction_date = Column(Date, nullable=False)
    target_date = Column(Date, nullable=False)
    
    predicted_return = Column(Numeric(8, 4), nullable=False)
    predicted_direction = Column(String(10), nullable=False) # 'positive', 'negative'
    predicted_probability = Column(Numeric(6, 4))
    
    # Filled after target_date has elapsed
    actual_return = Column(Numeric(8, 4), nullable=True)
    actual_direction = Column(String(10), nullable=True)
    direction_correct = Column(Boolean, nullable=True)
    return_error = Column(Numeric(8, 4), nullable=True)
    absolute_error = Column(Numeric(8, 4), nullable=True)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    outcome_recorded_at = Column(DateTime(timezone=True), nullable=True)

    model = relationship("ModelMetadata", back_populates="prediction_outcomes")


class ModelDriftMonitoring(Base):
    __tablename__ = "model_drift_monitoring"
    __table_args__ = ({"schema": "ml"})

    id = Column(Integer, primary_key=True, autoincrement=True)
    model_id = Column(UUID(as_uuid=True), ForeignKey("ml.model_metadata.id"), nullable=False)
    check_date = Column(Date, nullable=False)
    
    feature_name = Column(String(100), nullable=True)
    train_mean = Column(Numeric(12, 6))
    train_std = Column(Numeric(12, 6))
    current_mean = Column(Numeric(12, 6))
    current_std = Column(Numeric(12, 6))
    ks_statistic = Column(Numeric(8, 6))
    ks_p_value = Column(Numeric(8, 6))
    is_drifting = Column(Boolean, default=False)
    
    recent_accuracy_14d = Column(Numeric(6, 4))
    baseline_accuracy = Column(Numeric(6, 4))
    accuracy_degradation = Column(Numeric(6, 4))
    requires_retrain = Column(Boolean, default=False)
    alert_sent = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    model = relationship("ModelMetadata", back_populates="drift_checks")
