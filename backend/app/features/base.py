"""
StockSense AI — Feature Engineering Base Abstractions
Defines the base contract, context, and metadata for point-in-time feature extractors.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from enum import Enum
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from typing import Dict, Any, List, Optional, Set
import pandas as pd
import numpy as np


class FeatureCategory(str, Enum):
    TECHNICAL = "technical"
    PRICE = "price"
    FUNDAMENTAL = "fundamental"
    MARKET = "market"
    MACRO = "macro"
    SENTIMENT = "sentiment"
    REGIME = "regime"
    CROSS_SECTIONAL = "cross_sectional"


@dataclass
class FeatureMetadata:
    name: str
    category: FeatureCategory
    description: str
    lookback_periods: int = 1
    required_columns: List[str] = field(default_factory=list)
    version: str = "1.0.0"
    dependencies: List[str] = field(default_factory=list)
    market_compatibility: List[str] = field(default_factory=lambda: ["*"]) # '*' means all markets
    is_point_in_time_safe: bool = True
    parameters: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FeatureContext:
    """
    Context passed to feature extractors during calculation.
    Contains time-series price dataframe, fundamentals, macro, and news.
    """
    security_id: str
    ticker: str
    market_code: str
    exchange_code: str
    as_of_date: Optional[date] = None
    price_df: Optional[pd.DataFrame] = None # Expects columns: open, high, low, close, adj_close, volume, timestamp
    fundamentals_df: Optional[pd.DataFrame] = None
    macro_df: Optional[pd.DataFrame] = None
    news_df: Optional[pd.DataFrame] = None
    benchmark_df: Optional[pd.DataFrame] = None
    universe_prices: Optional[Dict[str, pd.DataFrame]] = None


class BaseFeatureExtractor(ABC):
    """
    Abstract base class for all feature extraction routines.
    """

    def __init__(self, metadata: FeatureMetadata):
        self.metadata = metadata

    @abstractmethod
    def compute(self, context: FeatureContext) -> pd.DataFrame:
        """
        Computes feature columns for the given context.
        Returns a DataFrame indexed by timestamp (or aligned with context.price_df index)
        containing computed feature columns.
        """
        pass

    def validate_inputs(self, df: pd.DataFrame) -> bool:
        """Validates that all required columns exist in input DataFrame."""
        if df is None or df.empty:
            return False
        for col in self.metadata.required_columns:
            if col not in df.columns:
                return False
        return True
