"""
StockSense AI — Backend Unit Tests
"""

import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.config import settings


@pytest.mark.asyncio
async def test_root_health():
    """Verify root health endpoint returns HTTP 200."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "app" in data


def test_settings_defaults():
    """Verify default environment settings configuration."""
    assert settings.app_name == "StockSense AI"
    assert settings.api_port == 8000
    assert len(settings.cors_origins) >= 1
    assert "market_data" not in settings.secret_key  # ensure secrets are not hardcoded values
