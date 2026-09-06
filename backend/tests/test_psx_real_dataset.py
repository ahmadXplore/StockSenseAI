"""
StockSense AI — Real PSX Dataset Integration Tests (Prompt 3, Section 39)
Tests streaming, validation, and security extraction against actual local PSX dataset.
"""

import pytest
import os
from app.data.providers.psx.provider import PSXMarketDataProvider
from app.data.providers.psx.parser import parse_psx_csv_stream, extract_psx_securities_from_csv


def test_real_psx_dataset_streaming():
    provider = PSXMarketDataProvider()
    if not os.path.exists(provider.csv_path):
        pytest.skip(f"PSX CSV dataset file not present at {provider.csv_path}")

    # Stream 500 records
    sample_records = []
    for price_dto, err in parse_psx_csv_stream(provider.csv_path, limit=500):
        if price_dto:
            sample_records.append(price_dto)

    assert len(sample_records) == 500
    for p in sample_records:
        assert p.currency == "PKR"
        assert p.security_id.startswith("PK.PSX.")
        assert p.is_geometrically_valid()


def test_real_psx_dataset_security_extraction():
    provider = PSXMarketDataProvider()
    if not os.path.exists(provider.csv_path):
        pytest.skip(f"PSX CSV dataset file not present at {provider.csv_path}")

    # Scan 2000 rows
    securities = extract_psx_securities_from_csv(provider.csv_path, limit=2000)
    assert len(securities) > 50
    assert "AABS" in securities or "ABL" in securities or "ABOT" in securities
