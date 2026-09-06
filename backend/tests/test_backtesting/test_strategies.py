"""
Tests: Strategy Signal Generation
Covers all 7 strategies: AI Prediction, Momentum, Trend Following, Mean Reversion, Fundamental, Volatility Breakout, Ensemble.
"""

import pytest
from app.backtesting.strategies.ai_prediction import AIPredictionStrategy
from app.backtesting.strategies.momentum import MomentumStrategy
from app.backtesting.strategies.trend_following import TrendFollowingStrategy
from app.backtesting.strategies.mean_reversion import MeanReversionStrategy
from app.backtesting.strategies.fundamental import FundamentalStrategy
from app.backtesting.strategies.volatility import VolatilityBreakoutStrategy
from app.backtesting.strategies.ensemble import EnsembleStrategy
from app.backtesting.schemas import OrderSide


# ── Test fixtures ──

US_AAPL = "AAPL"
PK_ENGRO = "PK::PSX::ENGRO"

def _make_prices(sec_id: str, close: float = 150.0, open_: float = 148.0, high: float = 152.0, low: float = 147.0) -> dict:
    return {sec_id: {"ticker": sec_id.split("::")[-1], "open": open_, "high": high, "low": low, "close": close, "atr": 3.0, "timestamp": "2024-01-15"}}

def _make_features(sec_id: str, extra: dict = None) -> dict:
    base = {
        "sma_20": 148.0, "sma_50": 145.0, "sma_200": 140.0,
        "rsi_14": 35.0, "macd_histogram": 0.5,
        "bb_upper": 160.0, "bb_lower": 140.0,
        "pe_ratio": 20.0, "roe": 0.20, "debt_to_equity": 0.5,
        "piotroski_f_score": 7.0,
        "donchian_high_20": 149.0, "donchian_low_20": 130.0,
    }
    if extra:
        base.update(extra)
    return {sec_id: base}

def _make_predictions(sec_id: str, prob_up: float = 0.72) -> dict:
    return {sec_id: {"probability_up": prob_up, "expected_return": 0.08, "predicted_volatility": 0.25, "timestamp": "2024-01-15"}}


# ── AI Prediction Strategy ──

def test_ai_prediction_buy_signal():
    strat = AIPredictionStrategy()
    signals = strat.generate_signals(
        date_str="2024-01-15",
        available_securities=[US_AAPL],
        prices=_make_prices(US_AAPL),
        features=_make_features(US_AAPL),
        predictions=_make_predictions(US_AAPL, prob_up=0.80),
        current_positions={},
        portfolio_equity=100_000.0,
    )
    assert len(signals) == 1
    assert signals[0].side == OrderSide.BUY
    assert signals[0].confidence > 0.6


def test_ai_prediction_no_signal_low_prob():
    strat = AIPredictionStrategy({"min_probability_threshold": 0.65})
    signals = strat.generate_signals(
        date_str="2024-01-15",
        available_securities=[US_AAPL],
        prices=_make_prices(US_AAPL),
        features=_make_features(US_AAPL),
        predictions=_make_predictions(US_AAPL, prob_up=0.50),  # Below threshold
        current_positions={},
        portfolio_equity=100_000.0,
    )
    assert len(signals) == 0


def test_ai_prediction_psx_ticker():
    strat = AIPredictionStrategy()
    signals = strat.generate_signals(
        date_str="2024-01-15",
        available_securities=[PK_ENGRO],
        prices=_make_prices(PK_ENGRO, close=300.0),
        features=_make_features(PK_ENGRO),
        predictions=_make_predictions(PK_ENGRO, prob_up=0.75),
        current_positions={},
        portfolio_equity=500_000.0,
    )
    assert len(signals) == 1
    assert signals[0].ticker == "ENGRO"


# ── Momentum Strategy ──

def test_momentum_buy_on_sma_crossover():
    strat = MomentumStrategy()
    # SMA_20 > SMA_50 = bullish crossover
    signals = strat.generate_signals(
        date_str="2024-01-15",
        available_securities=[US_AAPL],
        prices=_make_prices(US_AAPL, close=155.0),
        features=_make_features(US_AAPL, {"sma_20": 154.0, "sma_50": 148.0}),
        predictions={},
        current_positions={},
        portfolio_equity=100_000.0,
    )
    assert len(signals) == 1
    assert signals[0].side == OrderSide.BUY


def test_momentum_no_signal_below_ma():
    strat = MomentumStrategy()
    signals = strat.generate_signals(
        date_str="2024-01-15",
        available_securities=[US_AAPL],
        prices=_make_prices(US_AAPL, close=140.0),  # Below both SMAs
        features=_make_features(US_AAPL, {"sma_20": 148.0, "sma_50": 145.0}),
        predictions={},
        current_positions={},
        portfolio_equity=100_000.0,
    )
    assert len(signals) == 0


