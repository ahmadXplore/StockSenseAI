"""
StockSense AI — FastAPI Main Application Entry Point
"""

import time
import uuid
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.logging import setup_logging, get_logger
from app.api.v1.router import api_router
from app.db.base import Base
from app.db.session import async_engine
from sqlalchemy import text

# Initialize structured logging
setup_logging()
logger = get_logger("app.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown hooks."""
    logger.info("Starting StockSense AI Backend", env=settings.app_env, version="1.0.0")
    
    # Verify database connection on boot & create schemas if missing
    try:
        async with async_engine.begin() as conn:
            # PostgreSQL specific schema creation
            if "sqlite" not in settings.database_url.lower():
                schemas = [
                    "market_data", "fundamentals", "analysis",
                    "portfolio", "ml", "news", "macro", "audit"
                ]
                for s in schemas:
                    await conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {s};"))
            # Auto-create tables in development mode
            if settings.is_development:
                # Strip schema for SQLite compatibility
                if "sqlite" in settings.database_url.lower():
                    for table in Base.metadata.tables.values():
                        table.schema = None
                await conn.run_sync(Base.metadata.create_all)
            
            # Ensure new columns on portfolio.users exist (idempotent ALTER TABLE)
            if "sqlite" not in settings.database_url.lower():
                await conn.execute(text("ALTER TABLE portfolio.users ADD COLUMN IF NOT EXISTS full_name VARCHAR(150);"))
                await conn.execute(text("ALTER TABLE portfolio.users ADD COLUMN IF NOT EXISTS face_descriptor JSONB;"))
                await conn.execute(text("ALTER TABLE portfolio.users ADD COLUMN IF NOT EXISTS face_enrolled_at TIMESTAMPTZ;"))
                await conn.execute(text("ALTER TABLE portfolio.users ADD COLUMN IF NOT EXISTS is_admin BOOLEAN DEFAULT FALSE;"))
                await conn.execute(text("ALTER TABLE portfolio.users ADD COLUMN IF NOT EXISTS role VARCHAR(20) DEFAULT 'user';"))

                # Drop FK constraints on ticker columns so users can add any ticker freely
                # without requiring it to exist in market_data.companies first.
                try:
                    await conn.execute(text(
                        "ALTER TABLE portfolio.watchlist_items DROP CONSTRAINT IF EXISTS watchlist_items_ticker_fkey;"
                    ))
                except Exception:
                    pass
                try:
                    await conn.execute(text(
                        "ALTER TABLE portfolio.positions DROP CONSTRAINT IF EXISTS positions_ticker_fkey;"
                    ))
                except Exception:
                    pass

            logger.info("Database schemas and tables initialized successfully")
    except Exception as e:
        logger.error("Database initialization failed", error=str(e))

    yield

    logger.info("Shutting down StockSense AI Backend")
    await async_engine.dispose()


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="Production-grade AI Stock Prediction & Investment Analysis API",
    openapi_url="/api/v1/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_request_id_and_timing(request: Request, call_next):
    """Attach unique X-Request-ID and track request latency."""
    request_id = request.headers.get("X-Request-ID", f"req_{uuid.uuid4().hex[:12]}")
    start_time = time.time()
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time"] = f"{process_time:.4f}"
    
    return response


# Mount API v1 router
app.include_router(api_router, prefix="/api/v1")


@app.get("/health", tags=["Health"])
async def root_health():
    """Root health endpoint for container orchestration checks."""
    return {
        "status": "healthy",
        "app": settings.app_name,
        "environment": settings.app_env,
    }
