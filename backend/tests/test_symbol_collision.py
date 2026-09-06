"""
StockSense AI — Critical Symbol Collision Test (Prompt 3, Section 38)
Verifies that identical symbols residing on different exchanges/markets
receive globally unique and distinct security_id keys.
"""

import pytest
from app.data.canonical.market import build_security_id, parse_security_id
from app.data.canonical.security import SecurityDTO, SecurityStatus, SecurityType


def test_symbol_collision_prevention():
    """
    Test Case:
    Create symbol 'ABC' on Exchange A (PSX, Market PK)
    Create symbol 'ABC' on Exchange B (NASDAQ, Market US)
    Create symbol 'ABC' on Exchange C (LSE, Market GB)

    Verify that all 3 entities have unique security_id keys and do not collide.
    """
    sec_pk = SecurityDTO(
        security_id=build_security_id("PK", "PSX", "ABC"),
        exchange_id="PSX",
        market_id="PK",
        symbol="ABC",
        company_name="ABC Pakistan Limited",
        country="Pakistan",
        currency="PKR"
    )

    sec_us = SecurityDTO(
        security_id=build_security_id("US", "NASDAQ", "ABC"),
        exchange_id="NASDAQ",
        market_id="US",
        symbol="ABC",
        company_name="AmerisourceBergen Corp.",
        country="USA",
        currency="USD"
    )

    sec_gb = SecurityDTO(
        security_id=build_security_id("GB", "LSE", "ABC"),
        exchange_id="LSE",
        market_id="GB",
        symbol="ABC",
        company_name="ABC UK PLC",
        country="United Kingdom",
        currency="GBP"
    )

    # 1. Assert security_ids are unique
    assert sec_pk.security_id == "PK.PSX.ABC"
    assert sec_us.security_id == "US.NASDAQ.ABC"
    assert sec_gb.security_id == "GB.LSE.ABC"

    unique_ids = {sec_pk.security_id, sec_us.security_id, sec_gb.security_id}
    assert len(unique_ids) == 3, "Symbol collision detected! All security_ids must be unique."

    # 2. Assert parsing recovers correct market and exchange
    m_pk, e_pk, s_pk = parse_security_id(sec_pk.security_id)
    assert m_pk == "PK" and e_pk == "PSX" and s_pk == "ABC"

    m_us, e_us, s_us = parse_security_id(sec_us.security_id)
    assert m_us == "US" and e_us == "NASDAQ" and s_us == "ABC"
