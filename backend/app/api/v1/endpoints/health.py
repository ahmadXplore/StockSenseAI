"""
StockSense AI — Health Check Endpoints
"""

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import redis.asyncio as aioredis

from app.core.config import settings
from app.db.session import get_db
from app.schemas.health import HealthResponse, ServiceHealth

router = APIRouter()


@router.get("", response_model=HealthResponse, summary="System health check")
@router.get("/", response_model=HealthResponse, include_in_schema=False)
async def health_check(db: AsyncSession = Depends(get_db)):
    """
    Check availability of the API, PostgreSQL database, and Redis cache.
    """
    db_status = "disconnected"
    redis_status = "disconnected"

    # Test Database
    try:
        result = await db.execute(text("SELECT 1"))
        if result.scalar() == 1:
            db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)[:50]}"

    # Test Redis
    try:
        r = aioredis.from_url(settings.redis_url, socket_timeout=2)
        ping_ok = await r.ping()
        await r.aclose()
        if ping_ok:
            redis_status = "connected"
    except Exception as e:
        redis_status = f"error: {str(e)[:50]}"

    overall_status = "healthy" if db_status == "connected" and redis_status == "connected" else "degraded"

    return HealthResponse(
        status=overall_status,
        timestamp=datetime.utcnow(),
        version="1.0.0",
        database=db_status,
        redis=redis_status,
        environment=settings.app_env,
    )
