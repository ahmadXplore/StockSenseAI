"""
Tests: Transaction Costs & Friction Layer
Covers slippage, spread, commissions, taxes, and the master compute_transaction_friction for US and PSX markets.
"""

import pytest
from app.backtesting.costs.slippage import calculate_slippage
from app.backtesting.costs.commissions import calculate_commission
from app.backtesting.costs.taxes import calculate_taxes_and_statutory_fees
from app.backtesting.costs.spread import estimate_bid_ask_spread
from app.backtesting.costs.transaction_costs import compute_transaction_friction
from app.backtesting.schemas import OrderSide, SlippageModelType, BacktestConfig


# ── Slippage Tests ──

def test_fixed_bps_slippage_buy():
    # 5 bps = 0.05% of 100 = 0.05 -> executed = 100.05
    exec_price = calculate_slippage(
        reference_price=100.0,
        shares=100,
        side=OrderSide.BUY,
        model_type=SlippageModelType.FIXED_BPS,
        slippage_bps=5.0,
    )
    assert abs(exec_price - 100.05) < 0.001


def test_fixed_bps_slippage_sell():
    # Sells get worse fill (lower price)
    exec_price = calculate_slippage(
        reference_price=100.0,
        shares=100,
        side=OrderSide.SELL,
        model_type=SlippageModelType.FIXED_BPS,
        slippage_bps=5.0,
    )
    assert abs(exec_price - 99.95) < 0.001


def test_fixed_pct_slippage():
    exec_price = calculate_slippage(
        reference_price=200.0,
        shares=50,
        side=OrderSide.BUY,
        model_type=SlippageModelType.FIXED_PCT,
        slippage_bps=0.1, # 0.1%
    )
    assert abs(exec_price - 200.20) < 0.01


def test_volatility_slippage_high_vol():
    high_vol_price = calculate_slippage(
        reference_price=100.0,
        shares=100,
        side=OrderSide.BUY,
        model_type=SlippageModelType.VOLATILITY_BASED,
        atr_volatility=5.0,
    )
    low_vol_price = calculate_slippage(
        reference_price=100.0,
        shares=100,
        side=OrderSide.BUY,
        model_type=SlippageModelType.VOLATILITY_BASED,
        atr_volatility=0.5,
    )
    assert high_vol_price > low_vol_price


# ── Commission Tests ──

def test_per_share_commission():
    res = calculate_commission(
        trade_value=15000.0,
        shares=100,
        market_code="US",
        commission_per_share=0.005,
    )
    assert abs(res - 0.50) < 0.001


def test_percentage_commission():
    res = calculate_commission(
        trade_value=10000.0,
        shares=50,
        market_code="US",
        commission_pct=0.001,
    )
    assert abs(res - 10.0) < 0.01


def test_minimum_commission_enforced():
    res = calculate_commission(
        trade_value=10.0,
        shares=10,
        market_code="US",
        commission_pct=0.001,
        min_commission=5.0,
    )
    assert res >= 5.0


# ── Transaction Taxes Tests ──

def test_us_sec_fee_on_sell():
    tax = calculate_taxes_and_statutory_fees(
        trade_value=100000.0,
        market_code="US",
        side=OrderSide.SELL,
    )
    assert tax > 0.0


def test_psx_statutory_tax():
    tax = calculate_taxes_and_statutory_fees(
        trade_value=100000.0,
        market_code="PK",
        side=OrderSide.SELL,
    )
    assert tax > 0.0


def test_uk_stamp_duty_only_on_buy():
    tax_buy = calculate_taxes_and_statutory_fees(trade_value=10000.0, market_code="UK", side=OrderSide.BUY)
    tax_sell = calculate_taxes_and_statutory_fees(trade_value=10000.0, market_code="UK", side=OrderSide.SELL)
    assert tax_buy > tax_sell


def test_india_stt():
    tax = calculate_taxes_and_statutory_fees(trade_value=50000.0, market_code="IN", side=OrderSide.SELL)
    assert tax > 0.0


# ── Master Transaction Cost Calculator Tests ──

def test_compute_friction_buy_us():
    cfg = BacktestConfig(start_date="2022-01-01", end_date="2023-12-31", market_code="US")
    breakdown = compute_transaction_friction(
        reference_price=150.0,
        shares=100,
        side=OrderSide.BUY,
        market_code="US",
        config=cfg,
        daily_volume=1_000_000,
        atr_volatility=3.0,
    )
    assert breakdown.total_friction > 0.0
    assert breakdown.commission >= 0.0
    assert breakdown.slippage_cost >= 0.0


def test_compute_friction_sell_psx():
    cfg = BacktestConfig(start_date="2022-01-01", end_date="2023-12-31", market_code="PK")
    breakdown = compute_transaction_friction(
        reference_price=80.0,
        shares=1000,
        side=OrderSide.SELL,
        market_code="PK",
        config=cfg,
    )
    assert breakdown.total_friction > 0.0
    assert breakdown.taxes >= 0.0
