"""
StockSense AI — Position Risk & Exit Decision Engine
Evaluates position-level stop-loss, trailing stops, profit targets, time stops, volatility exits, and prediction reversals.

Priority Order (strict):
    1. Hard Stop-Loss (highest priority — overrides all other exits)
    2. Take Profit
    3. Trailing Stop
    4. Time Stop
    5. Volatility Stop
    6. Fundamental Thesis Exit
    7. AI Prediction Reversal (lowest priority)
"""

from typing import Optional
from app.backtesting.schemas import ExitReason, PositionSide
from app.backtesting.portfolio.position_manager import Position


class PositionExitSignal:
    def __init__(self, should_exit: bool, exit_reason: Optional[ExitReason] = None, message: str = ""):
        self.should_exit = should_exit
        self.exit_reason = exit_reason
        self.message = message


def evaluate_position_exits(
    position: Position,
    current_high: float,
    current_low: float,
    current_close: float,
    current_atr: Optional[float] = None,
    current_volatility: Optional[float] = None,
    current_ai_probability_up: Optional[float] = None,
    fundamental_health_score: Optional[float] = None,
    trailing_stop_atr_mult: Optional[float] = 1.5,
    volatility_stop_threshold: Optional[float] = None,
    time_stop_bars: Optional[int] = None,
    check_thesis: bool = True,
    check_prediction_reversal: bool = True,
) -> PositionExitSignal:
    """
    Evaluates all exit conditions against the current price bar for an open position.

    Priority: Stop-Loss > Take-Profit > Trailing-Stop > Time-Stop > Volatility-Stop > Thesis > AI Reversal
    This ordering ensures the 10% hard stop-loss is never overridden by softer exits.
    """
    if position.shares <= 0:
        return PositionExitSignal(False)

    position.bars_held += 1
    position.update_price_extremes(current_high, current_low)

    # ──────────────────────────────────────────────────
    # PRIORITY 1: Hard Stop-Loss (highest priority gate)
    # Must be evaluated FIRST — overrides all other exits.
    # ──────────────────────────────────────────────────
    if position.stop_loss_price is not None:
        if position.side == PositionSide.LONG and current_low <= position.stop_loss_price:
            return PositionExitSignal(
                True,
                ExitReason.STOP_LOSS,
                f"[STOP LOSS OVERRIDE] Hard stop-loss breached: low ${current_low:.2f} ≤ stop ${position.stop_loss_price:.2f} "
                f"(Entry ${position.average_entry_price:.2f}, Loss={((position.stop_loss_price - position.average_entry_price) / position.average_entry_price):.1%})"
            )
        elif position.side == PositionSide.SHORT and current_high >= position.stop_loss_price:
            return PositionExitSignal(
                True,
                ExitReason.STOP_LOSS,
                f"[STOP LOSS OVERRIDE] Hard stop-loss breached: high ${current_high:.2f} ≥ stop ${position.stop_loss_price:.2f} "
                f"(Entry ${position.average_entry_price:.2f}, Loss={((position.average_entry_price - position.stop_loss_price) / position.average_entry_price):.1%})"
            )

    # ──────────────────────────────────────────────────
    # PRIORITY 2: Take Profit Target
    # ──────────────────────────────────────────────────
    if position.take_profit_price is not None:
        if position.side == PositionSide.LONG and current_high >= position.take_profit_price:
            return PositionExitSignal(
                True,
                ExitReason.TAKE_PROFIT,
                f"[TAKE PROFIT] Target reached: high ${current_high:.2f} ≥ target ${position.take_profit_price:.2f} "
                f"(Entry ${position.average_entry_price:.2f}, Gain={((position.take_profit_price - position.average_entry_price) / position.average_entry_price):.1%})"
            )
        elif position.side == PositionSide.SHORT and current_low <= position.take_profit_price:
            return PositionExitSignal(
                True,
                ExitReason.TAKE_PROFIT,
                f"[TAKE PROFIT] Target reached: low ${current_low:.2f} ≤ target ${position.take_profit_price:.2f} "
                f"(Entry ${position.average_entry_price:.2f}, Gain={((position.average_entry_price - position.take_profit_price) / position.average_entry_price):.1%})"
            )

    # ──────────────────────────────────────────────────
    # PRIORITY 3: Update & check Trailing Stop
    # ──────────────────────────────────────────────────
    if trailing_stop_atr_mult and current_atr and current_atr > 0:
        if position.side == PositionSide.LONG:
            trail_level = position.highest_price_seen - (trailing_stop_atr_mult * current_atr)
            if position.trailing_stop_price is None or trail_level > position.trailing_stop_price:
                position.trailing_stop_price = round(trail_level, 4)
        else:  # SHORT
            trail_level = position.lowest_price_seen + (trailing_stop_atr_mult * current_atr)
            if position.trailing_stop_price is None or trail_level < position.trailing_stop_price:
                position.trailing_stop_price = round(trail_level, 4)

    if position.trailing_stop_price is not None:
        if position.side == PositionSide.LONG and current_low <= position.trailing_stop_price:
            return PositionExitSignal(
                True,
                ExitReason.TRAILING_STOP,
                f"[TRAILING STOP] Triggered: low ${current_low:.2f} ≤ trail ${position.trailing_stop_price:.2f} "
                f"(Peak ${position.highest_price_seen:.2f})"
            )
        elif position.side == PositionSide.SHORT and current_high >= position.trailing_stop_price:
            return PositionExitSignal(
                True,
                ExitReason.TRAILING_STOP,
                f"[TRAILING STOP] Triggered: high ${current_high:.2f} ≥ trail ${position.trailing_stop_price:.2f} "
                f"(Trough ${position.lowest_price_seen:.2f})"
            )

    # ──────────────────────────────────────────────────
    # PRIORITY 4: Time Stop
    # ──────────────────────────────────────────────────
    if time_stop_bars and position.bars_held >= time_stop_bars:
        return PositionExitSignal(
            True,
            ExitReason.TIME_STOP,
            f"[TIME STOP] Max holding period reached: {position.bars_held} bars ≥ limit {time_stop_bars} bars"
        )

    # ──────────────────────────────────────────────────
    # PRIORITY 5: Volatility Stop
    # ──────────────────────────────────────────────────
    if volatility_stop_threshold and current_volatility and current_volatility > volatility_stop_threshold:
        return PositionExitSignal(
            True,
            ExitReason.VOLATILITY_STOP,
            f"[VOLATILITY STOP] Realized vol {current_volatility:.2%} > threshold {volatility_stop_threshold:.2%}"
        )

    # ──────────────────────────────────────────────────
    # PRIORITY 6: Fundamental Thesis Exit
    # ──────────────────────────────────────────────────
    if check_thesis and fundamental_health_score is not None and fundamental_health_score < 40.0:
        return PositionExitSignal(
            True,
            ExitReason.THESIS_EXIT,
            f"[THESIS EXIT] Fundamental health deteriorated to {fundamental_health_score:.1f}/100 (threshold: 40)"
        )

    # ──────────────────────────────────────────────────
    # PRIORITY 7: AI Prediction Reversal (lowest priority)
    # ──────────────────────────────────────────────────
    if check_prediction_reversal and current_ai_probability_up is not None:
        if position.side == PositionSide.LONG and current_ai_probability_up < 0.40:
            return PositionExitSignal(
                True,
                ExitReason.PREDICTION_REVERSAL,
                f"[AI REVERSAL] AI probability turned bearish: P(up)={current_ai_probability_up:.2%} < 40% threshold"
            )
        elif position.side == PositionSide.SHORT and current_ai_probability_up > 0.60:
            return PositionExitSignal(
                True,
                ExitReason.PREDICTION_REVERSAL,
                f"[AI REVERSAL] AI probability turned bullish: P(up)={current_ai_probability_up:.2%} > 60% threshold"
            )

    return PositionExitSignal(False)
