"""
StockSense AI — Master Multi-Market Prediction Engine
Serves point-in-time inference, conformal bounds, and explainable signals for any global security.
"""

from __future__ import annotations
from typing import Optional, Dict, Any, List
from datetime import date, datetime, timezone
import pandas as pd

from app.data.canonical.price import CanonicalPriceDTO
from app.data.canonical.market import parse_security_id
from app.data.providers.registry import provider_registry
from app.features.pipeline import feature_pipeline
from app.ml.datasets.builder import dataset_builder
from app.ml.models.base import PredictionResult
from app.ml.models.ensemble import StockSenseEnsemble
from app.ml.training.trainer import model_trainer
from app.ml.registry.model_registry import model_registry


class StockSensePredictor:
    """
    High-level prediction service serving multi-market forecasts with fast in-memory caching.
    """

    def __init__(self):
        self._models_cache: Dict[str, BaseStockModel] = {}
        self._pred_cache: Dict[str, Any] = {}

    async def predict_security(
        self,
        security_id: str,
        horizon: str = "30d",
        as_of_date: Optional[date] = None,
        prices: Optional[List[CanonicalPriceDTO]] = None
    ) -> PredictionResult:
        cache_key = f"{security_id}_{horizon}_{as_of_date or date.today()}"
        if cache_key in self._pred_cache:
            ts, cached_pred = self._pred_cache[cache_key]
            if datetime.now().timestamp() - ts < 120.0:  # 2 minute cache
                return cached_pred

        market_code, exchange_code, ticker = parse_security_id(security_id)

        # 1. Fetch prices if not provided (2 years lookback is optimal and fast)
        if not prices:
            from datetime import timedelta
            lookback_date = (as_of_date or date.today()) - timedelta(days=730)
            prices = await provider_registry.get_historical_ohlcv(
                security_id=security_id,
                start_date=lookback_date,
                end_date=as_of_date or date.today()
            )

        if not prices or len(prices) < 20:
            # Insufficient data fallback
            return PredictionResult(
                security_id=security_id,
                horizon=horizon,
                direction="NEUTRAL",
                probability_up=0.50,
                probability_down=0.50,
                expected_return_pct=0.0,
                lower_bound_pct=-5.0,
                upper_bound_pct=5.0,
                predicted_volatility=20.0,
                confidence_score=30.0,
                model_version="fallback_1.0.0",
                feature_version="1.0.0",
                diagnostics={"status": "INSUFFICIENT_TRAINING_DATA"}
            )

        # 2. Extract features
        feat_res = feature_pipeline.extract_features(
            security_id=security_id,
            ticker=ticker,
            market_code=market_code,
            exchange_code=exchange_code,
            prices=prices,
            as_of_date=as_of_date
        )
        features_df = feat_res["features_df"]

        # 3. Resolve or train model
        model_cache_key = f"{market_code}_{exchange_code}_{horizon}"
        model = self._models_cache.get(model_cache_key)
        if model is None:
            model = model_registry.get_deployed_model(market_code, exchange_code, horizon=horizon)
            if model is not None:
                self._models_cache[model_cache_key] = model
        if model is None:
            # Build training dataset and train model
            ds = dataset_builder.build_dataset(
                security_id=security_id,
                ticker=ticker,
                market_code=market_code,
                exchange_code=exchange_code,
                prices=prices,
                horizon=horizon,
                as_of_date=as_of_date
            )
            if ds.sufficiency.is_sufficient and ds.sample_count >= 30:
                ensemble, report = model_trainer.train_and_validate(
                    ds,
                    calibrate_probabilities=True,
                    run_walk_forward=False
                )
                model_registry.save_model(
                    ensemble,
                    metrics={"accuracy": report.directional_accuracy, "mae": report.mae},
                    status="DEPLOYED"
                )
                model = ensemble
            else:
                # Insufficient data safety fallback
                return PredictionResult(
                    security_id=security_id,
                    horizon=horizon,
                    direction="NEUTRAL",
                    probability_up=0.50,
                    probability_down=0.50,
                    expected_return_pct=0.0,
                    lower_bound_pct=-5.0,
                    upper_bound_pct=5.0,
                    predicted_volatility=20.0,
                    confidence_score=30.0,
                    model_version="1.0.0",
                    feature_version=feat_res["feature_version"],
                    diagnostics={"status": "INSUFFICIENT_TRAINING_DATA", "reason": ds.sufficiency.reason}
                )

        # 4. Generate structured prediction
        if isinstance(model, StockSenseEnsemble):
            pred = model.predict_structured(
                security_id=security_id,
                X=features_df,
                feature_version=feat_res["feature_version"]
            )
        else:
            # Generic model prediction
            exp_ret = float(model.predict(features_df.iloc[[-1]])[0] * 100.0)
            pred = PredictionResult(
                security_id=security_id,
                horizon=horizon,
                direction="UP" if exp_ret >= 0 else "DOWN",
                probability_up=0.60 if exp_ret >= 0 else 0.40,
                probability_down=0.40 if exp_ret >= 0 else 0.60,
                expected_return_pct=round(exp_ret, 2),
                lower_bound_pct=round(exp_ret - 5.0, 2),
                upper_bound_pct=round(exp_ret + 5.0, 2),
                predicted_volatility=20.0,
                confidence_score=60.0,
                model_version=model.version,
                feature_version=feat_res["feature_version"]
            )

        self._pred_cache[cache_key] = (datetime.now().timestamp(), pred)
        return pred


stock_sense_predictor = StockSensePredictor()
