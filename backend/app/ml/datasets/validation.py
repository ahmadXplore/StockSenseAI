"""
StockSense AI — Data Sufficiency Checker
Ensures minimum historical depth and feature completeness before permitting model training.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Dict, Any
import pandas as pd


@dataclass
class DataSufficiencyResult:
    is_sufficient: bool
    status: str              # 'PASSED', 'INSUFFICIENT_TRAINING_DATA'
    history_days: int
    row_count: int
    feature_completeness_pct: float
    reason: Optional[str] = None
    metrics: Dict[str, Any] = None


def verify_data_sufficiency(
    features_df: pd.DataFrame,
    min_history_days: int = 60,
    min_training_rows: int = 40,
    min_completeness_pct: float = 75.0
) -> DataSufficiencyResult:
    """
    Blocks model training if data volume or history depth is insufficient.
    Guarantees no invalid or fabricated model training occurs.
    """
    if features_df is None or features_df.empty:
        return DataSufficiencyResult(
            is_sufficient=False,
            status="INSUFFICIENT_TRAINING_DATA",
            history_days=0,
            row_count=0,
            feature_completeness_pct=0.0,
            reason="Feature DataFrame is completely empty."
        )

    row_count = len(features_df)
    
    # Calculate days span if index is datetime
    if hasattr(features_df.index, "min") and hasattr(features_df.index, "max"):
        try:
            span = (features_df.index.max() - features_df.index.min()).days
        except Exception:
            span = row_count
    else:
        span = row_count

    # Calculate overall non-null completeness
    completeness = (1.0 - features_df.isna().mean().mean()) * 100.0

    errors = []
    if row_count < min_training_rows:
        errors.append(f"Row count ({row_count}) < minimum required ({min_training_rows})")
    if span < min_history_days:
        errors.append(f"Historical span ({span} days) < minimum required ({min_history_days} days)")
    if completeness < min_completeness_pct:
        errors.append(f"Feature completeness ({completeness:.1f}%) < minimum ({min_completeness_pct}%)")

    is_sufficient = len(errors) == 0
    status = "PASSED" if is_sufficient else "INSUFFICIENT_TRAINING_DATA"
    reason = "; ".join(errors) if errors else None

    return DataSufficiencyResult(
        is_sufficient=is_sufficient,
        status=status,
        history_days=span,
        row_count=row_count,
        feature_completeness_pct=round(completeness, 2),
        reason=reason,
        metrics={"row_count": row_count, "span_days": span, "completeness_pct": round(completeness, 2)}
    )
