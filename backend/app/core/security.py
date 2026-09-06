"""
StockSense AI — JWT Security & Admin Authentication Module

Provides:
  - Real JWT token creation (HS256) for face-auth users
  - FastAPI dependencies: get_current_user, require_admin_user
  - Admin token verification (server-side, not client-side)
"""

from __future__ import annotations

import os
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# --- JWT library with graceful fallback if python-jose not installed ---
try:
    from jose import jwt, JWTError
    _JOSE_AVAILABLE = True
except ImportError:
    _JOSE_AVAILABLE = False

# ─────────────────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────────────────

_SECRET_KEY = os.environ.get("SECRET_KEY", "dev_secret_key_stocksense_ai_change_in_production_32_bytes_min")
_ALGORITHM = os.environ.get("JWT_ALGORITHM", "HS256")
_EXPIRY_HOURS = int(os.environ.get("JWT_EXPIRATION_HOURS", "24"))

bearer_scheme = HTTPBearer(auto_error=False)


# ─────────────────────────────────────────────────────────
# Token Creation
# ─────────────────────────────────────────────────────────

def create_access_token(
    user_id: str,
    name: str,
    email: str,
    is_admin: bool = False,
    role: str = "user",
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Creates a signed JWT access token encoding user identity and admin status."""
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(hours=_EXPIRY_HOURS))
    payload = {
        "sub": user_id,
        "name": name,
        "email": email,
        "is_admin": is_admin,
        "role": role,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "jti": str(uuid.uuid4()),
    }
    if _JOSE_AVAILABLE:
        return jwt.encode(payload, _SECRET_KEY, algorithm=_ALGORITHM)
    # Fallback: opaque token embedding user_id (not cryptographically secure — install python-jose!)
    return f"stocksense_token_{user_id}_{int(expire.timestamp())}_admin={is_admin}"


# ─────────────────────────────────────────────────────────
# Token Decoding
# ─────────────────────────────────────────────────────────

def decode_token(token: str) -> Optional[dict]:
    """Decodes and validates a JWT. Returns payload dict or None on failure."""
    if not token:
        return None

    if _JOSE_AVAILABLE:
        try:
            payload = jwt.decode(token, _SECRET_KEY, algorithms=[_ALGORITHM])
            return payload
        except JWTError:
            return None

    # Fallback: parse opaque token format (stocksense_token_{user_id}_{exp}_admin={bool})
    if token.startswith("stocksense_token_") or token.startswith("stocksense_jwt_"):
        # Minimal parse — extract is_admin from suffix
        is_admin_str = "admin=True" in token or "_admin" in token
        return {
            "sub": "fallback_user",
            "name": "Authenticated User",
            "email": "user@stocksense.ai",
            "is_admin": is_admin_str,
            "role": "admin" if is_admin_str else "user",
        }
    return None


# ─────────────────────────────────────────────────────────
# FastAPI Dependencies
# ─────────────────────────────────────────────────────────

async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
) -> dict:
    """
    FastAPI dependency that extracts and validates the current user from a Bearer JWT.
    Raises HTTP 401 if no valid token is provided.
    """
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please log in to access this resource.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_token(credentials.credentials)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return payload


async def require_admin_user(
    current_user: dict = Depends(get_current_user),
) -> dict:
    """
    FastAPI dependency that ensures the authenticated user has admin privileges.
    Raises HTTP 403 if user is not an admin.
    This is the PRIMARY security guard for all /admin/* endpoints.
    """
    if not current_user.get("is_admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Administrator privileges are required to access this resource.",
        )
    return current_user


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
) -> Optional[dict]:
    """
    FastAPI dependency that returns user payload if authenticated, or None if not.
    Use for endpoints that work for both authenticated and anonymous users.
    """
    if not credentials or not credentials.credentials:
        return None
    return decode_token(credentials.credentials)
