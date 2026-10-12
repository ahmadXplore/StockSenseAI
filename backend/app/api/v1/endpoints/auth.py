"""
StockSense AI — Authentication Endpoints
Supports face biometric and PIN-based authentication.
"""

import hashlib
import math
import uuid
from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_

from app.db.session import get_db
from app.models.portfolio import User
from app.schemas.auth import (
    FaceSignupRequest, FaceLoginRequest, FaceUserResponse, FaceAuthResponse,
    PinLoginRequest, LanSignupRequest
)
from app.core.logging import get_logger
from app.core.security import create_access_token

logger = get_logger("api.auth")
router = APIRouter()


def euclidean_distance(v1: List[float], v2: List[float]) -> float:
    """Computes Euclidean distance between two 128-dimensional face embedding vectors."""
    if len(v1) != len(v2):
        raise ValueError("Descriptor vector dimensions must match")
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(v1, v2)))


def calculate_confidence(distance: float, threshold: float = 0.52) -> float:
    """Converts Euclidean distance into a 0-100% confidence rating."""
    if distance >= threshold:
        return 0.0
    # Normalized score: distance 0.0 -> 100%, distance at threshold -> 50%
    score = (1.0 - (distance / (threshold * 1.5))) * 100.0
    return round(max(50.0, min(99.9, score)), 1)


@router.post("/face-signup", response_model=FaceAuthResponse, summary="Register or update biometric face profile in database")
async def face_signup(
    payload: FaceSignupRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Stores a 128-dimensional facial embedding vector in the PostgreSQL database for a user.
    """
    clean_name = payload.name.strip()
    clean_email = payload.email.strip().lower() if payload.email else f"{clean_name.lower().replace(' ', '')}@stocksense.ai"
    clean_username = clean_name.lower().replace(' ', '_')

    # Validate descriptor
    if len(payload.descriptor) != 128:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Face descriptor must be exactly 128 floating-point values."
        )

    # Check if user already exists by email or name
    stmt = select(User).where(
        or_(
            func.lower(User.email) == clean_email,
            func.lower(User.full_name) == clean_name.lower(),
            func.lower(User.username) == clean_username
        )
    )
    result = await db.execute(stmt)
    user = result.scalars().first()

    now = datetime.now(timezone.utc)

    grant_admin = False

    if user:
        # Update existing user's face profile
        user.full_name = clean_name
        user.face_descriptor = payload.descriptor
        user.face_enrolled_at = now
        user.updated_at = now
        if grant_admin:
            user.role = "admin"
            user.is_admin = True
        logger.info(f"Updated face biometric enrollment for existing user {clean_name} ({user.id}) (admin={user.is_admin})")
    else:
        # Create new user record with face embedding
        user = User(
            id=uuid.uuid4(),
            email=clean_email,
            username=clean_username,
            full_name=clean_name,
            role="admin" if grant_admin else (payload.role or "user"),
            is_admin=grant_admin,
            face_descriptor=payload.descriptor,
            face_enrolled_at=now,
            email_verified=True,
            created_at=now,
            updated_at=now,
            last_login_at=now,
        )
        db.add(user)
        logger.info(f"Created new face biometric user {clean_name} ({user.id}) (admin={grant_admin})")

    await db.commit()
    await db.refresh(user)

    user_resp = FaceUserResponse(
        id=str(user.id),
        name=user.full_name or user.username or "StockSense User",
        email=user.email,
        username=user.username,
        role=getattr(user, "role", "user") or "user",
        is_active=user.is_active,
        is_admin=getattr(user, "is_admin", False) or False,
        face_enrolled_at=user.face_enrolled_at,
        last_login_at=user.last_login_at,
        created_at=user.created_at,
    )

    # Issue a real signed JWT with admin claim embedded
    jwt_token = create_access_token(
        user_id=str(user.id),
        name=user_resp.name,
        email=user_resp.email,
        is_admin=user_resp.is_admin,
        role=user_resp.role,
    )

    return FaceAuthResponse(
        success=True,
        message=f"Biometric face profile registered successfully for {clean_name}.",
        token=jwt_token,
        confidence_pct=100.0,
        user=user_resp,
    )


@router.post("/face-login", response_model=FaceAuthResponse, summary="Authenticate face against database records")
async def face_login(
    payload: FaceLoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Authenticates a live facial scan against the database:
    - 1:1 Verification if identifier (name/email) is provided.
    - 1:N Identification if identifier is omitted.
    """
    if len(payload.descriptor) != 128:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Captured face descriptor must be exactly 128 floating-point values."
        )

    threshold = payload.threshold or 0.52

    # Query all users with an active face descriptor
    stmt = select(User).where(User.face_descriptor.is_not(None))
    
    if payload.identifier and payload.identifier.strip():
        ident = payload.identifier.strip().lower()
        stmt = stmt.where(
            or_(
                func.lower(User.email) == ident,
                func.lower(User.full_name) == ident,
                func.lower(User.username) == ident
            )
        )

    result = await db.execute(stmt)
    users = result.scalars().all()

    if not users:
        detail_msg = f"No biometric enrollment found for '{payload.identifier}'." if payload.identifier else "No registered face profiles found in database. Please sign up first."
        return FaceAuthResponse(
            success=False,
            message=detail_msg,
            distance=None,
            confidence_pct=0.0,
            user=None,
        )

    best_match_user: Optional[User] = None
    min_distance = 999.0

    for u in users:
        if not u.face_descriptor or not isinstance(u.face_descriptor, list):
            continue
        try:
            dist = euclidean_distance(payload.descriptor, u.face_descriptor)
            if dist < min_distance:
                min_distance = dist
                best_match_user = u
        except Exception as e:
            logger.warning(f"Failed to compute distance for user {u.id}: {e}")

    if not best_match_user or min_distance > threshold:
        return FaceAuthResponse(
            success=False,
            message=f"Biometric verification failed. Face does not match registered profile (distance: {min_distance:.3f}, required: < {threshold:.2f}).",
            distance=round(min_distance, 4) if min_distance < 900 else None,
            confidence_pct=0.0,
            user=None,
        )

    # Check if user is blocked
    if not best_match_user.is_active:
        return FaceAuthResponse(
            success=False,
            message="Account is blocked by administrator. Please contact system admin.",
            distance=round(min_distance, 4),
            confidence_pct=0.0,
            user=None,
        )

    # Success: update last login timestamp
    now = datetime.now(timezone.utc)
    best_match_user.last_login_at = now
    await db.commit()
    await db.refresh(best_match_user)

    confidence = calculate_confidence(min_distance, threshold)
    user_name = best_match_user.full_name or best_match_user.username or "Investor"

    logger.info(f"Successful face authentication for {user_name} (distance={min_distance:.4f}, confidence={confidence}%)")

    user_resp = FaceUserResponse(
        id=str(best_match_user.id),
        name=user_name,
        email=best_match_user.email,
        username=best_match_user.username,
        role=getattr(best_match_user, "role", "user") or "user",
        is_active=best_match_user.is_active,
        is_admin=getattr(best_match_user, "is_admin", False) or False,
        face_enrolled_at=best_match_user.face_enrolled_at,
        last_login_at=best_match_user.last_login_at,
        created_at=best_match_user.created_at,
    )

    # Issue a real signed JWT with admin claim embedded
    jwt_token = create_access_token(
        user_id=str(best_match_user.id),
        name=user_resp.name,
        email=user_resp.email,
        is_admin=user_resp.is_admin,
        role=user_resp.role,
    )

    return FaceAuthResponse(
        success=True,
        message=f"Access Granted. Identity verified for {user_name}.",
        token=jwt_token,
        distance=round(min_distance, 4),
        confidence_pct=confidence,
        user=user_resp,
    )


