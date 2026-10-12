"""
StockSense AI — LAN Device Access Control Middleware
Enforces perimeter security on all incoming network requests over the LAN.
- Loopback / Localhost requests are auto-approved (server host is never locked out).
- Remote LAN devices must register and obtain administrator approval + secret device token.
- Exempt endpoints (health, status check, registration) allow discovery & onboarding.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional, Set
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy import select

from app.core.config import settings
from app.core.lan_service import is_loopback, hash_token
from app.core.logging import get_logger
from app.db.session import AsyncSessionLocal
from app.models.lan import LANDevice, LANAccessLog

logger = get_logger("app.core.lan_middleware")

_session_factory = None

def get_session_factory():
    return _session_factory or AsyncSessionLocal

def set_session_factory(factory):
    global _session_factory
    _session_factory = factory

# Endpoints exempt from LAN device authorization checks
EXEMPT_PATH_PREFIXES = (
    "/health",
    "/api/v1/health",
    "/api/v1/lan/status",
    "/api/v1/lan/devices/register",
    "/api/v1/lan/devices/check",
    "/docs",
    "/openapi.json",
    "/api/v1/openapi.json",
    "/redoc",
    "/favicon.ico",
)


def extract_client_ip(request: Request) -> str:
    """Extracts the real client IP, prioritizing proxy headers."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        # First entry in X-Forwarded-For is the originating client
        return forwarded.split(",")[0].strip()
    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        return real_ip.strip()
    if request.client and request.client.host:
        return request.client.host
    return "127.0.0.1"


