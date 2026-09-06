"""
StockSense AI — Base Strategy Interface
All backtest strategies inherit from this interface to generate standard trade signals point-in-time.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from app.backtesting.schemas import OrderSide, OrderType


class StrategySignal:
    def __init__(
        self,
        security_id: str,
        ticker: str,
        side: OrderSide,
        target_weight: Optional[float] = None,
        confidence: float = 1.0,
        expected_return: Optional[float] = None,
        predicted_volatility: Optional[float] = None,
        stop_loss_price: Optional[float] = None,
        take_profit_price: Optional[float] = None,
        trailing_stop_atr_mult: Optional[float] = None,
        order_type: OrderType = OrderType.MARKET,
        limit_price: Optional[float] = None,
        reason: str = "",
        signal_metadata: Optional[Dict[str, Any]] = None,
    ):
        self.security_id = security_id
        self.ticker = ticker
        self.side = side
        self.target_weight = target_weight
        self.confidence = confidence
        self.expected_return = expected_return
        self.predicted_volatility = predicted_volatility
        self.stop_loss_price = stop_loss_price
        self.take_profit_price = take_profit_price
        self.trailing_stop_atr_mult = trailing_stop_atr_mult
        self.order_type = order_type
        self.limit_price = limit_price
        self.reason = reason
        self.signal_metadata = signal_metadata or {}


class BaseStrategy(ABC):
    def __init__(self, name: str, params: Optional[Dict[str, Any]] = None):
        self.name = name
        self.params = params or {}

    @abstractmethod
    def generate_signals(
        self,
        date_str: str,
        available_securities: List[str],
        prices: Dict[str, Dict[str, float]],
        features: Dict[str, Dict[str, Any]],
        predictions: Dict[str, Dict[str, Any]],
        current_positions: Dict[str, Any],
        portfolio_equity: float,
    ) -> List[StrategySignal]:
        """
        Generates trading signals for the current timestamp bar using only data available at or before date_str.
        """
        pass