@router.get("/face-users", response_model=List[FaceUserResponse], summary="List all enrolled biometric face users from database")
async def list_face_users(db: AsyncSession = Depends(get_db)):
    """
    Returns all registered users with biometric face data stored in the database.
    """
    stmt = select(User).where(User.face_descriptor.is_not(None)).order_by(User.face_enrolled_at.desc())
    result = await db.execute(stmt)
    users = result.scalars().all()

    return [
        FaceUserResponse(
            id=str(u.id),
            name=u.full_name or u.username or "User",
            email=u.email,
            username=u.username,
            role=getattr(u, "role", "user") or "user",
            is_active=u.is_active,
            is_admin=getattr(u, "is_admin", False) or False,
            face_enrolled_at=u.face_enrolled_at,
            last_login_at=u.last_login_at,
            created_at=u.created_at,
        )
        for u in users
    ]


@router.delete("/face-users/{user_id}", summary="Delete biometric profile for a user")
async def delete_face_user(user_id: str, db: AsyncSession = Depends(get_db)):
    """
    Removes face descriptor enrollment for a specific user ID.
    """
    try:
        uid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID format.")

    stmt = select(User).where(User.id == uid)
    result = await db.execute(stmt)
    user = result.scalars().first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    user.face_descriptor = None
    user.face_enrolled_at = None
    await db.commit()

    return {"success": True, "message": f"Biometric enrollment removed for {user.full_name or user.email}."}


def _hash_pin(pin: str) -> str:
    """SHA-256 hash of a PIN string for storage in password_hash."""
    return hashlib.sha256(pin.strip().encode("utf-8")).hexdigest()


def _verify_pin(raw_pin: str, stored_hash: str) -> bool:
    """Compare a raw PIN against a stored SHA-256 hash."""
    return _hash_pin(raw_pin) == stored_hash


