"""
StockSense AI — Multi-Market REST API Endpoint Tests
Tests markets, exchanges, security search, and price query endpoints.
"""

import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_list_markets_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/markets")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 6
        codes = [m["code"] for m in data]
        assert "PK" in codes
        assert "US" in codes
        assert "GB" in codes


@pytest.mark.asyncio
async def test_list_exchanges_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/exchanges")
        assert resp.status_code == 200
        data = resp.json()
        codes = [e["code"] for e in data]
        assert "PSX" in codes
        assert "NASDAQ" in codes
        assert "NYSE" in codes
        assert "LSE" in codes


@pytest.mark.asyncio
async def test_search_securities_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/securities/search?q=AAPL")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 1
        assert any(s["symbol"] == "AAPL" for s in data)


@pytest.mark.asyncio
async def test_get_providers_health_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/providers/health")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 2
        provider_names = [p["provider_name"] for p in data]
        assert "psx_data_provider" in provider_names
        assert "international_data_provider" in provider_names
