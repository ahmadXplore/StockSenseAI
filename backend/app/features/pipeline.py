"""
StockSense AI — Master Feature Engineering Pipeline
Coordinates multi-market feature extraction, point-in-time alignment, and leakage checks.
"""

from __future__ import annotations
import pandas as pd
from datetime import date, datetime, timezone
from typing import Optional, List, Dict, Any

from app.data.canonical.price import CanonicalPriceDTO
from app.features.base import FeatureContext, FeatureCategory
from app.features.registry import feature_registry
from app.features.versioning import FeatureVersionConfig
from app.features.validation.leakage import check_feature_matrix_leakage, LeakageCheckResult
from app.features.validation.missingness import impute_features_safely


class FeaturePipeline:
    """
    Master pipeline that executes feature extraction for any global security.
    """

    def __init__(self, version: str = "1.0.0"):
        self.version = version

    def extract_features(
        self,
        security_id: str,
        ticker: str,
        market_code: str,
        exchange_code: str,
        prices: List[CanonicalPriceDTO],
        fundamentals_df: Optional[pd.DataFrame] = None,
        macro_df: Optional[pd.DataFrame] = None,
        news_df: Optional[pd.DataFrame] = None,
        benchmark_df: Optional[pd.DataFrame] = None,
        as_of_date: Optional[date] = None,
        impute_missing: bool = True
    ) -> Dict[str, Any]:
        """
        Builds complete feature matrix for a security from canonical records.
        """
        if not prices:
            return {
                "features_df": pd.DataFrame(),
                "feature_version": self.version,
                "config_hash": "",
                "leakage_check": LeakageCheckResult(has_leakage=False, status="EMPTY")
            }

        # Convert CanonicalPriceDTO list to DataFrame indexed by timestamp
        price_rows = []
        for p in prices:
            price_rows.append({
                "timestamp": p.timestamp,
                "open": float(p.open),
                "high": float(p.high),
                "low": float(p.low),
                "close": float(p.close),
                "adj_close": float(p.adj_close),
                "volume": p.volume,
            })
        
        price_df = pd.DataFrame(price_rows)
        price_df["timestamp"] = pd.to_datetime(price_df["timestamp"])
        price_df = price_df.sort_values("timestamp").set_index("timestamp")

        # Point-in-time filter up to as_of_date
        if as_of_date is not None:
            price_df = price_df[price_df.index.to_series().apply(lambda dt: dt.date() <= as_of_date)]

        context = FeatureContext(
            security_id=security_id,
            ticker=ticker,
            market_code=market_code,
            exchange_code=exchange_code,
            as_of_date=as_of_date,
            price_df=price_df,
            fundamentals_df=fundamentals_df,
            macro_df=macro_df,
            news_df=news_df,
            benchmark_df=benchmark_df
        )

        # Compute all registered features
        raw_features_df = feature_registry.compute_all(context)

        # Impute missing values if requested
        if impute_missing and not raw_features_df.empty:
            features_df, stats = impute_features_safely(raw_features_df)
        else:
            features_df = raw_features_df

        # Run automated leakage scan
        leakage_check = check_feature_matrix_leakage(features_df, as_of_date=as_of_date)

        # Generate version config & reproducibility hash
        version_config = FeatureVersionConfig(
            feature_set_id=f"{market_code}_{exchange_code}_{ticker}",
            version=self.version,
            feature_names=list(features_df.columns),
            extractor_parameters={"as_of_date": str(as_of_date) if as_of_date else "latest"}
        )

        return {
            "features_df": features_df,
            "feature_version": self.version,
            "config_hash": version_config.config_hash,
            "feature_names": list(features_df.columns),
            "leakage_check": leakage_check,
            "row_count": len(features_df),
            "column_count": len(features_df.columns)
        }


feature_pipeline = FeaturePipeline()
