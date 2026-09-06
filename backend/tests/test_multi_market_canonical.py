"""
StockSense AI — Critical Multi-Market Canonical Test (Prompt 3, Section 37)
Verifies that AAPL (NASDAQ, USD) and ENGRO (PSX, PKR) pass through the EXACT SAME
canonical model and pipeline without schema differences or market discrimination.
"""

import pytest
from datetime import datetime, timezone
from decimal import Decimal

from app.data.canonical.market import build_security_id
from app.data.canonical.price import CanonicalPriceDTO
from app.data.canonical.security import SecurityDTO, SecurityStatus, SecurityType
from app.data.validation.price_validation import validate_ohlcv_record
from app.data.ingestion.pipeline import IngestionPipeline


@pytest.mark.asyncio
async def test_multi_market_canonical_model_parity():
    """
    Verifies that AAPL (US/NASDAQ/USD) and ENGRO (PK/PSX/PKR) share the identical canonical schema.
    """
    # 1. Instantiate Canonical Price for AAPL
    aapl_id = build_security_id("US", "NASDAQ", "AAPL")
    aapl_price = CanonicalPriceDTO(
        security_id=aapl_id,
        ticker="AAPL",
        timestamp=datetime(2024, 5, 10, 16, 0, tzinfo=timezone.utc),
        open=Decimal("182.50"),
        high=Decimal("184.20"),
        low=Decimal("182.10"),
        close=Decimal("183.05"),
        adj_close=Decimal("183.05"),
        volume=54321000,
        currency="USD",
        data_source="yfinance",
        is_adjusted=True,
        quality_flag="ok"
    )

    # 2. Instantiate Canonical Price for ENGRO
    engro_id = build_security_id("PK", "PSX", "ENGRO")
    engro_price = CanonicalPriceDTO(
        security_id=engro_id,
        ticker="ENGRO",
        timestamp=datetime(2024, 5, 10, 15, 30, tzinfo=timezone.utc),
        open=Decimal("345.00"),
        high=Decimal("352.50"),
        low=Decimal("344.00"),
        close=Decimal("350.25"),
        adj_close=Decimal("350.25"),
        volume=1250000,
        currency="PKR",
        data_source="kaggle_psx",
        is_adjusted=False,
        quality_flag="ok"
    )

    # 3. Verify validation rules apply identically to both
    valid_aapl, errs_aapl = validate_ohlcv_record(aapl_price)
    assert valid_aapl, f"AAPL failed validation: {errs_aapl}"

    valid_engro, errs_engro = validate_ohlcv_record(engro_price)
    assert valid_engro, f"ENGRO failed validation: {errs_engro}"

    # 4. Verify canonical properties & types are completely symmetric
    for p in [aapl_price, engro_price]:
        assert isinstance(p.open, Decimal)
        assert isinstance(p.high, Decimal)
        assert isinstance(p.low, Decimal)
        assert isinstance(p.close, Decimal)
        assert isinstance(p.adj_close, Decimal)
        assert isinstance(p.volume, int)
        assert p.is_geometrically_valid()

    assert aapl_price.currency == "USD"
    assert engro_price.currency == "PKR"
    assert aapl_price.security_id == "US.NASDAQ.AAPL"
    assert engro_price.security_id == "PK.PSX.ENGRO"

    # 5. Run both through the IngestionPipeline without DB session
    pipeline = IngestionPipeline()
    res_us = await pipeline.run(
        provider_name="yfinance",
        market_code="US",
        exchange_code="NASDAQ",
        raw_prices=[aapl_price],
    )
    assert res_us.status == "PASSED"
    assert res_us.records_accepted == 1

    res_pk = await pipeline.run(
        provider_name="kaggle_psx",
        market_code="PK",
        exchange_code="PSX",
        raw_prices=[engro_price],
    )
    assert res_pk.status == "PASSED"
    assert res_pk.records_accepted == 1