@router.post("/pin-login", response_model=FaceAuthResponse, summary="PIN Login — works on all devices")
async def pin_login(
    payload: PinLoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Authenticates any user (local or LAN) via PIN verified against stored hash in password_hash.
    """
    ident = payload.identifier.strip().lower()
    pin_val = (payload.pin or "").strip()

    # Locate user by UUID, email, full_name, or username
    user_id_obj = None
    try:
        user_id_obj = uuid.UUID(ident)
    except Exception:
        pass

    stmt = select(User)
    if user_id_obj:
        stmt = stmt.where(User.id == user_id_obj)
    else:
        stmt = stmt.where(
            or_(
                func.lower(User.email) == ident,
                func.lower(User.full_name) == ident,
                func.lower(User.username) == ident,
            )
        )

    result = await db.execute(stmt)
    user = result.scalars().first()

    if not user:
        return FaceAuthResponse(
            success=False,
            message=f"No account found for '{payload.identifier}'. Please sign up first.",
            user=None,
        )

    if not user.is_active:
        return FaceAuthResponse(
            success=False,
            message="Account is disabled by administrator.",
            user=None,
        )

    if not pin_val:
        return FaceAuthResponse(
            success=False,
            message="PIN is required to log in.",
            user=None,
        )

    # PIN verification: check stored hash first, then master admin pins as fallback
    pin_ok = False
    stored_hash = getattr(user, "password_hash", None)
    if stored_hash and stored_hash.startswith("pin:"):
        # Format: "pin:<sha256hex>"
        pin_ok = _verify_pin(pin_val, stored_hash[4:])
    

    if not pin_ok:
        return FaceAuthResponse(
            success=False,
            message="Incorrect PIN. Please try again.",
            user=None,
        )

    # Success — update last login
    now = datetime.now(timezone.utc)
    user.last_login_at = now
    await db.commit()
    await db.refresh(user)

    user_resp = FaceUserResponse(
        id=str(user.id),
        name=user.full_name or user.username or "StockSense User",
        email=user.email,
        username=user.username,
        role=getattr(user, "role", "user") or "user",
        is_active=user.is_active,
        is_admin=getattr(user, "is_admin", False) or False,
        face_enrolled_at=user.face_enrolled_at,
        last_login_at=user.last_login_at,
        created_at=user.created_at,
    )

    jwt_token = create_access_token(
        user_id=str(user.id),
        name=user_resp.name,
        email=user_resp.email,
        is_admin=user_resp.is_admin,
        role=user_resp.role,
    )

    return FaceAuthResponse(
        success=True,
        message=f"Access Granted. Welcome back, {user_resp.name}.",
        token=jwt_token,
        confidence_pct=100.0,
        user=user_resp,
    )


@router.post("/lan-signup", response_model=FaceAuthResponse, summary="PIN Account Signup — works on all devices")
async def lan_signup(
    payload: LanSignupRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Registers a new user account with a PIN. No camera required.
    PIN is stored as a SHA-256 hash in password_hash (prefixed with 'pin:').
    """
    clean_name = payload.name.strip()
    clean_email = payload.email.strip().lower() if payload.email else f"{clean_name.lower().replace(' ', '_')}@stocksense.local"
    clean_username = clean_name.lower().replace(' ', '_')

    # Require a PIN for signup
    user_pin = (payload.pin or "").strip()
    if not user_pin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A PIN is required to create an account."
        )
    if len(user_pin) < 4:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="PIN must be at least 4 characters."
        )

    pin_hash_stored = f"pin:{_hash_pin(user_pin)}"

    # New signups cannot self-grant admin privileges
    grant_admin = False

    # Check if user already exists
    stmt = select(User).where(
        or_(
            func.lower(User.email) == clean_email,
            func.lower(User.full_name) == clean_name.lower(),
            func.lower(User.username) == clean_username,
        )
    )
    result = await db.execute(stmt)
    user = result.scalars().first()

    now = datetime.now(timezone.utc)
    if user:
        # Update existing user — refresh PIN
        user.full_name = clean_name
        user.password_hash = pin_hash_stored
        user.updated_at = now
        if grant_admin:
            user.role = "admin"
            user.is_admin = True
        logger.info(f"Updated PIN for existing user: {clean_name}")
    else:
        # Create new user with PIN
        user = User(
            id=uuid.uuid4(),
            email=clean_email,
            username=clean_username,
            full_name=clean_name,
            role="user",
            is_admin=False,
            password_hash=pin_hash_stored,
            email_verified=True,
            created_at=now,
            updated_at=now,
            last_login_at=now,
        )
        db.add(user)
        logger.info(f"Created new PIN user: {clean_name}")

    await db.commit()
    await db.refresh(user)

    user_resp = FaceUserResponse(
        id=str(user.id),
        name=user.full_name or user.username or "StockSense User",
        email=user.email,
        username=user.username,
        role=getattr(user, "role", "user") or "user",
        is_active=user.is_active,
        is_admin=getattr(user, "is_admin", False) or False,
        face_enrolled_at=user.face_enrolled_at,
        last_login_at=user.last_login_at,
        created_at=user.created_at,
    )

    jwt_token = create_access_token(
        user_id=str(user.id),
        name=user_resp.name,
        email=user_resp.email,
        is_admin=user_resp.is_admin,
        role=user_resp.role,
    )

    return FaceAuthResponse(
        success=True,
        message=f"Account created for {clean_name}. You can now log in.",
        token=jwt_token,
        confidence_pct=100.0,
        user=user_resp,
    )
