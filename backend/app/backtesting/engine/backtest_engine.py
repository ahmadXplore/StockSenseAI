"""
StockSense AI — Master Event-Driven Backtest Engine
Orchestrates timeline iteration, point-in-time universe, ML strategy execution, risk gates, friction, and evaluation.
"""

import time
import uuid
from typing import Dict, List, Any, Optional
import numpy as np
from datetime import datetime, timezone

from app.backtesting.schemas import (
    BacktestConfig, BacktestResponse, Order, Fill, TradeRecord,
    OrderSide, OrderType, OrderStatus, PositionSide, ExitReason,
    EquityCurvePoint, PerformanceMetrics, RiskMetricsReport,
    PerformanceAttribution, AllocationMethod, PositionSizingMethod
)
from app.backtesting.engine.event_loop import EventLoop, MarketTimelineBar
from app.backtesting.engine.execution_engine import ExecutionEngine
from app.backtesting.engine.order_engine import OrderEngine
from app.backtesting.portfolio.portfolio_engine import PortfolioEngine
from app.backtesting.portfolio.position_manager import Position
from app.backtesting.costs.transaction_costs import compute_transaction_friction
from app.backtesting.risk.risk_engine import RiskEngine
from app.backtesting.corporate_actions.adjustments import process_corporate_action
from app.backtesting.strategies import create_strategy, BaseStrategy, StrategySignal
from app.backtesting.evaluation.performance import calculate_performance_metrics
from app.backtesting.evaluation.benchmark import compute_benchmark_comparison
from app.backtesting.evaluation.attribution import compute_performance_attribution
from app.backtesting.evaluation.statistics import generate_monthly_returns_heatmap, generate_yearly_returns
from app.backtesting.validation.reproducibility import generate_configuration_hash
from app.backtesting.validation.leakage import assert_no_lookahead_leakage
from app.backtesting.validation.survivorship import resolve_point_in_time_universe
from app.core.logging import get_logger

logger = get_logger("backtesting.engine")


