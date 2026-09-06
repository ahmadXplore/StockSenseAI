"""
StockSense AI — Feature Leakage & Look-Ahead Detection Engine
Scans generated feature matrices to detect and block look-ahead leakage and future target contamination.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import List, Dict, Any, Optional
import numpy as np
import pandas as pd


@dataclass
class LeakageCheckResult:
    has_leakage: bool
    status: str              # 'PASSED', 'BLOCKED_LEAKAGE_DETECTED'
    violations: List[str] = field(default_factory=list)
    tested_features_count: int = 0
    max_target_correlation: float = 0.0
    details: Dict[str, Any] = field(default_factory=dict)


def check_feature_matrix_leakage(
    features_df: pd.DataFrame,
    target_series: Optional[pd.Series] = None,
    as_of_date: Optional[date] = None,
    correlation_threshold: float = 0.99
) -> LeakageCheckResult:
    """
    Automated safety gate scanning for look-ahead bias and target leakage.
    Blocks model training if leakage is detected.
    """
    if features_df is None or features_df.empty:
        return LeakageCheckResult(
            has_leakage=False,
            status="PASSED",
            tested_features_count=0
        )

    violations: List[str] = []
    max_corr = 0.0

    # 1. Check for future timestamp observations if as_of_date is provided
    if as_of_date is not None:
        for idx in features_df.index:
            row_d = idx.date() if hasattr(idx, "date") else idx
            if isinstance(row_d, date) and row_d > as_of_date:
                violations.append(f"Future observation detected: index {row_d} is after as_of_date {as_of_date}")
                break

    # 2. Check for exact or near-perfect correlation with future target (target leakage)
    if target_series is not None and not target_series.empty:
        clean_target = target_series.reindex(features_df.index).astype(float)
        
        for col in features_df.columns:
            # Skip non-numeric
            if not np.issubdtype(features_df[col].dtype, np.number):
                continue
            
            s = features_df[col].astype(float)
            if s.std() == 0 or clean_target.std() == 0:
                continue

            corr = float(abs(s.corr(clean_target)))
            if not np.isnan(corr):
                max_corr = max(max_corr, corr)
                if corr >= correlation_threshold:
                    violations.append(
                        f"Target leakage detected in feature '{col}': Correlation with target is {corr:.4f} >= {correlation_threshold}"
                    )

    has_leakage = len(violations) > 0
    status = "BLOCKED_LEAKAGE_DETECTED" if has_leakage else "PASSED"

    return LeakageCheckResult(
        has_leakage=has_leakage,
        status=status,
        violations=violations,
        tested_features_count=len(features_df.columns),
        max_target_correlation=round(max_corr, 4),
        details={"features_checked": list(features_df.columns)[:20]}
    )