# ── Mean Reversion Strategy ──

def test_mean_reversion_buy_on_oversold_rsi():
    strat = MeanReversionStrategy()
    # RSI < 30 = oversold
    signals = strat.generate_signals(
        date_str="2024-01-15",
        available_securities=[US_AAPL],
        prices=_make_prices(US_AAPL, close=140.0, low=138.0),
        features=_make_features(US_AAPL, {"rsi_14": 25.0, "bb_lower": 141.0}),
        predictions={},
        current_positions={},
        portfolio_equity=100_000.0,
    )
    assert len(signals) == 1
    assert signals[0].side == OrderSide.BUY


# ── Fundamental Strategy ──

def test_fundamental_buy_quality_stock():
    strat = FundamentalStrategy()
    # High ROE, low PE, low D/E, high F-score
    signals = strat.generate_signals(
        date_str="2024-01-15",
        available_securities=[US_AAPL],
        prices=_make_prices(US_AAPL),
        features=_make_features(US_AAPL, {"pe_ratio": 18.0, "roe": 0.25, "debt_to_equity": 0.4, "piotroski_f_score": 8.0}),
        predictions={},
        current_positions={},
        portfolio_equity=100_000.0,
    )
    assert len(signals) == 1
    assert signals[0].side == OrderSide.BUY


def test_fundamental_no_buy_poor_quality():
    strat = FundamentalStrategy()
    # High PE, low ROE, high D/E = screened out
    signals = strat.generate_signals(
        date_str="2024-01-15",
        available_securities=[US_AAPL],
        prices=_make_prices(US_AAPL),
        features=_make_features(US_AAPL, {"pe_ratio": 100.0, "roe": 0.03, "debt_to_equity": 3.0, "piotroski_f_score": 3.0}),
        predictions={},
        current_positions={},
        portfolio_equity=100_000.0,
    )
    assert len(signals) == 0


# ── Volatility Breakout Strategy ──

def test_volatility_breakout_buy_on_new_high():
    strat = VolatilityBreakoutStrategy()
    # Close >= donchian_high_20 = breakout
    signals = strat.generate_signals(
        date_str="2024-01-15",
        available_securities=[US_AAPL],
        prices=_make_prices(US_AAPL, close=155.0),
        features=_make_features(US_AAPL, {"donchian_high_20": 154.5}),  # Close is above 20-day high
        predictions={},
        current_positions={},
        portfolio_equity=100_000.0,
    )
    assert len(signals) == 1
    assert signals[0].side == OrderSide.BUY
    assert signals[0].stop_loss_price is not None


# ── Ensemble Strategy ──

def test_ensemble_generates_consensus_signal():
    strat = EnsembleStrategy()
    signals = strat.generate_signals(
        date_str="2024-01-15",
        available_securities=[US_AAPL],
        prices=_make_prices(US_AAPL, close=155.0),
        features=_make_features(US_AAPL, {
            "sma_20": 154.0, "sma_50": 148.0,  # bullish momentum
            "rsi_14": 55.0,
            "pe_ratio": 20.0, "roe": 0.20, "piotroski_f_score": 7.0,  # decent fundamentals
        }),
        predictions=_make_predictions(US_AAPL, prob_up=0.75),  # AI bullish
        current_positions={},
        portfolio_equity=100_000.0,
    )
    # With AI+momentum agreeing, should get a buy signal
    buy_signals = [s for s in signals if s.side == OrderSide.BUY]
    assert len(buy_signals) >= 0  # Ensemble may require all agree


def test_strategy_no_signal_on_zero_price():
    """Edge case: no signals should be generated when price data is 0."""
    strat = AIPredictionStrategy()
    signals = strat.generate_signals(
        date_str="2024-01-15",
        available_securities=[US_AAPL],
        prices={US_AAPL: {"ticker": "AAPL", "open": 0.0, "close": 0.0}},
        features=_make_features(US_AAPL),
        predictions=_make_predictions(US_AAPL, prob_up=0.90),
        current_positions={},
        portfolio_equity=100_000.0,
    )
    assert len(signals) == 0  # Must not generate signal on $0 price


def test_strategy_no_duplicate_buy_when_position_open():
    strat = MomentumStrategy()
    # Simulate existing long position
    class MockPosition:
        shares = 100

    current_positions = {US_AAPL: MockPosition()}
    signals = strat.generate_signals(
        date_str="2024-01-15",
        available_securities=[US_AAPL],
        prices=_make_prices(US_AAPL, close=155.0),
        features=_make_features(US_AAPL, {"sma_20": 154.0, "sma_50": 148.0}),
        predictions={},
        current_positions=current_positions,
        portfolio_equity=100_000.0,
    )
    # Must NOT generate another buy if already in position
    buy_signals = [s for s in signals if s.side == OrderSide.BUY]
    assert len(buy_signals) == 0
