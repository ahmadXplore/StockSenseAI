"""
StockSense AI — LAN Device Access & Security Test Suite
Tests:
  - LAN status endpoint
  - Remote device registration & pending gating
  - Localhost loopback auto-approval
  - Admin approval flow and secret token issuance
  - Token-authenticated access to protected API endpoints
  - Rejection & Revocation enforcement
  - Security audit logging
"""

import pytest
import pytest_asyncio
import uuid
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.db.base import Base
from app.db.session import get_db
from app.core.security import create_access_token
from app.models.lan import LANDevice, LANAccessLog


from app.core.lan_middleware import set_session_factory

# Test SQLite in-memory database
TEST_DB_URL = "sqlite+aiosqlite:///:memory:"

@pytest_asyncio.fixture(scope="function")
async def test_db():
    engine = create_async_engine(
        TEST_DB_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    # Strip schemas for SQLite
    for table in Base.metadata.tables.values():
        table.schema = None

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    set_session_factory(async_session)

    yield async_session

    set_session_factory(None)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def client(test_db):
    async def override_get_db():
        async with test_db() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def admin_token():
    return create_access_token(
        user_id=str(uuid.uuid4()),
        name="Security Administrator",
        email="admin@stocksense.lan",
        is_admin=True,
        role="admin",
    )


@pytest.mark.asyncio
async def test_lan_status_public(client: AsyncClient):
    """Verifies that the LAN status endpoint is publicly accessible and returns network info."""
    res = await client.get("/api/v1/lan/status")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "online"
    assert "host_ip" in data
    assert "ports" in data
    assert data["ports"]["frontend"] in [3000, 3005]
    assert data["components"]["database"] == "connected"


@pytest.mark.asyncio
async def test_local_loopback_auto_approved(client: AsyncClient):
    """Ensures requests originating from localhost loopback are never blocked."""
    # Loopback request with no headers to /health
    res = await client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "healthy"


@pytest.mark.asyncio
async def test_remote_client_missing_device_id_blocked(client: AsyncClient):
    """Remote clients connecting without X-Device-ID must receive HTTP 403."""
    headers = {"X-Forwarded-For": "192.168.1.188"}
    res = await client.get("/api/v1/settings", headers=headers)
    assert res.status_code == 403
    data = res.json()
    assert data["code"] == "DEVICE_REGISTRATION_REQUIRED"


@pytest.mark.asyncio
async def test_remote_device_lifecycle(client: AsyncClient, admin_token: str):
    """
    Full LAN access lifecycle:
    1. Remote device self-registers -> PENDING
    2. Remote device attempts protected call -> BLOCKED (DEVICE_PENDING)
    3. Admin lists pending devices
    4. Admin approves device -> receives token
    5. Remote device checks status -> receives token
    6. Remote device accesses protected endpoint with token -> SUCCESS
    7. Admin revokes device
    8. Remote device attempts access -> BLOCKED (DEVICE_BLOCKED)
    """
    remote_ip = "192.168.1.77"
    device_uuid = f"device-test-{uuid.uuid4().hex[:12]}"
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    device_remote_headers = {
        "X-Forwarded-For": remote_ip,
        "X-Device-ID": device_uuid,
    }

    # 1. Register device
    reg_res = await client.post(
        "/api/v1/lan/devices/register",
        headers={"X-Forwarded-For": remote_ip},
        json={
            "device_identifier": device_uuid,
            "device_name": "Test iPhone 15 Pro",
            "user_agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X)",
        },
    )
    assert reg_res.status_code == 200
    reg_data = reg_res.json()
    assert reg_data["status"] == "PENDING"
    assert reg_data["is_approved"] is False

    # 2. Remote access attempt while PENDING -> 403
    blocked_res = await client.get("/api/v1/settings", headers=device_remote_headers)
    assert blocked_res.status_code == 403, f"Expected 403, got {blocked_res.status_code}: {blocked_res.text}"
    assert blocked_res.json()["code"] == "DEVICE_PENDING"

    # 3. Admin lists pending devices
    pending_res = await client.get("/api/v1/lan/devices/pending", headers=admin_headers)
    assert pending_res.status_code == 200
    pending_list = pending_res.json()
    assert any(d["device_identifier"] == device_uuid for d in pending_list)

    # 4. Admin approves device
    approve_res = await client.post(
        f"/api/v1/lan/devices/{device_uuid}/approve",
        headers=admin_headers,
    )
    assert approve_res.status_code == 200
    appr_data = approve_res.json()
    assert appr_data["success"] is True
    assert appr_data["status"] == "APPROVED"
    assert "token" in appr_data
    token = appr_data["token"]
    assert token.startswith("ss_dev_")

    # 5. Device polls check endpoint -> receives token
    check_res = await client.get(
        "/api/v1/lan/devices/check",
        headers=device_remote_headers,
    )
    assert check_res.status_code == 200
    check_data = check_res.json()
    assert check_data["status"] == "APPROVED"
    assert check_data["is_approved"] is True
    assert check_data["token"] == token

    # 6. Device makes protected request with valid token
    auth_remote_headers = {
        "X-Forwarded-For": remote_ip,
        "X-Device-ID": device_uuid,
        "X-Device-Token": token,
    }
    allowed_res = await client.get("/api/v1/settings", headers=auth_remote_headers)
    assert allowed_res.status_code == 200

    # 7. Admin revokes device
    revoke_res = await client.post(
        f"/api/v1/lan/devices/{device_uuid}/revoke",
        headers=admin_headers,
    )
    assert revoke_res.status_code == 200
    assert revoke_res.json()["status"] == "REVOKED"

    # 8. Device blocked after revocation
    revoked_res = await client.get("/api/v1/settings", headers=auth_remote_headers)
    assert revoked_res.status_code == 403
    assert revoked_res.json()["code"] == "DEVICE_BLOCKED"


@pytest.mark.asyncio
async def test_audit_logs_retrieval(client: AsyncClient, admin_token: str):
    """Verifies that LAN access logs are recorded and queryable by admins."""
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    logs_res = await client.get("/api/v1/lan/access-logs", headers=admin_headers)
    assert logs_res.status_code == 200
    logs = logs_res.json()
    assert isinstance(logs, list)
