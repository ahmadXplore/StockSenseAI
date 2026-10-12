"""
StockSense AI — LAN Device Access Control & Network Management Endpoints
Provides administrative APIs for managing connected LAN devices, reviewing
pending approval requests, revoking access, and viewing security audit logs.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, Header, Query, Request, status
from pydantic import BaseModel, Field
from sqlalchemy import select, desc, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.lan_middleware import extract_client_ip
from app.core.lan_service import (
    get_system_lan_status,
    is_loopback,
    generate_device_token,
    hash_token,
    get_laptop_lan_ip,
)
from app.core.logging import get_logger
from app.core.security import require_admin_user
from app.db.session import get_db
from app.models.lan import LANDevice, LANAccessLog

logger = get_logger("app.api.lan")
router = APIRouter()


# ─────────────────────────────────────────────────────────
# Schemas
# ─────────────────────────────────────────────────────────

class LANDeviceRegisterRequest(BaseModel):
    device_identifier: str = Field(..., min_length=8, max_length=128, description="Client unique UUID fingerprint")
    device_name: str = Field(..., min_length=2, max_length=100, description="Friendly device name (e.g. Chrome on Android)")
    user_agent: Optional[str] = Field(None, max_length=500)


class LANDeviceCheckResponse(BaseModel):
    device_id: str
    device_name: str
    status: str
    is_approved: bool
    is_server_host: bool = False
    token: Optional[str] = None
    rejection_reason: Optional[str] = None


class LANDeviceRejectRequest(BaseModel):
    reason: Optional[str] = Field("Access denied by administrator", max_length=500)


class LANDeviceUpdateRequest(BaseModel):
    device_name: Optional[str] = Field(None, min_length=2, max_length=100)


class LANDeviceResponse(BaseModel):
    id: str
    device_name: str
    device_identifier: str
    current_ip: str
    user_agent: Optional[str] = None
    status: str
    is_server_host: bool
    created_at: str
    last_seen_at: str
    approved_at: Optional[str] = None
    revoked_at: Optional[str] = None
    created_by: Optional[str] = None
    rejection_reason: Optional[str] = None


class LANAccessLogResponse(BaseModel):
    id: str
    device_id: Optional[str] = None
    device_identifier: Optional[str] = None
    ip_address: str
    user_agent: Optional[str] = None
    endpoint: str
    method: str
    action: str
    status: str
    details: Optional[str] = None
    timestamp: str


# ─────────────────────────────────────────────────────────
# Public / Unrestricted Endpoints
# ─────────────────────────────────────────────────────────

@router.get("/status", summary="Get LAN Server Status & Network Health")
async def get_lan_status(db: AsyncSession = Depends(get_db)):
    """Returns host LAN IP, active interfaces, port config, and component health."""
    return await get_system_lan_status(db)


@router.post("/devices/register", summary="Register Device for LAN Access")
async def register_lan_device(
    payload: LANDeviceRegisterRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Submits a device access request.
    If the request originates from the local host laptop and auto-approval is active,
    the device is automatically approved and issued an access token.
    """
    client_ip = extract_client_ip(request)
    user_agent = payload.user_agent or request.headers.get("user-agent", "")
    
    # Check if client explicitly indicates it is a remote LAN device
    is_remote = (
        request.headers.get("x-client-type") == "remote-lan"
        or request.headers.get("X-Client-Type") == "remote-lan"
        or payload.device_identifier.startswith("dev_")
    )
    is_local = settings.lan_auto_approve_local and is_loopback(client_ip) and not is_remote

    # Check for existing device registration
    stmt = select(LANDevice).where(LANDevice.device_identifier == payload.device_identifier)
    res = await db.execute(stmt)
    device = res.scalars().first()

    raw_token = None

    if is_local:
        # Localhost laptop device: auto-approve immediately
        if not device:
            raw_token, token_hash = generate_device_token()
            device = LANDevice(
                device_name=payload.device_name or "Host Laptop (Local Server)",
                device_identifier=payload.device_identifier,
                token_hash=token_hash,
                current_ip=client_ip,
                user_agent=user_agent,
                status="APPROVED",
                is_server_host=True,
                approved_at=datetime.now(timezone.utc),
                created_by="system (loopback auto-approved)",
            )
            db.add(device)
        else:
            device.status = "APPROVED"
            device.is_server_host = True
            device.current_ip = client_ip
            device.last_seen_at = datetime.now(timezone.utc)
            if not device.token_hash:
                raw_token, token_hash = generate_device_token()
                device.token_hash = token_hash

        await db.commit()
        await db.refresh(device)

        return {
            "status": "APPROVED",
            "is_approved": True,
            "is_server_host": True,
            "device_id": str(device.device_identifier),
            "device_name": device.device_name,
            "token": raw_token,
            "message": "Local server host access granted automatically.",
        }

    # Remote LAN client
    if device:
        # If device already registered
        device.current_ip = client_ip
        device.last_seen_at = datetime.now(timezone.utc)
        if payload.device_name:
            device.device_name = payload.device_name

        token_to_return = None
        if device.status == "APPROVED" and device.pending_claim_token:
            token_to_return = device.pending_claim_token
            device.pending_claim_token = None

        await db.commit()

        return {
            "status": device.status,
            "is_approved": device.status == "APPROVED",
            "is_server_host": device.is_server_host,
            "device_id": str(device.device_identifier),
            "device_name": device.device_name,
            "token": token_to_return,
            "rejection_reason": device.rejection_reason,
            "message": f"Device is currently {device.status.lower()}.",
        }

    # Create new PENDING request
    device = LANDevice(
        device_name=payload.device_name,
        device_identifier=payload.device_identifier,
        current_ip=client_ip,
        user_agent=user_agent,
        status="PENDING",
        is_server_host=False,
    )
    db.add(device)

    # Log request audit event
    log_entry = LANAccessLog(
        device_id=device.id,
        device_identifier=device.device_identifier,
        ip_address=client_ip,
        user_agent=user_agent,
        endpoint=request.url.path,
        method=request.method,
        action="DEVICE_REQUESTED",
        status="PENDING",
        details=f"New LAN device registration requested: {payload.device_name}",
        timestamp=datetime.now(timezone.utc),
    )
    db.add(log_entry)

    await db.commit()
    await db.refresh(device)

    return {
        "status": "PENDING",
        "is_approved": False,
        "is_server_host": False,
        "device_id": str(device.device_identifier),
        "device_name": device.device_name,
        "token": None,
        "message": "Access request submitted. Awaiting administrator approval.",
    }


