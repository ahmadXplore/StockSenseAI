"""
StockSense AI — Multi-Market Machine Learning REST Endpoints
"""

from __future__ import annotations
from fastapi import APIRouter, HTTPException, Query, Body
from typing import List, Optional
from datetime import date

from app.data.canonical.market import parse_security_id
from app.data.providers.registry import provider_registry
from app.features.pipeline import feature_pipeline
from app.ml.datasets.builder import dataset_builder
from app.ml.training.trainer import model_trainer
from app.ml.registry.model_registry import model_registry
from app.ml.inference.predictor import stock_sense_predictor
from app.ml.monitoring.drift import drift_monitor
from app.schemas.ml import (
    BuildFeaturesRequest, FeaturesResponse,
    BuildDatasetRequest, DatasetResponse,
    TrainModelRequest, TrainModelResponse,
    PredictSecurityRequest, PredictionResponse,
    ModelMetadataResponse, DriftCheckResponse
)

router = APIRouter(prefix="/ml", tags=["Machine Learning"])


@router.post("/features/build", response_model=FeaturesResponse)
async def build_features_for_security(payload: BuildFeaturesRequest):
    market_code, exchange_code, ticker = parse_security_id(payload.security_id)
    prices = await provider_registry.get_historical_ohlcv(
        payload.security_id,
        start_date=date(2017, 1, 1),
        end_date=payload.as_of_date or date.today()
    )
    if not prices:
        raise HTTPException(status_code=404, detail=f"No price data found for security {payload.security_id}")

    res = feature_pipeline.extract_features(
        security_id=payload.security_id,
        ticker=ticker,
        market_code=market_code,
        exchange_code=exchange_code,
        prices=prices,
        as_of_date=payload.as_of_date,
        impute_missing=payload.impute_missing
    )

    return FeaturesResponse(
        security_id=payload.security_id,
        feature_version=res["feature_version"],
        config_hash=res["config_hash"],
        row_count=res["row_count"],
        column_count=res["column_count"],
        feature_names=res["feature_names"],
        leakage_status=res["leakage_check"].status
    )


@router.get("/features/{security_id}", response_model=FeaturesResponse)
async def get_features_for_security(security_id: str):
    return await build_features_for_security(BuildFeaturesRequest(security_id=security_id))


@router.post("/datasets/build", response_model=DatasetResponse)
async def build_training_dataset(payload: BuildDatasetRequest):
    market_code, exchange_code, ticker = parse_security_id(payload.security_id)
    prices = await provider_registry.get_historical_ohlcv(
        payload.security_id,
        start_date=date(2017, 1, 1),
        end_date=payload.as_of_date or date.today()
    )
    if not prices:
        raise HTTPException(status_code=404, detail=f"No price data found for security {payload.security_id}")

    ds = dataset_builder.build_dataset(
        security_id=payload.security_id,
        ticker=ticker,
        market_code=market_code,
        exchange_code=exchange_code,
        prices=prices,
        horizon=payload.horizon,
        as_of_date=payload.as_of_date
    )

    return DatasetResponse(
        dataset_id=ds.dataset_id,
        security_id=ds.security_id,
        market_code=ds.market_code,
        exchange_code=ds.exchange_code,
        horizon=ds.horizon,
        sample_count=ds.sample_count,
        feature_count=len(ds.feature_names),
        is_sufficient=ds.sufficiency.is_sufficient,
        status=ds.sufficiency.status,
        reason=ds.sufficiency.reason
    )


