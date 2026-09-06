"""
StockSense AI — Position Risk & Exit Decision Engine
Evaluates position-level stop-loss, trailing stops, profit targets, time stops, volatility exits, and prediction reversals.
"""

from typing import Optional, Tuple
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
    """
    if position.shares <= 0:
        return PositionExitSignal(False)

    position.bars_held += 1
    position.update_price_extremes(current_high, current_low)

    # 1. Update dynamic trailing stop
    if trailing_stop_atr_mult and current_atr and current_atr > 0:
        if position.side == PositionSide.LONG:
            trail_level = position.highest_price_seen - (trailing_stop_atr_mult * current_atr)
            if position.trailing_stop_price is None or trail_level > position.trailing_stop_price:
                position.trailing_stop_price = round(trail_level, 4)
        else: # SHORT
            trail_level = position.lowest_price_seen + (trailing_stop_atr_mult * current_atr)
            if position.trailing_stop_price is None or trail_level < position.trailing_stop_price:
                position.trailing_stop_price = round(trail_level, 4)

    # 2. Check Hard Stop Loss
    if position.stop_loss_price is not None:
        if position.side == PositionSide.LONG and current_low <= position.stop_loss_price:
            return PositionExitSignal(True, ExitReason.STOP_LOSS, f"Hard stop-loss breached at ${position.stop_loss_price:.2f}")
        elif position.side == PositionSide.SHORT and current_high >= position.stop_loss_price:
            return PositionExitSignal(True, ExitReason.STOP_LOSS, f"Hard stop-loss breached at ${position.stop_loss_price:.2f}")

    # 3. Check Trailing Stop
    if position.trailing_stop_price is not None:
        if position.side == PositionSide.LONG and current_low <= position.trailing_stop_price:
            return PositionExitSignal(True, ExitReason.TRAILING_STOP, f"Trailing stop triggered at ${position.trailing_stop_price:.2f}")
        elif position.side == PositionSide.SHORT and current_high >= position.trailing_stop_price:
            return PositionExitSignal(True, ExitReason.TRAILING_STOP, f"Trailing stop triggered at ${position.trailing_stop_price:.2f}")

    # 4. Check Take Profit
    if position.take_profit_price is not None:
        if position.side == PositionSide.LONG and current_high >= position.take_profit_price:
            return PositionExitSignal(True, ExitReason.TAKE_PROFIT, f"Take profit target reached at ${position.take_profit_price:.2f}")
        elif position.side == PositionSide.SHORT and current_low <= position.take_profit_price:
            return PositionExitSignal(True, ExitReason.TAKE_PROFIT, f"Take profit target reached at ${position.take_profit_price:.2f}")

    # 5. Check Time Stop
    if time_stop_bars and position.bars_held >= time_stop_bars:
        return PositionExitSignal(True, ExitReason.TIME_STOP, f"Time stop reached after {position.bars_held} bars")

    # 6. Check Volatility Stop
    if volatility_stop_threshold and current_volatility and current_volatility > volatility_stop_threshold:
        return PositionExitSignal(True, ExitReason.VOLATILITY_STOP, f"Volatility stop triggered: {current_volatility:.2%} > threshold {volatility_stop_threshold:.2%}")

    # 7. Check Fundamental Thesis Exit
    if check_thesis and fundamental_health_score is not None and fundamental_health_score < 40.0:
        return PositionExitSignal(True, ExitReason.THESIS_EXIT, f"Fundamental thesis deteriorated (health score: {fundamental_health_score:.1f}/100)")

    # 8. Check AI Prediction Reversal
    if check_prediction_reversal and current_ai_probability_up is not None:
        if position.side == PositionSide.LONG and current_ai_probability_up < 0.40:
            return PositionExitSignal(True, ExitReason.PREDICTION_REVERSAL, f"AI probability reversed to bearish (P(up) = {current_ai_probability_up:.2%})")
        elif position.side == PositionSide.SHORT and current_ai_probability_up > 0.60:
            return PositionExitSignal(True, ExitReason.PREDICTION_REVERSAL, f"AI probability reversed to bullish (P(up) = {current_ai_probability_up:.2%})")

    return PositionExitSignal(False)