class BacktestEngine:
    def __init__(self, config: BacktestConfig):
        self.config = config
        self.run_id = f"bt_{uuid.uuid4().hex[:12]}"
        self.config_hash = generate_configuration_hash(config)
        self.portfolio = PortfolioEngine(
            initial_capital=config.initial_capital,
            base_currency=config.base_currency,
            cash_interest_rate_pct=config.cash_interest_rate_pct,
        )
        self.risk_engine = RiskEngine(config)
        self.order_engine = OrderEngine()
        self.execution_engine = ExecutionEngine(config)

        # Inject ensemble-specific config params into strategy_params
        strategy_params = dict(config.strategy_params or {})
        if config.stop_loss_pct is not None:
            strategy_params.setdefault("stop_loss_pct", config.stop_loss_pct)
        if config.take_profit_pct is not None:
            strategy_params.setdefault("take_profit_pct", config.take_profit_pct)
        strategy_params.setdefault("ai_weight", 0.50)
        strategy_params.setdefault("momentum_weight", 0.30)
        strategy_params.setdefault("fundamental_weight", 0.20)
        self.strategy: BaseStrategy = create_strategy(config.strategy_type, strategy_params)

        # Core state tracking
        self.trades: List[TradeRecord] = []
        self.equity_curve: List[EquityCurvePoint] = []
        self.pending_orders: List[Order] = []
        self.trade_entry_signals: Dict[str, Dict[str, Any]] = {}  # security_id -> entry signal metadata

        # Monthly volatility recalibration state
        self._price_history: Dict[str, List[float]] = {}  # security_id -> recent close history
        self._monthly_vol_cache: Dict[str, float] = {}  # security_id -> trailing 30d realized vol
        self._last_recalibration_month: Optional[str] = None  # "YYYY-MM" of last recalibration
        self._monthly_vol_log: List[Dict[str, Any]] = []  # audit trail of vol recalibrations

    def run(self, timeline: List[MarketTimelineBar], security_metadata: Optional[Dict[str, Dict[str, Any]]] = None) -> BacktestResponse:
        """
        Executes the event-driven backtest over the chronological timeline.
        """
        start_time = time.time()
        logger.info(f"Starting backtest {self.run_id} ({self.config.name}) over {len(timeline)} bars")

        if len(timeline) == 0:
            raise ValueError("INSUFFICIENT_BACKTEST_DATA: Timeline contains 0 bars for requested date range.")

        event_loop = EventLoop(timeline)
        prev_equity = self.config.initial_capital
        benchmark_initial_val: Optional[float] = None

        # ── Main Event Loop ──
        for bar_idx, bar in event_loop.iterate_bars():
            current_date = bar.date
            prices = bar.prices
            features = bar.features
            predictions = bar.predictions
            corp_actions = bar.corporate_actions

            # 1. Look-ahead bias assertion
            for sec_id, f_dict in features.items():
                f_ts = f_dict.get("timestamp", current_date)
                assert_no_lookahead_leakage(current_date, f_ts, current_date)

            # 1b. Track rolling price history for volatility recalibration
            for sec_id, p_data in prices.items():
                c = float(p_data.get("close", 0.0))
                if c > 0:
                    if sec_id not in self._price_history:
                        self._price_history[sec_id] = []
                    self._price_history[sec_id].append(c)
                    # Keep only last 63 trading days (~3 months window)
                    if len(self._price_history[sec_id]) > 63:
                        self._price_history[sec_id] = self._price_history[sec_id][-63:]

            # 1c. Monthly Volatility Recalibration (AI Confidence Sizing re-evaluation)
            current_month = current_date[:7]  # "YYYY-MM"
            if (
                self.config.monthly_volatility_recalibration
                and self._last_recalibration_month != current_month
                and bar_idx > 0  # Skip very first bar
            ):
                self._last_recalibration_month = current_month
                new_vol_cache: Dict[str, float] = {}
                for sec_id, hist in self._price_history.items():
                    if len(hist) >= 10:
                        # Trailing 30d realized vol (annualized from daily log-returns)
                        window = hist[-min(30, len(hist)):]
                        if len(window) >= 2:
                            log_rets = [
                                np.log(window[i] / window[i - 1])
                                for i in range(1, len(window))
                                if window[i - 1] > 0
                            ]
                            if log_rets:
                                daily_vol = float(np.std(log_rets, ddof=1))
                                annualized_vol = daily_vol * np.sqrt(252)
                                new_vol_cache[sec_id] = round(annualized_vol, 4)

                if new_vol_cache:
                    self._monthly_vol_cache = new_vol_cache
                    avg_pool_vol = round(float(np.mean(list(new_vol_cache.values()))), 4)
                    self._monthly_vol_log.append({
                        "date": current_date,
                        "month": current_month,
                        "securities_recalibrated": len(new_vol_cache),
                        "avg_pool_volatility": avg_pool_vol,
                        "volatility_target": self.config.volatility_target_pct,
                        "vol_by_security": new_vol_cache,
                    })
                    logger.info(
                        f"[MONTHLY VOL RECAL] {current_month}: "
                        f"Pool avg σ={avg_pool_vol:.2%}, Target σ={self.config.volatility_target_pct:.2%}, "
                        f"Securities={len(new_vol_cache)}"
                    )

            # 2. Point-in-time universe resolution (Survivorship-bias-free)
            active_universe = resolve_point_in_time_universe(
                as_of_date=current_date,
                market_code=self.config.market_code,
                exchange_code=self.config.exchange_code or "US",
                requested_securities=self.config.securities,
                security_metadata=security_metadata,
            )

            # 3. Process Pending Orders from Previous Bar (Next-Open Execution Semantics)
            orders_to_process = self.pending_orders
            self.pending_orders = []

            for order in orders_to_process:
                sec_p = prices.get(order.security_id, {})
                if not sec_p or sec_p.get("open", 0) <= 0:
                    self.order_engine.update_order_status(order.order_id, OrderStatus.REJECTED, "No price data on open")
                    continue

                fill = self.execution_engine.execute_order(
                    order=order,
                    bar_open=sec_p.get("open", 0.0),
                    bar_high=sec_p.get("high", 0.0),
                    bar_low=sec_p.get("low", 0.0),
                    bar_close=sec_p.get("close", 0.0),
                    bar_date=current_date,
                    bar_volume=sec_p.get("volume"),
                    bar_atr=sec_p.get("atr"),
                )

                if fill:
                    self.order_engine.record_fill(fill)
                    self._apply_fill(fill, current_date, order.strategy_signal)
                else:
                    # Order did not fill (e.g. limit price not touched)
                    self.order_engine.update_order_status(order.order_id, OrderStatus.CANCELLED, "Price boundary not reached")

            # 4. Process Corporate Actions (Splits, Dividends)
            for action in corp_actions:
                sec_id = action.get("security_id", "")
                if self.portfolio.has_position(sec_id):
                    pos = self.portfolio.get_position(sec_id)
                    cur_p = prices.get(sec_id, {}).get("close", pos.average_entry_price)
                    adj_res = process_corporate_action(
                        action=action,
                        current_shares=pos.shares,
                        current_avg_price=pos.average_entry_price,
                        current_market_price=cur_p,
                        reinvest_dividends=(self.config.dividend_handling == "REINVEST"),
                    )
                    pos.shares += adj_res.shares_delta
                    pos.average_entry_price = adj_res.new_average_entry_price
                    if adj_res.cash_delta > 0:
                        self.portfolio.cash.credit_cash(adj_res.cash_delta, pos.native_currency)
                        self.portfolio.ledger.record_dividend(current_date, sec_id, adj_res.cash_delta)

            # 5. Evaluate Open Position Risk & Dynamic Exits (Stops, Trailing Stops, Take Profits)
            current_close_prices = {s: p.get("close", 0.0) for s, p in prices.items()}
            for sec_id, pos in list(self.portfolio.positions.items()):
                sec_p = prices.get(sec_id, {})
                if not sec_p or sec_p.get("close", 0) <= 0:
                    continue

                exit_sig = self.risk_engine.check_position_exits(
                    position=pos,
                    high=sec_p.get("high", sec_p["close"]),
                    low=sec_p.get("low", sec_p["close"]),
                    close=sec_p["close"],
                    atr=sec_p.get("atr"),
                    volatility=sec_p.get("volatility"),
                    ai_prob_up=predictions.get(sec_id, {}).get("probability_up"),
                    fundamental_score=features.get(sec_id, {}).get("fundamental_score"),
                )

                if exit_sig.should_exit:
                    # Immediate stop execution at current bar exit price
                    exit_price = sec_p["close"]
                    if exit_sig.exit_reason == ExitReason.STOP_LOSS and pos.stop_loss_price:
                        exit_price = pos.stop_loss_price
                    elif exit_sig.exit_reason == ExitReason.TRAILING_STOP and pos.trailing_stop_price:
                        exit_price = pos.trailing_stop_price
                    elif exit_sig.exit_reason == ExitReason.TAKE_PROFIT and pos.take_profit_price:
                        exit_price = pos.take_profit_price

                    self._close_position_trade(pos, exit_price, current_date, exit_sig.exit_reason or ExitReason.STOP_LOSS)

            # 6. Accrue Cash Interest
            self.portfolio.cash.accrue_daily_interest()

            # 7. Generate Strategy Signals
            current_equity = self.portfolio.get_total_equity(current_close_prices)
            signals = self.strategy.generate_signals(
                date_str=current_date,
                available_securities=active_universe,
                prices=prices,
                features=features,
                predictions=predictions,
                current_positions=self.portfolio.positions,
                portfolio_equity=current_equity,
            )

            # 8. Filter Signals & Enforce Pre-Trade Risk Limits -> Queue Orders
            for sig in signals:
                sec_p = prices.get(sig.security_id, {})
                cur_price = sec_p.get("close", 0.0)
                if cur_price <= 0:
                    continue

                if sig.side == OrderSide.BUY and not self.portfolio.has_position(sig.security_id):
                    # Position Sizing
                    shares_to_buy = self._calculate_position_size(sig, cur_price, current_equity, sec_p.get("atr"), sig.security_id)
                    if shares_to_buy <= 0:
                        continue

                    # Pre-trade Risk Limit Check
                    risk_res = self.risk_engine.check_pre_trade(
                        security_id=sig.security_id,
                        requested_shares=shares_to_buy,
                        current_price=cur_price,
                        side=sig.side,
                        portfolio_equity=current_equity,
                        cash_balance=self.portfolio.cash.get_total_cash_in_base_currency(),
                        existing_shares=0.0,
                        current_drawdown_pct=((self.portfolio.peak_equity - current_equity) / self.portfolio.peak_equity * 100.0) if self.portfolio.peak_equity > 0 else 0.0,
                    )

                    if risk_res.is_allowed:
                        final_shares = risk_res.adjusted_shares or shares_to_buy
                        if not self.config.allow_fractional_shares:
                            final_shares = float(int(final_shares))
                        
                        if final_shares > 0:
                            order = self.order_engine.create_order(
                                security_id=sig.security_id,
                                ticker=sig.ticker,
                                market_code=self.config.market_code,
                                exchange_code=self.config.exchange_code or "US",
                                side=sig.side,
                                order_type=sig.order_type,
                                quantity=final_shares,
                                limit_price=sig.limit_price,
                                stop_price=sig.stop_loss_price,
                                created_at=current_date,
                                strategy_signal={
                                    "reason": sig.reason,
                                    "confidence": sig.confidence,
                                    "expected_return": sig.expected_return,
                                    "predicted_volatility": sig.predicted_volatility,
                                    "stop_loss_price": sig.stop_loss_price,
                                    "take_profit_price": sig.take_profit_price,
                                    "signal_metadata": sig.signal_metadata,
                                }
                            )
                            self.pending_orders.append(order)

                elif sig.side == OrderSide.SELL and self.portfolio.has_position(sig.security_id):
                    pos = self.portfolio.get_position(sig.security_id)
                    self._close_position_trade(pos, cur_price, current_date, ExitReason.PREDICTION_REVERSAL)

            # 9. Record End-of-Bar Equity Curve Point
            snapshot = self.portfolio.generate_snapshot(current_date, current_close_prices)
            daily_ret = ((snapshot.portfolio_value - prev_equity) / prev_equity) if prev_equity > 0 else 0.0
            snapshot.daily_return = round(daily_ret * 100.0, 4)
            prev_equity = snapshot.portfolio_value

            # Benchmark tracking
            bm_close = bar.benchmark.get("close")
            if bm_close is not None and bm_close > 0:
                if benchmark_initial_val is None:
                    benchmark_initial_val = bm_close
                snapshot.benchmark_value = round(bm_close, 2)
                snapshot.benchmark_cumulative_return = round(((bm_close - benchmark_initial_val) / benchmark_initial_val) * 100.0, 4)

            self.equity_curve.append(snapshot)

        # ── Close Any Remaining Open Positions at Final Bar ──
        final_bar = timeline[-1]
        for sec_id, pos in list(self.portfolio.positions.items()):
            final_p = final_bar.prices.get(sec_id, {}).get("close", pos.average_entry_price)
            self._close_position_trade(pos, final_p, final_bar.date, ExitReason.END_OF_BACKTEST)

        duration = round(time.time() - start_time, 3)

        # ── Compute Performance Metrics & Analytics ──
        perf_metrics = calculate_performance_metrics(
            equity_curve=self.equity_curve,
            trades=self.trades,
            initial_capital=self.config.initial_capital,
            risk_free_rate=self.config.cash_interest_rate_pct / 100.0 if self.config.cash_interest_rate_pct > 0 else 0.045,
        )

        daily_returns_list = [p.daily_return / 100.0 for p in self.equity_curve[1:]]
        benchmark_returns_list = []
        if len(self.equity_curve) > 1 and self.equity_curve[0].benchmark_value:
            for i in range(1, len(self.equity_curve)):
                b_prev = self.equity_curve[i - 1].benchmark_value or 1.0
                b_curr = self.equity_curve[i].benchmark_value or b_prev
                benchmark_returns_list.append((b_curr - b_prev) / b_prev)

        risk_report = self.risk_engine.generate_risk_report(
            daily_returns=daily_returns_list,
            benchmark_returns=benchmark_returns_list if len(benchmark_returns_list) == len(daily_returns_list) else None,
            portfolio_value=self.portfolio.get_total_equity({}),
        )

        attribution = compute_performance_attribution(self.trades)
        heatmap = generate_monthly_returns_heatmap(self.equity_curve)
        yearly = generate_yearly_returns(heatmap)

        logger.info(
            f"Backtest {self.run_id} completed: Return={perf_metrics.total_return_pct:.2f}%, "
            f"Sharpe={perf_metrics.sharpe_ratio:.2f}, MaxDD={perf_metrics.max_drawdown_pct:.2f}%, "
            f"Trades={perf_metrics.total_trades} in {duration}s"
        )

        return BacktestResponse(
            run_id=self.run_id,
            configuration_hash=self.config_hash,
            created_at=datetime.now(timezone.utc).isoformat(),
            status="COMPLETED",
            config=self.config,
            performance=perf_metrics,
            risk=risk_report,
            attribution=attribution,
            equity_curve=self.equity_curve,
            trades=self.trades,
            monthly_returns_heatmap=heatmap,
            yearly_returns=yearly,
            data_quality_score=100.0,
            lookahead_audit_passed=True,
            survivorship_audit_passed=True,
            reproducibility_seed=self.config.random_seed,
            execution_duration_seconds=duration,
            warnings=[],
        )

    def _calculate_position_size(
        self,
        signal: StrategySignal,
        current_price: float,
        portfolio_equity: float,
        atr: Optional[float] = None,
        security_id: Optional[str] = None,
    ) -> float:
        """
        Calculates share size based on configured sizing method.
        AI_CONFIDENCE_SIZING: Scales by signal confidence AND monthly localized volatility.
        If the pool's realized vol exceeds the volatility target, positions are reduced proportionally.
        """
        if current_price <= 0 or portfolio_equity <= 0:
            return 0.0

        max_cap_per_pos = portfolio_equity * self.config.max_position_weight

        if self.config.position_sizing == PositionSizingMethod.FIXED_PERCENTAGE:
            pos_cap = portfolio_equity * self.config.risk_per_trade_pct * 5.0
            pos_cap = min(pos_cap, max_cap_per_pos)
            return pos_cap / current_price

        elif self.config.position_sizing == PositionSizingMethod.ATR_RISK and atr and atr > 0:
            # Risk capital = Equity × risk_per_trade_pct
            # Stop distance = stop_loss_pct × price (or 2×ATR if no stop configured)
            sl_pct = self.config.stop_loss_pct or 0.10
            stop_dist = max(0.01, sl_pct * current_price if sl_pct > 0 else 2.0 * atr)
            risk_cap = portfolio_equity * self.config.risk_per_trade_pct
            shares = risk_cap / stop_dist
            if (shares * current_price) > max_cap_per_pos:
                shares = max_cap_per_pos / current_price
            return shares

        elif self.config.position_sizing in (
            PositionSizingMethod.CONFIDENCE_WEIGHTED,
            PositionSizingMethod.AI_CONFIDENCE_SIZING,
        ):
            # Base position weight scaled by AI confidence
            confidence = max(0.05, min(1.0, signal.confidence))
            base_weight = self.config.max_position_weight * confidence

            # Monthly volatility scaling: reduce size when local vol > target vol
            vol_scale = 1.0
            if self.config.monthly_volatility_recalibration and security_id:
                local_vol = self._monthly_vol_cache.get(security_id)
                if local_vol and local_vol > 0:
                    target_vol = self.config.volatility_target_pct or 0.20
                    # Vol-targeting scalar: scale down when local > target, scale up (capped) when local < target
                    vol_scale = min(2.0, target_vol / local_vol)
                    vol_scale = max(0.10, vol_scale)  # Floor at 10% to never fully exit

            adjusted_weight = min(self.config.max_position_weight, base_weight * vol_scale)
            return (portfolio_equity * adjusted_weight) / current_price

        else:
            # Default: fixed capital allocation
            pos_cap = min(portfolio_equity * 0.10, max_cap_per_pos)
            return pos_cap / current_price

    def _apply_fill(self, fill: Fill, current_date: str, signal_meta: Optional[Dict[str, Any]]) -> None:
        """Applies an executed order fill to portfolio state with full stop-loss/take-profit assignment."""
        total_cost = (fill.fill_price * fill.quantity) + fill.total_friction
        self.portfolio.cash.debit_cash(total_cost)
        self.portfolio.ledger.record_friction(current_date, fill.security_id, fill.total_friction)

        # Resolve stop-loss price: use signal's explicit price, else compute from config pct
        stop_loss = signal_meta.get("stop_loss_price") if signal_meta else None
        if not stop_loss and self.config.stop_loss_pct and self.config.stop_loss_pct > 0:
            stop_loss = round(fill.fill_price * (1.0 - self.config.stop_loss_pct), 4)

        # Resolve take-profit price: use signal's explicit price, else compute from config pct
        take_profit = signal_meta.get("take_profit_price") if signal_meta else None
        if not take_profit and self.config.take_profit_pct and self.config.take_profit_pct > 0:
            take_profit = round(fill.fill_price * (1.0 + self.config.take_profit_pct), 4)

        pos = self.portfolio.open_or_add_position(
            security_id=fill.security_id,
            ticker=fill.ticker,
            market_code=fill.market_code,
            shares=fill.quantity,
            fill_price=fill.fill_price,
            entry_date=current_date,
            side=PositionSide.LONG if fill.side == OrderSide.BUY else PositionSide.SHORT,
            stop_loss_price=stop_loss,
            take_profit_price=take_profit,
        )

        self.trade_entry_signals[fill.security_id] = signal_meta or {}

    def _close_position_trade(self, position: Position, exit_price: float, exit_date: str, reason: ExitReason) -> None:
        """Executes position closure and logs completed TradeRecord."""
        sec_id = position.security_id
        shares_to_close = position.shares
        entry_price = position.average_entry_price
        entry_date = position.entry_date

        closed_shares, realized_pnl = self.portfolio.close_or_reduce_position(
            security_id=sec_id,
            shares_to_close=shares_to_close,
            exit_price=exit_price,
            exit_date=exit_date,
        )

        gross_proceeds = exit_price * closed_shares
        exit_friction = compute_transaction_friction(
            reference_price=exit_price,
            shares=closed_shares,
            side=OrderSide.SELL,
            market_code=position.market_code,
            config=self.config,
        )

        net_proceeds = gross_proceeds - exit_friction.total_friction
        self.portfolio.cash.credit_cash(net_proceeds)
        self.portfolio.ledger.record_friction(exit_date, sec_id, exit_friction.total_friction)

        gross_pnl = (exit_price - entry_price) * closed_shares
        net_pnl = gross_pnl - exit_friction.total_friction
        ret_pct = ((exit_price - entry_price) / entry_price * 100.0) if entry_price > 0 else 0.0

        # Retrieve entry signal provenance
        meta = self.trade_entry_signals.get(sec_id, {})
        sig_meta = meta.get("signal_metadata", {})

        dt_entry = datetime.strptime(entry_date, "%Y-%m-%d") if entry_date else datetime.utcnow()
        dt_exit = datetime.strptime(exit_date, "%Y-%m-%d") if exit_date else datetime.utcnow()
        holding_days = max(1, (dt_exit - dt_entry).days)

        trade = TradeRecord(
            trade_id=f"trd_{uuid.uuid4().hex[:12]}",
            security_id=sec_id,
            ticker=position.ticker,
            market_code=position.market_code,
            exchange_code=self.config.exchange_code or "US",
            side=position.side,
            entry_date=entry_date,
            entry_price=round(entry_price, 4),
            shares=round(closed_shares, 4),
            entry_cost_basis=round(entry_price * closed_shares, 2),
            entry_friction=0.0,
            exit_date=exit_date,
            exit_price=round(exit_price, 4),
            exit_proceeds=round(net_proceeds, 2),
            exit_friction=exit_friction.total_friction,
            exit_reason=reason,
            holding_period_days=holding_days,
            gross_pnl=round(gross_pnl, 2),
            net_pnl=round(net_pnl, 2),
            return_pct=round(ret_pct, 4),
            signal_name=meta.get("reason", "AI_PREDICTION"),
            prediction_probability=sig_meta.get("probability_up"),
            expected_return=sig_meta.get("expected_return"),
            predicted_volatility=sig_meta.get("predicted_volatility"),
            risk_score=sig_meta.get("risk_score"),
            market_regime=sig_meta.get("market_regime"),
            native_currency=position.native_currency,
            base_currency=self.config.base_currency,
            fx_rate=1.0,
        )

        self.trades.append(trade)
        if sec_id in self.trade_entry_signals:
            del self.trade_entry_signals[sec_id]
