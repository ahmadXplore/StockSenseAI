"""
StockSense AI — Corporate Action Validator
Validates split ratios, dividend payments, and event timestamps.
"""

from __future__ import annotations
from typing import List, Tuple
from decimal import Decimal
from app.data.canonical.corporate_action import CorporateActionDTO, CorporateActionType


def validate_corporate_action(action: CorporateActionDTO) -> Tuple[bool, List[str]]:
    """
    Validates a corporate action record.
    """
    errors: List[str] = []

    if action.action_type in (CorporateActionType.STOCK_SPLIT, CorporateActionType.REVERSE_SPLIT, CorporateActionType.BONUS_ISSUE):
        if not action.split_ratio or action.split_ratio <= 0:
            errors.append(f"Invalid split ratio for {action.action_type}: {action.split_ratio}")

    if action.action_type == CorporateActionType.CASH_DIVIDEND:
        if action.dividend_amount is not None and action.dividend_amount < 0:
            errors.append(f"Negative dividend amount: {action.dividend_amount}")

    return len(errors) == 0, errors
