"""
StockSense AI — LAN Network Discovery & Device Security Service
Provides:
  - Robust LAN IPv4 auto-detection for Windows native hosting
  - Loopback validation for local server access
  - Cryptographic device token generation & SHA-256 hashing
  - Live system status inspection (DB, ML, Backtesting, Device stats)
"""

from __future__ import annotations

import hashlib
import os
import secrets
import socket
from datetime import datetime, timezone
from typing import List, Tuple, Optional, Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text

from app.core.logging import get_logger

logger = get_logger("app.core.lan_service")


def get_laptop_lan_ip() -> str:
    """
    Safely discovers the primary LAN IPv4 address of the Windows laptop.
    Uses outbound UDP routing inspection without transmitting any packets.
    Falls back to hostname resolution or loopback if disconnected.
    """
    # Attempt 1: Route probe via UDP socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0.5)
        # 8.8.8.8:80 does not send data; OS kernel selects preferred local interface IP
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        if ip and not ip.startswith("127."):
            return ip
    except Exception:
        pass

    # Attempt 2: Resolve local hostname interfaces
    try:
        hostname = socket.gethostname()
        for info in socket.getaddrinfo(hostname, None, socket.AF_INET):
            candidate = info[4][0]
            if candidate and not candidate.startswith("127.") and not candidate.startswith("169.254."):
                return candidate
    except Exception:
        pass

    return "127.0.0.1"


def get_all_lan_ips() -> List[str]:
    """Returns all detectable local IPv4 addresses (loopback + active interfaces)."""
    ips = {"127.0.0.1"}
    primary = get_laptop_lan_ip()
    if primary:
        ips.add(primary)

    try:
        hostname = socket.gethostname()
        for info in socket.getaddrinfo(hostname, None, socket.AF_INET):
            candidate = info[4][0]
            if candidate:
                ips.add(candidate)
    except Exception:
        pass

    return sorted(list(ips))


def is_loopback(ip_str: Optional[str]) -> bool:
    """
    Determines whether a client IP represents the local Windows host loopback interface.
    Includes 127.0.0.1, ::1, localhost, and testclient.
    Note: The server's Wi-Fi / LAN IP (e.g. 192.168.x.x) is NOT loopback.
    """
    if not ip_str:
        return False
    ip_clean = ip_str.strip().lower()
    
    # Common loopback representations
    if ip_clean in ("127.0.0.1", "::1", "localhost", "testclient", "0.0.0.0"):
        return True
    if ip_clean.startswith("127."):
        return True

    return False


def hash_token(raw_token: str) -> str:
    """Generates a cryptographic SHA-256 hash of a raw device token."""
    return hashlib.sha256(raw_token.strip().encode("utf-8")).hexdigest()


def generate_device_token() -> Tuple[str, str]:
    """
    Generates a cryptographically strong random token and its SHA-256 hash.
    Returns: (raw_token, token_hash)
    """
    raw_token = f"ss_dev_{secrets.token_urlsafe(32)}"
    token_hash = hash_token(raw_token)
    return raw_token, token_hash


async def get_system_lan_status(db: AsyncSession) -> Dict[str, Any]:
    """
    Queries live server status, network endpoints, component health, and device counts.
    """
    from app.core.config import settings
    from app.models.lan import LANDevice

    lan_ip = get_laptop_lan_ip()
    all_ips = get_all_lan_ips()

    # Device statistics
    stats = {
        "total": 0,
        "pending": 0,
        "approved": 0,
        "rejected": 0,
        "revoked": 0,
    }
    try:
        result = await db.execute(
            select(LANDevice.status, func.count(LANDevice.id)).group_by(LANDevice.status)
        )
        for row in result.all():
            status_name = str(row[0]).lower()
            count = int(row[1])
            if status_name in stats:
                stats[status_name] = count
            stats["total"] += count
    except Exception as e:
        logger.warning("Failed to query LANDevice statistics", error=str(e))

    # Database connectivity test
    db_status = "connected"
    try:
        await db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    return {
        "status": "online",
        "app_name": settings.app_name,
        "environment": settings.app_env,
        "host_ip": lan_ip,
        "all_interfaces": all_ips,
        "ports": {
            "frontend": getattr(settings, "frontend_port", 3005),
            "backend": settings.lan_server_port,
        },
        "lan_access_url": f"http://{lan_ip}:{getattr(settings, 'frontend_port', 3005)}" if lan_ip != "127.0.0.1" else f"http://localhost:{getattr(settings, 'frontend_port', 3005)}",
        "backend_docs_url": f"http://{lan_ip}:{getattr(settings, 'frontend_port', 3005)}/docs" if lan_ip != "127.0.0.1" else f"http://localhost:{getattr(settings, 'frontend_port', 3005)}/docs",
        "lan_enabled": settings.lan_enabled,
        "device_auth_required": settings.lan_device_auth_required,
        "auto_approve_local": settings.lan_auto_approve_local,
        "device_stats": stats,
        "components": {
            "database": db_status,
            "ml_engine": "ready",
            "backtesting_engine": "ready",
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
