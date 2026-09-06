"""
StockSense AI — Database & Domain Enums
"""

from enum import Enum


class AnalysisJobStatus(str, Enum):
    PENDING = "PENDING"
    FETCHING_PRICE = "FETCHING_PRICE"
    FETCHING_FUNDAMENTALS = "FETCHING_FUNDAMENTALS"
    FETCHING_NEWS = "FETCHING_NEWS"
    RUNNING_TECHNICALS = "RUNNING_TECHNICALS"
    RUNNING_SENTIMENT = "RUNNING_SENTIMENT"
    RUNNING_ML = "RUNNING_ML"
    RUNNING_RISK = "RUNNING_RISK"
    RUNNING_VALUATION = "RUNNING_VALUATION"
    RUNNING_SCENARIOS = "RUNNING_SCENARIOS"
    RUNNING_RULES = "RUNNING_RULES"
    GENERATING_REPORT = "GENERATING_REPORT"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class RecommendationSignal(str, Enum):
    STRONG_BUY = "STRONG BUY"
    BUY = "BUY"
    HOLD = "HOLD"
    HIGH_RISK_BUY = "HIGH-RISK BUY"
    AVOID = "AVOID"
    STRONG_AVOID = "STRONG AVOID"


class PredictionHorizon(str, Enum):
    DAYS_7 = "7d"
    DAYS_30 = "30d"
    MONTHS_3 = "3m"
    MONTHS_6 = "6m"
    YEAR_1 = "1y"
    YEARS_3 = "3y"


class MarketRegimeType(str, Enum):
    BULL = "bull"
    BEAR = "bear"
    HIGH_VOLATILITY = "high_vol"
    LOW_VOLATILITY = "low_vol"
    RATE_SHOCK = "rate_shock"
    RECESSION = "recession"
    MIXED = "mixed"


class AnomalyType(str, Enum):
    TYPE_A = "TYPE_A"  # Market/Technical Shock (Temporary)
    TYPE_B = "TYPE_B"  # Company-Specific Temporary Problem
    TYPE_C = "TYPE_C"  # Fundamental Structural Deterioration (Danger)
    UNCLEAR = "UNCLEAR"


class ThesisStatus(str, Enum):
    VALID = "valid"
    REVIEW = "review"
    INVALIDATED = "invalidated"


class AlertType(str, Enum):
    EARNINGS = "EARNINGS"
    STOP_LOSS = "STOP_LOSS"
    THESIS = "THESIS"
    ANOMALY = "ANOMALY"
    RECOMMENDATION = "RECOMMENDATION"
    RISK = "RISK"
    DATA_STALE = "DATA_STALE"
    MODEL_DEGRADED = "MODEL_DEGRADED"


class SeverityLevel(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class PositionStatus(str, Enum):
    OPEN = "open"
    CLOSED = "closed"
    PARTIAL = "partial"


class ModelStatus(str, Enum):
    TRAINING = "TRAINING"
    VALIDATED = "VALIDATED"
    DEPLOYED = "DEPLOYED"
    DEGRADED = "DEGRADED"
    RETIRED = "RETIRED"
    FAILED = "FAILED"


class UniverseType(str, Enum):
    CURRENT_UNIVERSE_APPROXIMATE = "CURRENT_UNIVERSE_APPROXIMATE"
    HISTORICAL_UNIVERSE = "HISTORICAL_UNIVERSE"


class ReportExportStatus(str, Enum):
    PENDING = "PENDING"
    GENERATING = "GENERATING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class DataQualityStatus(str, Enum):
    PASS = "PASS"
    WARNING = "WARNING"
    FAIL = "FAIL"
