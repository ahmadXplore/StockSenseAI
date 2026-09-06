"""
StockSense AI — Strategy Engine Modules
"""

from typing import Dict, Any, Type
from app.backtesting.schemas import StrategyType
from app.backtesting.strategies.base import BaseStrategy, StrategySignal
from app.backtesting.strategies.ai_prediction import AIPredictionStrategy
from app.backtesting.strategies.momentum import MomentumStrategy
from app.backtesting.strategies.trend_following import TrendFollowingStrategy
from app.backtesting.strategies.mean_reversion import MeanReversionStrategy
from app.backtesting.strategies.fundamental import FundamentalStrategy
from app.backtesting.strategies.volatility import VolatilityBreakoutStrategy
from app.backtesting.strategies.ensemble import EnsembleStrategy

STRATEGY_REGISTRY: Dict[StrategyType, Type[BaseStrategy]] = {
    StrategyType.AI_PREDICTION: AIPredictionStrategy,
    StrategyType.MOMENTUM: MomentumStrategy,
    StrategyType.TREND_FOLLOWING: TrendFollowingStrategy,
    StrategyType.MEAN_REVERSION: MeanReversionStrategy,
    StrategyType.FUNDAMENTAL: FundamentalStrategy,
    StrategyType.VOLATILITY_BREAKOUT: VolatilityBreakoutStrategy,
    StrategyType.ENSEMBLE: EnsembleStrategy,
}


def create_strategy(strategy_type: StrategyType, params: Dict[str, Any] = None) -> BaseStrategy:
    cls = STRATEGY_REGISTRY.get(strategy_type, AIPredictionStrategy)
    return cls(params or {})


__all__ = [
    "BaseStrategy",
    "StrategySignal",
    "AIPredictionStrategy",
    "MomentumStrategy",
    "TrendFollowingStrategy",
    "MeanReversionStrategy",
    "FundamentalStrategy",
    "VolatilityBreakoutStrategy",
    "EnsembleStrategy",
    "STRATEGY_REGISTRY",
    "create_strategy",
]
