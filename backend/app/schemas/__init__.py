"""
StockSense AI — Schemas Registry
"""

from app.schemas.health import HealthResponse, ServiceHealth
from app.schemas.analysis import (
    AnalysisRequest, BatchAnalysisRequest, JobStatusResponse,
    FullReportResponse, ScoreCard, HorizonPredictionResponse,
    ScenarioCardResponse, ExitPlanResponse, InvestmentSimulationResponse,
    ExplainabilityResponse, DataFreshnessInfo
)
from app.schemas.market import RegimeResponse, MarketOverviewResponse, TickerSearchResult
from app.schemas.watchlist import WatchlistAddRequest, WatchlistItemResponse, WatchlistResponse
from app.schemas.portfolio import PositionCreateRequest, PositionResponse, PortfolioSummaryResponse
from app.schemas.settings import UserSettingsRequest, UserSettingsResponse
from app.schemas.auth import (
    FaceSignupRequest, FaceLoginRequest, FaceUserResponse, FaceAuthResponse
)

__all__ = [
    "HealthResponse",
    "ServiceHealth",
    "AnalysisRequest",
    "BatchAnalysisRequest",
    "JobStatusResponse",
    "FullReportResponse",
    "ScoreCard",
    "HorizonPredictionResponse",
    "ScenarioCardResponse",
    "ExitPlanResponse",
    "InvestmentSimulationResponse",
    "ExplainabilityResponse",
    "DataFreshnessInfo",
    "RegimeResponse",
    "MarketOverviewResponse",
    "TickerSearchResult",
    "WatchlistAddRequest",
    "WatchlistItemResponse",
    "WatchlistResponse",
    "PositionCreateRequest",
    "PositionResponse",
    "PortfolioSummaryResponse",
    "UserSettingsRequest",
    "UserSettingsResponse",
    "FaceSignupRequest",
    "FaceLoginRequest",
    "FaceUserResponse",
    "FaceAuthResponse",
]
