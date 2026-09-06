"""
StockSense AI — Data Quality Engine & Audit Report Generator
Computes quality scores and comprehensive health metrics for ingested datasets.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from typing import List, Dict, Optional, Tuple

from app.data.canonical.price import CanonicalPriceDTO
from app.data.canonical.security import SecurityDTO, SecurityStatus
from app.data.canonical.corporate_action import CorporateActionDTO
from app.data.validation.price_validation import validate_price_series
from app.data.validation.extreme_values import classify_extreme_moves, AnomalyFlag


@dataclass
class DataQualityResult:
    provider: str
    market: str
    exchange: str
    date_range: Tuple[Optional[date], Optional[date]]
    securities_count: int
    records_checked: int
    records_accepted: int
    records_rejected: int
    duplicates_count: int
    invalid_values_count: int
    extreme_moves_count: int
    delisted_count: int
    corporate_actions_count: int
    quality_score: float # 0.0 to 100.0
    status: str          # 'PASSED', 'WARNING', 'FAILED'
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    licensing_notes: str = "Free tier / Open data. No commercial redistribution restrictions."
    survivorship_bias_warning: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class DataQualityEngine:
    """
    Evaluates dataset integrity, anomaly prevalence, and completeness.
    """

    def evaluate(
        self,
        provider: str,
        market: str,
        exchange: str,
        prices: List[CanonicalPriceDTO],
        securities: Optional[List[SecurityDTO]] = None,
        corporate_actions: Optional[List[CorporateActionDTO]] = None
    ) -> DataQualityResult:
        records_checked = len(prices)
        accepted, rejected, logs = validate_price_series(prices)
        
        duplicates_count = sum(1 for l in logs if "Duplicate timestamp" in l)
        invalid_count = len(rejected) - duplicates_count

        # Extreme moves analysis
        anomalies = classify_extreme_moves(accepted, corporate_actions)
        extreme_count = len(anomalies)

        # Dates
        min_date = min((p.timestamp.date() for p in accepted), default=None)
        max_date = max((p.timestamp.date() for p in accepted), default=None)

        # Securities & Delisted stats
        sec_list = securities or []
        delisted_count = sum(1 for s in sec_list if s.status == SecurityStatus.DELISTED)
        
        # Calculate Quality Score (100 base)
        # Deduct penalties for rejected records, anomalies, duplicates
        rejection_rate = (len(rejected) / records_checked) if records_checked > 0 else 0.0
        anomaly_rate = (extreme_count / len(accepted)) if accepted else 0.0

        quality_score = 100.0 - (rejection_rate * 50.0) - (anomaly_rate * 20.0) - (min(duplicates_count, 10) * 1.0)
        quality_score = max(0.0, min(100.0, round(quality_score, 2)))

        errors: List[str] = logs[:50] # Top 50 logs
        warnings: List[str] = [
            f"Flagged {a.classification.value} on {a.security_id} ({a.date}): {a.notes}"
            for a in anomalies[:20]
        ]

        if quality_score >= 90.0:
            status = "PASSED"
        elif quality_score >= 70.0:
            status = "WARNING"
        else:
            status = "FAILED"

        survivorship_warning = None
        if delisted_count == 0 and sec_list:
            survivorship_warning = "Dataset contains zero delisted securities — possible survivorship bias."

        return DataQualityResult(
            provider=provider,
            market=market,
            exchange=exchange,
            date_range=(min_date, max_date),
            securities_count=len(sec_list),
            records_checked=records_checked,
            records_accepted=len(accepted),
            records_rejected=len(rejected),
            duplicates_count=duplicates_count,
            invalid_values_count=invalid_count,
            extreme_moves_count=extreme_count,
            delisted_count=delisted_count,
            corporate_actions_count=len(corporate_actions or []),
            quality_score=quality_score,
            status=status,
            errors=errors,
            warnings=warnings,
            licensing_notes="Free academic / research / local distribution tier.",
            survivorship_bias_warning=survivorship_warning
        )


data_quality_engine = DataQualityEngine()