@router.get("/devices/check", response_model=LANDeviceCheckResponse, summary="Poll / Check Device Authorization Status")
async def check_device_status(
    request: Request,
    x_device_id: Optional[str] = Header(None, alias="X-Device-ID"),
    device_id: Optional[str] = Query(None),
    x_client_type: Optional[str] = Header(None, alias="X-Client-Type"),
    db: AsyncSession = Depends(get_db),
):
    """
    Called by clients (especially during pending state) to check authorization status.
    If the device was just approved by the admin, returns the one-time issued token.
    """
    identifier = x_device_id or device_id
    client_ip = extract_client_ip(request)
    is_remote = (
        x_client_type == "remote-lan"
        or request.headers.get("x-client-type") == "remote-lan"
        or (identifier and identifier.startswith("dev_"))
    )

    # 1. If an identifier is provided, ALWAYS verify against the registered devices in database!
    if identifier:
        stmt = select(LANDevice).where(LANDevice.device_identifier == identifier)
        res = await db.execute(stmt)
        device = res.scalars().first()

        if not device:
            return LANDeviceCheckResponse(
                device_id=identifier,
                device_name="Unknown Device",
                status="NOT_REGISTERED",
                is_approved=False,
                is_server_host=False,
            )

        # If device is approved and has a pending claim token, yield it and wipe plain token
        issued_token = None
        if device.status == "APPROVED" and device.pending_claim_token:
            issued_token = device.pending_claim_token
            device.pending_claim_token = None
            device.current_ip = client_ip
            device.last_seen_at = datetime.now(timezone.utc)
            await db.commit()

        return LANDeviceCheckResponse(
            device_id=str(device.device_identifier),
            device_name=device.device_name,
            status=device.status,
            is_approved=(device.status == "APPROVED"),
            is_server_host=device.is_server_host,
            token=issued_token,
            rejection_reason=device.rejection_reason,
        )

    # 2. If NO identifier was provided, local host can be auto-approved
    if settings.lan_auto_approve_local and is_loopback(client_ip) and not is_remote:
        return LANDeviceCheckResponse(
            device_id="local-server-host",
            device_name="Host Laptop (Local Server)",
            status="APPROVED",
            is_approved=True,
            is_server_host=True,
        )

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Missing device identifier in header or query parameter.",
    )


# ─────────────────────────────────────────────────────────
# Administrator Endpoints (Protected by require_admin_user)
# ─────────────────────────────────────────────────────────

