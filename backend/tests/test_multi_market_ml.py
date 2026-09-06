"""
CRITICAL MULTI-MARKET ML INTEGRATION TEST (Section 40)
Validates that PK.PSX.ENGRO and US.NASDAQ.AAPL pass through the EXACT SAME
Canonical Data -> Feature Engineering -> Dataset Builder -> Model -> Prediction pipeline.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import date

from app.data.canonical.price import CanonicalPriceDTO
from app.features.pipeline import feature_pipeline
from app.ml.datasets.builder import dataset_builder
from app.ml.training.trainer import model_trainer
from app.ml.inference.predictor import stock_sense_predictor


def generate_mock_canonical_prices(security_id: str, market_code: str, currency: str, n_days: int = 150):
    prices = []
    base_price = 300.0 if currency == "PKR" else 180.0
    start_dt = date(2023, 1, 1)
    dates = pd.date_range(start_dt, periods=n_days, freq="B")
    
    np.random.seed(hash(security_id) % 10000)
    current = base_price
    for dt in dates:
        ret = np.random.normal(0.0005, 0.02)
        close = round(max(10.0, current * (1.0 + ret)), 2)
        high = round(close * 1.015, 2)
        low = round(close * 0.985, 2)
        open_p = round((high + low) / 2.0, 2)
        volume = int(np.random.uniform(50000, 500000))
        
        ticker = security_id.split(".")[-1]
        prices.append(CanonicalPriceDTO(
            security_id=security_id,
            ticker=ticker,
            timestamp=dt.to_pydatetime(),
            open=open_p,
            high=high,
            low=low,
            close=close,
            adj_close=close,
            volume=volume,
            currency=currency,
            data_source="canonical_test"
        ))
        current = close
    return prices


@pytest.mark.asyncio
async def test_multi_market_parity_engro_and_aapl():
    # 1. Generate Canonical Prices for Pakistan (ENGRO in PKR) and US (AAPL in USD)
    engro_prices = generate_mock_canonical_prices("PK.PSX.ENGRO", "PK", "PKR", 150)
    aapl_prices = generate_mock_canonical_prices("US.NASDAQ.AAPL", "US", "USD", 150)

    # 2. Build Datasets using Shared DatasetBuilder
    ds_engro = dataset_builder.build_dataset(
        security_id="PK.PSX.ENGRO",
        ticker="ENGRO",
        market_code="PK",
        exchange_code="PSX",
        prices=engro_prices,
        horizon="30d"
    )

    ds_aapl = dataset_builder.build_dataset(
        security_id="US.NASDAQ.AAPL",
        ticker="AAPL",
        market_code="US",
        exchange_code="NASDAQ",
        prices=aapl_prices,
        horizon="30d"
    )

    assert ds_engro.sufficiency.is_sufficient is True
    assert ds_aapl.sufficiency.is_sufficient is True
    assert len(ds_engro.feature_names) == len(ds_aapl.feature_names)

    # 3. Train Models using Shared ModelTrainer
    ensemble_engro, rep_engro = model_trainer.train_and_validate(ds_engro)
    ensemble_aapl, rep_aapl = model_trainer.train_and_validate(ds_aapl)

    assert rep_engro.status == "VALIDATED"
    assert rep_aapl.status == "VALIDATED"

    # 4. Generate Predictions using Shared StockSensePredictor
    pred_engro = await stock_sense_predictor.predict_security("PK.PSX.ENGRO", horizon="30d", prices=engro_prices)
    pred_aapl = await stock_sense_predictor.predict_security("US.NASDAQ.AAPL", horizon="30d", prices=aapl_prices)

    assert pred_engro.security_id == "PK.PSX.ENGRO"
    assert pred_aapl.security_id == "US.NASDAQ.AAPL"
    assert pred_engro.direction in ["UP", "DOWN", "NEUTRAL"]
    assert pred_aapl.direction in ["UP", "DOWN", "NEUTRAL"]
    assert 0.0 <= pred_engro.confidence_score <= 100.0
    assert 0.0 <= pred_aapl.confidence_score <= 100.0
    assert pred_engro.lower_bound_pct <= pred_engro.upper_bound_pct
    assert pred_aapl.lower_bound_pct <= pred_aapl.upper_bound_pct