class LANDeviceAccessMiddleware(BaseHTTPMiddleware):
    """
    Middleware that intercepts incoming HTTP requests to ensure only authorized LAN
    devices access StockSense AI API endpoints.
    """

    async def dispatch(self, request: Request, call_next):
        # 1. Allow CORS preflight requests without restriction
        if request.method == "OPTIONS":
            return await call_next(request)

        # 2. Check if LAN security is active
        if not settings.lan_enabled or not settings.lan_device_auth_required:
            return await call_next(request)

        # 3. Check for exempt public paths
        path = request.url.path
        if any(path == prefix or path.startswith(f"{prefix}/") or path == f"{prefix}" for prefix in EXEMPT_PATH_PREFIXES):
            return await call_next(request)

        # Also exempt root path
        if path in ("/", ""):
            return await call_next(request)

        client_ip = extract_client_ip(request)

        # Check if caller is explicitly identified as a remote LAN client or provides a device ID
        is_remote_client = (
            request.headers.get("x-client-type") == "remote-lan"
            or bool(request.headers.get("x-device-id"))
            or bool(request.headers.get("X-Device-ID"))
        )

        # 4. Local loopback requests (originating on the laptop itself) are automatically trusted
        # Remote devices proxied through Next.js must NOT bypass authorization.
        if settings.lan_auto_approve_local and is_loopback(client_ip) and not is_remote_client:
            return await call_next(request)

        # 5. For remote LAN clients, require X-Device-ID
        device_id = (
            request.headers.get("x-device-id")
            or request.headers.get("X-Device-ID")
            or request.query_params.get("device_id")
        )
        device_token = (
            request.headers.get("x-device-token")
            or request.headers.get("X-Device-Token")
        )

        user_agent = request.headers.get("user-agent", "")

        if not device_id:
            logger.warning(
                "LAN access blocked: Missing device identification",
                ip=client_ip,
                path=path,
                method=request.method,
            )
            # Asynchronously log unauthorized attempt
            await self._log_event(
                device_id=None,
                device_identifier=None,
                ip_address=client_ip,
                user_agent=user_agent,
                endpoint=path,
                method=request.method,
                action="UNAUTHORIZED_ACCESS_ATTEMPT",
                status="BLOCKED",
                details="Missing X-Device-ID header on remote LAN request",
            )
            return JSONResponse(
                status_code=403,
                content={
                    "detail": "Device access control active. Device registration and authorization required.",
                    "code": "DEVICE_REGISTRATION_REQUIRED",
                    "client_ip": client_ip,
                },
            )

        # 6. Query device status from database
        session_maker = get_session_factory()
        async with session_maker() as db:
            try:
                result = await db.execute(
                    select(LANDevice).where(LANDevice.device_identifier == device_id)
                )
                device = result.scalars().first()
            except Exception as e:
                logger.error("Error querying LANDevice in middleware", error=str(e))
                # Fail securely
                return JSONResponse(
                    status_code=500,
                    content={"detail": "LAN security validation failed temporarily.", "code": "SERVER_ERROR"},
                )

            # Device not registered in database
            if not device:
                await self._log_event(
                    device_id=None,
                    device_identifier=device_id,
                    ip_address=client_ip,
                    user_agent=user_agent,
                    endpoint=path,
                    method=request.method,
                    action="UNAUTHORIZED_ACCESS_ATTEMPT",
                    status="BLOCKED",
                    details=f"Unregistered device_id '{device_id}' attempted access",
                )
                return JSONResponse(
                    status_code=403,
                    content={
                        "detail": "Device not recognized. Please submit access request from the device gate.",
                        "code": "DEVICE_NOT_REGISTERED",
                        "device_id": device_id,
                    },
                )

            # Device is pending admin approval
            if device.status == "PENDING":
                return JSONResponse(
                    status_code=403,
                    content={
                        "detail": "Device authorization pending approval by administrator.",
                        "code": "DEVICE_PENDING",
                        "device_id": device_id,
                        "device_name": device.device_name,
                    },
                )

            # Device is rejected or revoked
            if device.status in ("REJECTED", "REVOKED"):
                await self._log_event(
                    device_id=device.id,
                    device_identifier=device_id,
                    ip_address=client_ip,
                    user_agent=user_agent,
                    endpoint=path,
                    method=request.method,
                    action="UNAUTHORIZED_ACCESS_ATTEMPT",
                    status="BLOCKED",
                    details=f"Device is {device.status}. Reason: {device.rejection_reason or 'None'}",
                )
                return JSONResponse(
                    status_code=403,
                    content={
                        "detail": f"Device access has been {device.status.lower()} by administrator. {device.rejection_reason or ''}".strip(),
                        "code": "DEVICE_BLOCKED",
                        "status": device.status,
                        "rejection_reason": device.rejection_reason,
                    },
                )

            # Device is approved: verify secret token hash
            if device.status == "APPROVED":
                if not device_token or hash_token(device_token) != device.token_hash:
                    await self._log_event(
                        device_id=device.id,
                        device_identifier=device_id,
                        ip_address=client_ip,
                        user_agent=user_agent,
                        endpoint=path,
                        method=request.method,
                        action="UNAUTHORIZED_ACCESS_ATTEMPT",
                        status="BLOCKED",
                        details="Invalid or missing X-Device-Token for approved device",
                    )
                    return JSONResponse(
                        status_code=403,
                        content={
                            "detail": "Invalid or missing device credentials. Device token mismatch.",
                            "code": "DEVICE_UNAUTHORIZED",
                        },
                    )

                # Approved & verified: update heartbeat
                try:
                    device.last_seen_at = datetime.now(timezone.utc)
                    device.current_ip = client_ip
                    await db.commit()
                except Exception:
                    await db.rollback()

        # All checks passed — forward request
        return await call_next(request)

    async def _log_event(
        self,
        device_id: Optional[Any],
        device_identifier: Optional[str],
        ip_address: str,
        user_agent: str,
        endpoint: str,
        method: str,
        action: str,
        status: str,
        details: Optional[str] = None,
    ):
        """Asynchronously writes a security audit event to lan_access_logs."""
        try:
            session_maker = get_session_factory()
            async with session_maker() as db:
                log_entry = LANAccessLog(
                    device_id=device_id,
                    device_identifier=device_identifier,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    endpoint=endpoint,
                    method=method,
                    action=action,
                    status=status,
                    details=details,
                    timestamp=datetime.now(timezone.utc),
                )
                db.add(log_entry)
                await db.commit()
        except Exception as e:
            logger.warning("Failed to record LAN access audit log", error=str(e))