@router.get("/devices", response_model=List[LANDeviceResponse], summary="List All Registered LAN Devices")
async def list_all_devices(
    db: AsyncSession = Depends(get_db),
    admin: dict = Depends(require_admin_user),
):
    """Lists all registered LAN devices (Pending, Approved, Rejected, Revoked)."""
    stmt = select(LANDevice).order_by(desc(LANDevice.last_seen_at))
    res = await db.execute(stmt)
    devices = res.scalars().all()

    return [
        LANDeviceResponse(
            id=str(d.id),
            device_name=d.device_name,
            device_identifier=d.device_identifier,
            current_ip=d.current_ip,
            user_agent=d.user_agent,
            status=d.status,
            is_server_host=d.is_server_host,
            created_at=d.created_at.isoformat(),
            last_seen_at=d.last_seen_at.isoformat(),
            approved_at=d.approved_at.isoformat() if d.approved_at else None,
            revoked_at=d.revoked_at.isoformat() if d.revoked_at else None,
            created_by=d.created_by,
            rejection_reason=d.rejection_reason,
        )
        for d in devices
    ]


@router.get("/devices/pending", response_model=List[LANDeviceResponse], summary="List Pending LAN Approval Requests")
async def list_pending_devices(
    db: AsyncSession = Depends(get_db),
    admin: dict = Depends(require_admin_user),
):
    """Lists only devices awaiting administrator approval."""
    stmt = select(LANDevice).where(LANDevice.status == "PENDING").order_by(desc(LANDevice.created_at))
    res = await db.execute(stmt)
    devices = res.scalars().all()

    return [
        LANDeviceResponse(
            id=str(d.id),
            device_name=d.device_name,
            device_identifier=d.device_identifier,
            current_ip=d.current_ip,
            user_agent=d.user_agent,
            status=d.status,
            is_server_host=d.is_server_host,
            created_at=d.created_at.isoformat(),
            last_seen_at=d.last_seen_at.isoformat(),
            approved_at=None,
            revoked_at=None,
            created_by=d.created_by,
            rejection_reason=None,
        )
        for d in devices
    ]


@router.post("/devices/{device_id}/approve", summary="Approve LAN Device Access")
async def approve_device(
    device_id: str,
    db: AsyncSession = Depends(get_db),
    admin: dict = Depends(require_admin_user),
):
    """
    Approves a pending or revoked device, generates a cryptographic token, and stores
    its SHA-256 hash. The token will be transferred to the device upon next poll or displayed to admin.
    """
    # Accept either UUID primary key or device_identifier
    stmt = select(LANDevice).where(
        (LANDevice.device_identifier == device_id) | (LANDevice.id == uuid.UUID(device_id) if len(device_id) == 36 else False)
    )
    res = await db.execute(stmt)
    device = res.scalars().first()

    if not device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found.")

    raw_token, token_hash = generate_device_token()

    device.status = "APPROVED"
    device.token_hash = token_hash
    device.pending_claim_token = raw_token
    device.approved_at = datetime.now(timezone.utc)
    device.revoked_at = None
    device.rejection_reason = None
    device.created_by = admin.get("email") or "administrator"

    # Audit log
    log_entry = LANAccessLog(
        device_id=device.id,
        device_identifier=device.device_identifier,
        ip_address=device.current_ip,
        user_agent=device.user_agent,
        endpoint=f"/api/v1/lan/devices/{device_id}/approve",
        method="POST",
        action="DEVICE_APPROVED",
        status="SUCCESS",
        details=f"Device '{device.device_name}' approved by {admin.get('email', 'admin')}",
        timestamp=datetime.now(timezone.utc),
    )
    db.add(log_entry)

    await db.commit()
    await db.refresh(device)

    logger.info("LAN device approved by administrator", device_id=device.device_identifier, name=device.device_name)

    return {
        "success": True,
        "status": "APPROVED",
        "device_id": str(device.device_identifier),
        "device_name": device.device_name,
        "token": raw_token,
        "message": "Device successfully approved. Device token issued.",
    }


@router.post("/devices/{device_id}/reject", summary="Reject Pending LAN Device Access")
async def reject_device(
    device_id: str,
    payload: Optional[LANDeviceRejectRequest] = None,
    db: AsyncSession = Depends(get_db),
    admin: dict = Depends(require_admin_user),
):
    """Rejects a device access request with an optional reason."""
    stmt = select(LANDevice).where(
        (LANDevice.device_identifier == device_id) | (LANDevice.id == uuid.UUID(device_id) if len(device_id) == 36 else False)
    )
    res = await db.execute(stmt)
    device = res.scalars().first()

    if not device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found.")

    reason = payload.reason if payload and payload.reason else "Access rejected by administrator"

    device.status = "REJECTED"
    device.rejection_reason = reason
    device.token_hash = None
    device.pending_claim_token = None

    log_entry = LANAccessLog(
        device_id=device.id,
        device_identifier=device.device_identifier,
        ip_address=device.current_ip,
        user_agent=device.user_agent,
        endpoint=f"/api/v1/lan/devices/{device_id}/reject",
        method="POST",
        action="DEVICE_REJECTED",
        status="BLOCKED",
        details=f"Device '{device.device_name}' rejected by {admin.get('email', 'admin')}: {reason}",
        timestamp=datetime.now(timezone.utc),
    )
    db.add(log_entry)

    await db.commit()

    return {
        "success": True,
        "status": "REJECTED",
        "device_id": str(device.device_identifier),
        "device_name": device.device_name,
        "reason": reason,
    }


