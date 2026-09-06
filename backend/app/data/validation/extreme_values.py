"""
StockSense AI — Extreme Value & Return Anomaly Detection
Classifies large price movements without destructive deletions.
"""

from __future__ import annotations
from enum import Enum
from dataclasses import dataclass
from typing import List, Optional, Dict
from decimal import Decimal
from datetime import date

from app.data.canonical.price import CanonicalPriceDTO
from app.data.canonical.corporate_action import CorporateActionDTO, CorporateActionType


class ExtremeMoveClassification(str, Enum):
    POSSIBLE_DATA_ERROR = "possible_data_error"
    POSSIBLE_CORPORATE_ACTION = "possible_corporate_action"
    POSSIBLE_MARKET_EVENT = "possible_market_event"
    POSSIBLE_MISSING_ADJUSTMENT = "possible_missing_adjustment"
    POSSIBLE_VALID_EXTREME_MOVE = "possible_valid_extreme_move"
    NORMAL_MOVE = "normal_move"


@dataclass
class AnomalyFlag:
    security_id: str
    date: date
    price_before: Decimal
    price_current: Decimal
    return_pct: float
    classification: ExtremeMoveClassification
    notes: str


def classify_extreme_moves(
    prices: List[CanonicalPriceDTO],
    corporate_actions: Optional[List[CorporateActionDTO]] = None,
    threshold_pct: float = 30.0
) -> List[AnomalyFlag]:
    """
    Evaluates price series for single-day moves exceeding threshold_pct (default 30%).
    Cross-references corporate actions before classifying anomalies.
    """
    flags: List[AnomalyFlag] = []
    if len(prices) < 2:
        return flags

    # Group by security_id
    by_sec: Dict[str, List[CanonicalPriceDTO]] = {}
    for p in prices:
        by_sec.setdefault(p.security_id, []).append(p)

    actions = corporate_actions or []

    for sec_id, sec_prices in by_sec.items():
        sorted_prices = sorted(sec_prices, key=lambda p: p.timestamp)
        sec_actions = [a for a in actions if a.security_id == sec_id or not a.security_id]

        for i in range(1, len(sorted_prices)):
            prev = sorted_prices[i - 1]
            curr = sorted_prices[i]

            if prev.close <= 0:
                continue

            ret_pct = float(((curr.close - prev.close) / prev.close) * 100)
            abs_ret = abs(ret_pct)

            if abs_ret >= threshold_pct:
                curr_date = curr.timestamp.date()
                
                # Check if corporate action exists on or near this date (within 3 days)
                matching_actions = [
                    a for a in sec_actions
                    if abs((a.action_date - curr_date).days) <= 3
                ]

                if matching_actions:
                    action_types = [a.action_type for a in matching_actions]
                    if any(t in (CorporateActionType.STOCK_SPLIT, CorporateActionType.REVERSE_SPLIT, CorporateActionType.BONUS_ISSUE) for t in action_types):
                        classification = ExtremeMoveClassification.POSSIBLE_CORPORATE_ACTION
                        notes = f"Correlated with corporate action: {', '.join(action_types)}"
                    else:
                        classification = ExtremeMoveClassification.POSSIBLE_MISSING_ADJUSTMENT
                        notes = f"Large move near dividend/action: {', '.join(action_types)}"
                elif abs_ret >= 80.0 and curr.volume == 0:
                    classification = ExtremeMoveClassification.POSSIBLE_DATA_ERROR
                    notes = f"Extreme move of {ret_pct:.1f}% with zero traded volume"
                elif abs_ret >= 100.0:
                    classification = ExtremeMoveClassification.POSSIBLE_DATA_ERROR
                    notes = f"Suspect extreme move of {ret_pct:.1f}% without corporate action"
                elif curr.volume > prev.volume * 2:
                    classification = ExtremeMoveClassification.POSSIBLE_VALID_EXTREME_MOVE
                    notes = f"Extreme move of {ret_pct:.1f}% backed by high volume surge"
                else:
                    classification = ExtremeMoveClassification.POSSIBLE_MARKET_EVENT
                    notes = f"Extreme move of {ret_pct:.1f}% flagged for review"

                flags.append(
                    AnomalyFlag(
                        security_id=curr.security_id,
                        date=curr_date,
                        price_before=prev.close,
                        price_current=curr.close,
                        return_pct=ret_pct,
                        classification=classification,
                        notes=notes
                    )
                )

    return flags
