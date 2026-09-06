"""
StockSense AI — Training Dataset Builder
Assembles aligned, point-in-time training matrices (X) and multi-horizon target labels (y).
"""

from __future__ import annotations
import uuid
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from typing import Optional, List, Dict, Any, Tuple
import pandas as pd
import numpy as np

from app.data.canonical.price import CanonicalPriceDTO
from app.features.pipeline import feature_pipeline
from app.ml.datasets.labels import generate_time_series_labels
from app.ml.datasets.validation import verify_data_sufficiency, DataSufficiencyResult


@dataclass
class TrainingDataset:
    dataset_id: str
    security_id: str
    market_code: str
    exchange_code: str
    horizon: str
    feature_names: List[str]
    X: pd.DataFrame
    y_direction: pd.Series
    y_return: pd.Series
    y_volatility: pd.Series
    sufficiency: DataSufficiencyResult
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def sample_count(self) -> int:
        return len(self.X)


class DatasetBuilder:
    """
    Constructs reproducible, point-in-time aligned training datasets for ML models.
    """

    def build_dataset(
        self,
        security_id: str,
        ticker: str,
        market_code: str,
        exchange_code: str,
        prices: List[CanonicalPriceDTO],
        horizon: str = "30d",
        fundamentals_df: Optional[pd.DataFrame] = None,
        macro_df: Optional[pd.DataFrame] = None,
        news_df: Optional[pd.DataFrame] = None,
        benchmark_df: Optional[pd.DataFrame] = None,
        as_of_date: Optional[date] = None,
    ) -> TrainingDataset:
        dataset_id = str(uuid.uuid4())

        # 1. Extract Features
        feat_res = feature_pipeline.extract_features(
            security_id=security_id,
            ticker=ticker,
            market_code=market_code,
            exchange_code=exchange_code,
            prices=prices,
            fundamentals_df=fundamentals_df,
            macro_df=macro_df,
            news_df=news_df,
            benchmark_df=benchmark_df,
            as_of_date=as_of_date
        )
        features_df = feat_res["features_df"]

        # 2. Check Data Sufficiency
        sufficiency = verify_data_sufficiency(features_df)
        if not sufficiency.is_sufficient:
            return TrainingDataset(
                dataset_id=dataset_id,
                security_id=security_id,
                market_code=market_code,
                exchange_code=exchange_code,
                horizon=horizon,
                feature_names=[],
                X=pd.DataFrame(),
                y_direction=pd.Series(dtype=float),
                y_return=pd.Series(dtype=float),
                y_volatility=pd.Series(dtype=float),
                sufficiency=sufficiency
            )

        # 3. Generate Labels
        price_rows = [{"timestamp": p.timestamp, "close": float(p.close)} for p in prices]
        p_df = pd.DataFrame(price_rows).set_index("timestamp").sort_index()
        labels_df = generate_time_series_labels(p_df, horizon=horizon)

        # 4. Align X and y on index and drop NaNs in target labels (future unobserved period)
        h_key = horizon.lower()
        aligned = pd.concat([features_df, labels_df], axis=1).dropna(subset=[f"target_return_{h_key}"])

        feature_cols = [c for c in features_df.columns if c in aligned.columns]
        X = aligned[feature_cols].copy()
        y_dir = aligned[f"target_direction_{h_key}"].astype(int)
        y_ret = aligned[f"target_return_{h_key}"].astype(float)
        y_vol = aligned[f"target_volatility_{h_key}"].astype(float)

        return TrainingDataset(
            dataset_id=dataset_id,
            security_id=security_id,
            market_code=market_code,
            exchange_code=exchange_code,
            horizon=horizon,
            feature_names=feature_cols,
            X=X,
            y_direction=y_dir,
            y_return=y_ret,
            y_volatility=y_vol,
            sufficiency=sufficiency
        )


dataset_builder = DatasetBuilder()