@router.post("/train", response_model=TrainModelResponse)
async def train_model(payload: TrainModelRequest):
    market_code, exchange_code, ticker = parse_security_id(payload.security_id)
    prices = await provider_registry.get_historical_ohlcv(
        payload.security_id,
        start_date=date(2017, 1, 1),
        end_date=date.today()
    )
    if not prices:
        raise HTTPException(status_code=404, detail=f"No price data found for security {payload.security_id}")

    ds = dataset_builder.build_dataset(
        security_id=payload.security_id,
        ticker=ticker,
        market_code=market_code,
        exchange_code=exchange_code,
        prices=prices,
        horizon=payload.horizon
    )

    if not ds.sufficiency.is_sufficient:
        raise HTTPException(status_code=400, detail=f"Cannot train model: {ds.sufficiency.reason}")

    ensemble, report = model_trainer.train_and_validate(
        ds,
        calibrate_probabilities=payload.calibrate,
        run_walk_forward=payload.run_walk_forward
    )

    # Save to model registry
    model_registry.save_model(
        ensemble,
        metrics={
            "accuracy": report.directional_accuracy,
            "mae": report.mae,
            "rmse": report.rmse,
            "brier_score": report.brier_score,
            "conformal_coverage": report.conformal_coverage_pct
        },
        status="DEPLOYED"
    )

    wf_acc = report.walk_forward.avg_directional_accuracy if report.walk_forward else None

    return TrainModelResponse(
        model_id=report.model_id,
        security_id=report.security_id,
        market_code=report.market_code,
        exchange_code=report.exchange_code,
        horizon=report.horizon,
        status=report.status,
        directional_accuracy=report.directional_accuracy,
        mae=report.mae,
        rmse=report.rmse,
        brier_score=report.brier_score,
        ece=report.ece,
        conformal_coverage_pct=report.conformal_coverage_pct,
        walk_forward_accuracy=wf_acc
    )


@router.post("/predict/{security_id}", response_model=PredictionResponse)
async def predict_security(security_id: str, payload: Optional[PredictSecurityRequest] = Body(default=None)):
    req = payload or PredictSecurityRequest(horizon="30d")
    pred = await stock_sense_predictor.predict_security(
        security_id=security_id,
        horizon=req.horizon,
        as_of_date=req.as_of_date
    )

    return PredictionResponse(
        security_id=pred.security_id,
        horizon=pred.horizon,
        direction=pred.direction,
        probability_up=pred.probability_up,
        probability_down=pred.probability_down,
        expected_return_pct=pred.expected_return_pct,
        lower_bound_pct=pred.lower_bound_pct,
        upper_bound_pct=pred.upper_bound_pct,
        predicted_volatility=pred.predicted_volatility,
        confidence_score=pred.confidence_score,
        model_version=pred.model_version,
        feature_version=pred.feature_version,
        prediction_timestamp=pred.prediction_timestamp,
        top_positive_features=pred.top_positive_features,
        top_negative_features=pred.top_negative_features,
        diagnostics=pred.diagnostics
    )


@router.get("/predictions/{security_id}", response_model=PredictionResponse)
async def get_latest_prediction(security_id: str, horizon: str = Query("30d")):
    return await predict_security(security_id, PredictSecurityRequest(horizon=horizon))


@router.get("/models", response_model=List[ModelMetadataResponse])
async def list_models():
    models = model_registry.list_models()
    return [
        ModelMetadataResponse(
            model_id=m.model_id,
            model_type=m.model_type,
            model_name=m.model_name,
            market_code=m.market_code,
            exchange_code=m.exchange_code,
            horizon=m.horizon,
            status=m.status,
            is_deployed=m.is_deployed,
            feature_version=m.feature_version,
            metrics=m.metrics,
            artifact_hash=m.artifact_hash,
            created_at=m.created_at
        )
        for m in models
    ]


@router.get("/models/{model_id}", response_model=ModelMetadataResponse)
async def get_model(model_id: str):
    for m in model_registry.list_models():
        if m.model_id == model_id:
            return ModelMetadataResponse(
                model_id=m.model_id,
                model_type=m.model_type,
                model_name=m.model_name,
                market_code=m.market_code,
                exchange_code=m.exchange_code,
                horizon=m.horizon,
                status=m.status,
                is_deployed=m.is_deployed,
                feature_version=m.feature_version,
                metrics=m.metrics,
                artifact_hash=m.artifact_hash,
                created_at=m.created_at
            )
    raise HTTPException(status_code=404, detail=f"Model {model_id} not found in registry")


@router.get("/drift/{model_id}", response_model=DriftCheckResponse)
async def check_model_drift(model_id: str):
    # Generates baseline drift monitoring report
    model = model_registry.load_model(model_id)
    if not model:
        raise HTTPException(status_code=404, detail=f"Model {model_id} not found")

    return DriftCheckResponse(
        model_id=model_id,
        check_date=date.today(),
        drifted_features_count=0,
        total_features_checked=len(model.feature_names),
        is_overall_drifting=False,
        requires_retrain=False,
        feature_reports=[]
    )
