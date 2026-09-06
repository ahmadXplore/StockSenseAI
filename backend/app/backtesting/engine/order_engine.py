"""
StockSense AI — Order Engine
Manages order generation, queuing, validation, and lifecycle state transitions.
"""

import uuid
from typing import List, Dict, Optional, Any
from app.backtesting.schemas import (
    Order, OrderType, OrderSide, OrderStatus, Fill
)


class OrderEngine:
    def __init__(self):
        self.orders: Dict[str, Order] = {}
        self.fills: List[Fill] = []

    def create_order(
        self,
        security_id: str,
        ticker: str,
        market_code: str,
        exchange_code: str,
        side: OrderSide,
        order_type: OrderType,
        quantity: float,
        limit_price: Optional[float] = None,
        stop_price: Optional[float] = None,
        created_at: str = "",
        strategy_signal: Optional[Dict[str, Any]] = None,
    ) -> Order:
        order_id = f"ord_{uuid.uuid4().hex[:12]}"
        order = Order(
            order_id=order_id,
            security_id=security_id,
            ticker=ticker,
            market_code=market_code,
            exchange_code=exchange_code,
            side=side,
            order_type=order_type,
            quantity=round(quantity, 4),
            limit_price=limit_price,
            stop_price=stop_price,
            created_at=created_at,
            status=OrderStatus.PENDING,
            strategy_signal=strategy_signal,
        )
        self.orders[order_id] = order
        return order

    def update_order_status(self, order_id: str, status: OrderStatus, reason: Optional[str] = None) -> None:
        order = self.orders.get(order_id)
        if order:
            order.status = status
            if reason:
                order.reason = reason

    def record_fill(self, fill: Fill) -> None:
        self.fills.append(fill)
        self.update_order_status(fill.order_id, OrderStatus.FILLED)

    def get_pending_orders(self) -> List[Order]:
        return [o for o in self.orders.values() if o.status in (OrderStatus.PENDING, OrderStatus.SUBMITTED)]
