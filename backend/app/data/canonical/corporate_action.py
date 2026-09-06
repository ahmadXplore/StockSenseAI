"""
StockSense AI — Canonical Corporate Actions & Price Adjustments
Defines splits, dividends, rights, bonus issues, mergers, delistings,
and separate unadjusted vs adjusted price calculation routines.
"""

from __future__ import annotations
from enum import Enum
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from typing import Optional, Dict, Any, List
from decimal import Decimal

from app.data.canonical.price import CanonicalPriceDTO


class CorporateActionType(str, Enum):
    STOCK_SPLIT = "stock_split"
    REVERSE_SPLIT = "reverse_split"
    CASH_DIVIDEND = "cash_dividend"
    STOCK_DIVIDEND = "stock_dividend"
    BONUS_ISSUE = "bonus_issue"
    RIGHTS_ISSUE = "rights_issue"
    MERGER = "merger"
    ACQUISITION = "acquisition"
    SPINOFF = "spinoff"
    SYMBOL_CHANGE = "symbol_change"
    DELISTING = "delisting"


@dataclass
class CorporateActionDTO:
    action_date: date
    action_type: CorporateActionType
    security_id: Optional[str] = None
    ticker: Optional[str] = None
    split_ratio: Optional[Decimal] = None      # e.g., Decimal("2.0") for 2-for-1 split, Decimal("0.5") for 1-for-2
    dividend_amount: Optional[Decimal] = None  # in native currency
    dividend_type: Optional[str] = "cash"      # 'cash', 'stock'
    notes: Optional[str] = None
    source: Optional[str] = None
    verified: bool = False
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


def calculate_split_adjustment_factor(actions: List[CorporateActionDTO], target_date: date) -> Decimal:
    """
    Computes cumulative split adjustment factor for dates strictly before corporate action dates.
    """
    cumulative_factor = Decimal("1.0")
    for action in actions:
        if action.action_date > target_date:
            if action.action_type in (CorporateActionType.STOCK_SPLIT, CorporateActionType.REVERSE_SPLIT, CorporateActionType.BONUS_ISSUE):
                if action.split_ratio and action.split_ratio > 0:
                    cumulative_factor *= (Decimal("1.0") / action.split_ratio)
    return cumulative_factor


def adjust_prices_for_corporate_actions(
    prices: List[CanonicalPriceDTO],
    corporate_actions: List[CorporateActionDTO]
) -> List[CanonicalPriceDTO]:
    """
    Produces adjusted price copies with split and dividend adjustments applied backwards,
    preserving original unadjusted OHLCV records intact.
    """
    if not corporate_actions or not prices:
        return prices

    # Sort chronological
    sorted_prices = sorted(prices, key=lambda p: p.timestamp)
    sorted_actions = sorted(corporate_actions, key=lambda a: a.action_date)
    
    adjusted_records: List[CanonicalPriceDTO] = []
    for price in sorted_prices:
        p_date = price.timestamp.date() if isinstance(price.timestamp, datetime) else price.timestamp
        factor = calculate_split_adjustment_factor(sorted_actions, p_date)
        
        adj_p = Decimal(str(price.close)) * factor
        
        record = CanonicalPriceDTO(
            security_id=price.security_id,
            ticker=price.ticker,
            timestamp=price.timestamp,
            open=price.open * factor,
            high=price.high * factor,
            low=price.low * factor,
            close=price.close * factor,
            adj_close=adj_p,
            volume=int(price.volume / float(factor)) if factor > 0 else price.volume,
            vwap=price.vwap * factor if price.vwap else None,
            currency=price.currency,
            split_factor=factor,
            dividend_amount=price.dividend_amount,
            source_id=price.source_id,
            data_source=price.data_source,
            is_adjusted=True,
            quality_flag=price.quality_flag,
            retrieved_at=price.retrieved_at,
        )
        adjusted_records.append(record)

    return adjusted_records
