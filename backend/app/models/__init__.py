"""
StockSense AI — ORM Models Registry
Exports all models across all PostgreSQL schemas including multi-market canonical models.
"""

from app.models.market_data import (
    Market, Exchange, SecurityMaster, SymbolHistory, RawMarketData, IngestionJobLog,
    Company, PriceData, TechnicalIndicator, CorporateAction, IndexConstituent
)
from app.models.fundamentals import (
    IncomeStatement, BalanceSheet, CashFlowStatement, FinancialRatio,
    AnalystEstimate, EarningsEvent
)
from app.models.analysis import (
    AnalysisJob, AnalysisReport, ScoreComponent, ScoreHistory, Prediction,
    Scenario, InvestmentCalculatorRun, FundamentalHealthScore, ValuationAnalysis,
    RiskMetrics, ExitStrategy, AnomalyDetection, BacktestRun
)
from app.models.ml import (
    ModelMetadata, FeatureImportance, PredictionOutcome, ModelDriftMonitoring
)
from app.models.news import (
    NewsItem, SentimentAggregate, InsiderTransaction
)
from app.models.macro import (
    MacroIndicator, MarketRegime
)
from app.models.portfolio import (
    User, Watchlist, WatchlistItem, Position, ThesisValidation, Alert
)
from app.models.audit import (
    AnalysisRequest, DataQualityLog, ReportExport
)
from app.models.backtest import (
    BacktestRunRecord, BacktestTradeRecord, RiskLimitRecord, RiskEventRecord,
    PortfolioOptimizationRecord
)

__all__ = [
    # market_data
    "Market",
    "Exchange",
    "SecurityMaster",
    "SymbolHistory",
    "RawMarketData",
    "IngestionJobLog",
    "Company",
    "PriceData",
    "TechnicalIndicator",
    "CorporateAction",
    "IndexConstituent",
    # fundamentals
    "IncomeStatement",
    "BalanceSheet",
    "CashFlowStatement",
    "FinancialRatio",
    "AnalystEstimate",
    "EarningsEvent",
    # analysis
    "AnalysisJob",
    "AnalysisReport",
    "ScoreComponent",
    "ScoreHistory",
    "Prediction",
    "Scenario",
    "InvestmentCalculatorRun",
    "FundamentalHealthScore",
    "ValuationAnalysis",
    "RiskMetrics",
    "ExitStrategy",
    "AnomalyDetection",
    "BacktestRun",
    # ml
    "ModelMetadata",
    "FeatureImportance",
    "PredictionOutcome",
    "ModelDriftMonitoring",
    # news
    "NewsItem",
    "SentimentAggregate",
    "InsiderTransaction",
    # macro
    "MacroIndicator",
    "MarketRegime",
    # portfolio
    "User",
    "Watchlist",
    "WatchlistItem",
    "Position",
    "ThesisValidation",
    "Alert",
    # audit
    "AnalysisRequest",
    "DataQualityLog",
    "ReportExport",
    # backtesting & risk
    "BacktestRunRecord",
    "BacktestTradeRecord",
    "RiskLimitRecord",
    "RiskEventRecord",
    "PortfolioOptimizationRecord",
]

