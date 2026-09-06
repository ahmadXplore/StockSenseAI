"""
StockSense AI — Realistic Execution Engine
Executes orders at realistic prices (Next-Open, Same-Close, VWAP, Limit, Stop) with friction and slippage.
"""

import uuid
from typing import Dict, Any, Optional, Tuple
from app.backtesting.schemas import (
    Order, Fill, OrderType, OrderSide, OrderStatus, ExecutionTiming, BacktestConfig
)
from app.backtesting.costs.transaction_costs import compute_transaction_friction, FrictionBreakdown


class ExecutionEngine:
    def __init__(self, config: BacktestConfig):
        self.config = config

    def execute_order(
        self,
        order: Order,
        bar_open: float,
        bar_high: float,
        bar_low: float,
        bar_close: float,
        bar_date: str,
        bar_volume: Optional[float] = None,
        bar_atr: Optional[float] = None,
    ) -> Optional[Fill]:
        """
        Executes a single order against the active price bar according to execution rules.
        """
        if order.quantity <= 0:
            return None

        ref_price = 0.0
        can_fill = False

        # 1. Determine Reference Price based on Order Type & Timing
        if order.order_type == OrderType.MARKET:
            if self.config.execution_timing == ExecutionTiming.NEXT_OPEN:
                ref_price = bar_open
            elif self.config.execution_timing == ExecutionTiming.VWAP:
                # Approximation of typical price (H + L + C) / 3
                ref_price = (bar_high + bar_low + bar_close) / 3.0
            else: # SAME_CLOSE
                ref_price = bar_close
            can_fill = True

        elif order.order_type == OrderType.LIMIT:
            if order.limit_price is None:
                return None
            if order.side in (OrderSide.BUY, OrderSide.BUY_TO_COVER):
                # Buy limit fills if bar low touches limit price
                if bar_low <= order.limit_price:
                    ref_price = min(bar_open, order.limit_price)
                    can_fill = True
            else:
                # Sell limit fills if bar high touches limit price
                if bar_high >= order.limit_price:
                    ref_price = max(bar_open, order.limit_price)
                    can_fill = True

        elif order.order_type == OrderType.STOP:
            if order.stop_price is None:
                return None
            if order.side in (OrderSide.BUY, OrderSide.BUY_TO_COVER):
                if bar_high >= order.stop_price:
                    ref_price = max(bar_open, order.stop_price)
                    can_fill = True
            else:
                if bar_low <= order.stop_price:
                    ref_price = min(bar_open, order.stop_price)
                    can_fill = True

        if not can_fill or ref_price <= 0:
            return None

        # 2. Compute Friction (Slippage + Commissions + Exchange Fees + Taxes)
        friction: FrictionBreakdown = compute_transaction_friction(
            reference_price=ref_price,
            shares=order.quantity,
            side=order.side,
            market_code=order.market_code,
            exchange_code=order.exchange_code,
            config=self.config,
            daily_volume=bar_volume,
            atr_volatility=bar_atr,
        )

        fill_id = f"fill_{uuid.uuid4().hex[:12]}"
        fill = Fill(
            fill_id=fill_id,
            order_id=order.order_id,
            security_id=order.security_id,
            ticker=order.ticker,
            market_code=order.market_code,
            side=order.side,
            quantity=order.quantity,
            fill_price=friction.executed_price,
            reference_price=friction.reference_price,
            slippage_cost=friction.slippage_cost,
            commission=friction.commission,
            exchange_fee=friction.exchange_fee,
            taxes=friction.taxes,
            total_friction=friction.total_friction,
            filled_at=bar_date,
        )

        return fill