@router.post("/devices/{device_id}/revoke", summary="Revoke Approved LAN Device Access")
async def revoke_device(
    device_id: str,
    db: AsyncSession = Depends(get_db),
    admin: dict = Depends(require_admin_user),
):
    """Immediately invalidates a device's access credentials and blocks future requests."""
    stmt = select(LANDevice).where(
        (LANDevice.device_identifier == device_id) | (LANDevice.id == uuid.UUID(device_id) if len(device_id) == 36 else False)
    )
    res = await db.execute(stmt)
    device = res.scalars().first()

    if not device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found.")

    # Guard against revoking the host server laptop
    if device.is_server_host:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot revoke local server host device.",
        )

    device.status = "REVOKED"
    device.revoked_at = datetime.now(timezone.utc)
    device.token_hash = None
    device.pending_claim_token = None
    device.rejection_reason = f"Access revoked by {admin.get('email', 'admin')}"

    log_entry = LANAccessLog(
        device_id=device.id,
        device_identifier=device.device_identifier,
        ip_address=device.current_ip,
        user_agent=device.user_agent,
        endpoint=f"/api/v1/lan/devices/{device_id}/revoke",
        method="POST",
        action="DEVICE_REVOKED",
        status="BLOCKED",
        details=f"Access for '{device.device_name}' revoked by {admin.get('email', 'admin')}",
        timestamp=datetime.now(timezone.utc),
    )
    db.add(log_entry)

    await db.commit()

    return {
        "success": True,
        "status": "REVOKED",
        "device_id": str(device.device_identifier),
        "device_name": device.device_name,
        "message": "Device access revoked successfully.",
    }


@router.patch("/devices/{device_id}", summary="Update LAN Device Information")
async def update_device(
    device_id: str,
    payload: LANDeviceUpdateRequest,
    db: AsyncSession = Depends(get_db),
    admin: dict = Depends(require_admin_user),
):
    """Updates device metadata (friendly name)."""
    stmt = select(LANDevice).where(
        (LANDevice.device_identifier == device_id) | (LANDevice.id == uuid.UUID(device_id) if len(device_id) == 36 else False)
    )
    res = await db.execute(stmt)
    device = res.scalars().first()

    if not device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found.")

    if payload.device_name:
        device.device_name = payload.device_name

    await db.commit()
    await db.refresh(device)

    return {
        "success": True,
        "device_id": str(device.device_identifier),
        "device_name": device.device_name,
    }


@router.delete("/devices/{device_id}", summary="Delete LAN Device Record")
async def delete_device(
    device_id: str,
    db: AsyncSession = Depends(get_db),
    admin: dict = Depends(require_admin_user),
):
    """Permanently removes a device record and its access history."""
    stmt = select(LANDevice).where(
        (LANDevice.device_identifier == device_id) | (LANDevice.id == uuid.UUID(device_id) if len(device_id) == 36 else False)
    )
    res = await db.execute(stmt)
    device = res.scalars().first()

    if not device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found.")

    if device.is_server_host:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete local server host device.",
        )

    # Delete access logs for this device
    await db.execute(
        delete(LANAccessLog).where(
            (LANAccessLog.device_id == device.id) | (LANAccessLog.device_identifier == device.device_identifier)
        )
    )
    await db.delete(device)
    await db.commit()

    return {
        "success": True,
        "message": f"Device '{device.device_name}' removed permanently.",
    }


@router.get("/access-logs", response_model=List[LANAccessLogResponse], summary="Query LAN Access & Security Logs")
async def get_lan_access_logs(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    action: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    db: AsyncSession = Depends(get_db),
    admin: dict = Depends(require_admin_user),
):
    """Returns recent security audit logs for device connections and authorization attempts."""
    stmt = select(LANAccessLog)
    if action:
        stmt = stmt.where(LANAccessLog.action == action)
    if status_filter:
        stmt = stmt.where(LANAccessLog.status == status_filter)

    stmt = stmt.order_by(desc(LANAccessLog.timestamp)).offset(offset).limit(limit)
    res = await db.execute(stmt)
    logs = res.scalars().all()

    return [
        LANAccessLogResponse(
            id=str(log.id),
            device_id=str(log.device_id) if log.device_id else None,
            device_identifier=log.device_identifier,
            ip_address=log.ip_address,
            user_agent=log.user_agent,
            endpoint=log.endpoint,
            method=log.method,
            action=log.action,
            status=log.status,
            details=log.details,
            timestamp=log.timestamp.isoformat(),
        )
        for log in logs
    ]
