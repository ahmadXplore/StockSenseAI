"""
StockSense AI — Critical Survivorship Bias Test (Prompt 3, Section 36)
Verifies that delisted securities are included in historical universe queries
for dates prior to delisting, and excluded after delisting.
"""

import pytest
from datetime import date
from decimal import Decimal

from app.data.canonical.security import SecurityDTO, SecurityStatus, SecurityType
from app.data.canonical.universe import resolve_historical_universe


def test_survivorship_bias_point_in_time():
    """
    Test Case:
    Security A:
      listed: 2018-01-01
      delisted: 2022-12-31
    
    Universe query as of 2020-06-15 -> Security A MUST BE INCLUDED.
    Universe query as of 2023-01-15 -> Security A MUST BE EXCLUDED.
    """
    security_a = SecurityDTO(
        security_id="PK.PSX.SECA",
        exchange_id="PSX",
        market_id="PK",
        symbol="SECA",
        company_name="Security A Ltd.",
        currency="PKR",
        country="Pakistan",
        status=SecurityStatus.DELISTED,
        listing_date=date(2018, 1, 1),
        delisting_date=date(2022, 12, 31),
        delisting_reason="Voluntary delisting / buyout"
    )

    security_b = SecurityDTO(
        security_id="PK.PSX.SECB",
        exchange_id="PSX",
        market_id="PK",
        symbol="SECB",
        company_name="Security B Ltd.",
        currency="PKR",
        country="Pakistan",
        status=SecurityStatus.ACTIVE,
        listing_date=date(2015, 1, 1),
        delisting_date=None,
    )

    securities_pool = [security_a, security_b]

    # Query 1: As of 2020-06-15 (During active life of Security A)
    universe_2020 = resolve_historical_universe(
        market="PK",
        exchange="PSX",
        as_of_date=date(2020, 6, 15),
        securities=securities_pool
    )

    sec_ids_2020 = [s.security_id for s in universe_2020.securities]
    assert "PK.PSX.SECA" in sec_ids_2020, "Security A MUST be included in the 2020 historical universe"
    assert "PK.PSX.SECB" in sec_ids_2020
    assert universe_2020.total_count == 2
    assert universe_2020.delisted_included_count == 1

    # Query 2: As of 2023-01-15 (Post delisting of Security A)
    universe_2023 = resolve_historical_universe(
        market="PK",
        exchange="PSX",
        as_of_date=date(2023, 1, 15),
        securities=securities_pool
    )

    sec_ids_2023 = [s.security_id for s in universe_2023.securities]
    assert "PK.PSX.SECA" not in sec_ids_2023, "Security A MUST NOT be included in the 2023 universe"
    assert "PK.PSX.SECB" in sec_ids_2023
    assert universe_2023.total_count == 1
    assert universe_2023.delisted_included_count == 0

    # Query 3: As of 2017-01-01 (Pre listing of Security A)
    universe_2017 = resolve_historical_universe(
        market="PK",
        exchange="PSX",
        as_of_date=date(2017, 1, 1),
        securities=securities_pool
    )
    sec_ids_2017 = [s.security_id for s in universe_2017.securities]
    assert "PK.PSX.SECA" not in sec_ids_2017, "Security A was not yet listed in 2017"
