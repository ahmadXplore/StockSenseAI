"""
StockSense AI — Data Quality Engine & Anomaly Detection Tests
Tests OHLC validation, negative prices, deduplication, and corporate action aware extreme returns.
"""

import pytest
from datetime import datetime, timezone, date
from decimal import Decimal

from app.data.canonical.price import CanonicalPriceDTO
from app.data.canonical.corporate_action import CorporateActionDTO, CorporateActionType
from app.data.validation.price_validation import validate_ohlcv_record, validate_price_series
from app.data.validation.extreme_values import classify_extreme_moves, ExtremeMoveClassification
from app.data.validation.data_quality import DataQualityEngine


def test_invalid_ohlc_geometry_rejected():
    # 1. High lower than Open
    bad_price_1 = CanonicalPriceDTO(
        security_id="PK.PSX.TEST",
        ticker="TEST",
        timestamp=datetime(2024, 1, 1, tzinfo=timezone.utc),
        open=Decimal("100.0"),
        high=Decimal("95.0"), # Invalid: high < open
        low=Decimal("90.0"),
        close=Decimal("98.0"),
        adj_close=Decimal("98.0"),
        volume=1000,
    )
    is_valid, errs = validate_ohlcv_record(bad_price_1)
    assert not is_valid
    assert any("High" in e for e in errs)

    # 2. Negative price
    bad_price_2 = CanonicalPriceDTO(
        security_id="PK.PSX.TEST",
        ticker="TEST",
        timestamp=datetime(2024, 1, 2, tzinfo=timezone.utc),
        open=Decimal("100.0"),
        high=Decimal("105.0"),
        low=Decimal("-10.0"), # Invalid: negative price
        close=Decimal("102.0"),
        adj_close=Decimal("102.0"),
        volume=1000,
    )
    is_valid_2, errs_2 = validate_ohlcv_record(bad_price_2)
    assert not is_valid_2
    assert any("Negative" in e for e in errs_2)


def test_extreme_move_with_corporate_action_awareness():
    # Stock undergoes 2-for-1 split on 2024-03-15: close drops from 200 to 100 (-50%)
    p1 = CanonicalPriceDTO(
        security_id="US.NASDAQ.SPLIT",
        ticker="SPLIT",
        timestamp=datetime(2024, 3, 14, tzinfo=timezone.utc),
        open=Decimal("198.0"),
        high=Decimal("202.0"),
        low=Decimal("197.0"),
        close=Decimal("200.0"),
        adj_close=Decimal("200.0"),
        volume=50000,
    )
    p2 = CanonicalPriceDTO(
        security_id="US.NASDAQ.SPLIT",
        ticker="SPLIT",
        timestamp=datetime(2024, 3, 15, tzinfo=timezone.utc),
        open=Decimal("100.0"),
        high=Decimal("102.0"),
        low=Decimal("99.0"),
        close=Decimal("100.0"),
        adj_close=Decimal("100.0"),
        volume=100000,
    )

    action = CorporateActionDTO(
        security_id="US.NASDAQ.SPLIT",
        ticker="SPLIT",
        action_date=date(2024, 3, 15),
        action_type=CorporateActionType.STOCK_SPLIT,
        split_ratio=Decimal("2.0")
    )

    anomalies = classify_extreme_moves([p1, p2], corporate_actions=[action])
    assert len(anomalies) == 1
    assert anomalies[0].classification == ExtremeMoveClassification.POSSIBLE_CORPORATE_ACTION
    assert "Correlated with corporate action" in anomalies[0].notes


def test_data_quality_engine_scoring():
    engine = DataQualityEngine()
    
    valid_prices = [
        CanonicalPriceDTO(
            security_id="PK.PSX.GOOD",
            ticker="GOOD",
            timestamp=datetime(2024, 1, i, tzinfo=timezone.utc),
            open=Decimal("50.0"),
            high=Decimal("52.0"),
            low=Decimal("49.0"),
            close=Decimal("51.0"),
            adj_close=Decimal("51.0"),
            volume=1000,
        )
        for i in range(1, 10)
    ]

    result = engine.evaluate(
        provider="test_provider",
        market="PK",
        exchange="PSX",
        prices=valid_prices
    )

    assert result.status == "PASSED"
    assert result.records_accepted == 9
    assert result.records_rejected == 0
    assert result.quality_score == 100.0
