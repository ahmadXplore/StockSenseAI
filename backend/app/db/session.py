"""
StockSense AI — Database Session Management
Supports both Async (FastAPI request lifecycle) and Sync (Celery / Alembic / Migrations).
"""

from typing import AsyncGenerator
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import sessionmaker, Session

from app.core.config import settings

# Engine configuration (conditional on SQLite vs PostgreSQL)
is_sqlite = "sqlite" in settings.database_url.lower()
async_kwargs = {"echo": False, "future": True}
if not is_sqlite:
    async_kwargs.update({"pool_pre_ping": True, "pool_size": 10, "max_overflow": 20})

# Async Engine for FastAPI async handlers
async_engine = create_async_engine(
    settings.database_url,
    **async_kwargs,
)

# Async Session Factory
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

is_sqlite_sync = "sqlite" in settings.database_url_sync.lower()
sync_kwargs = {"echo": False, "future": True}
if not is_sqlite_sync:
    sync_kwargs.update({"pool_pre_ping": True, "pool_size": 5, "max_overflow": 10})

# Sync Engine for synchronous tasks, Celery workers & migrations
sync_engine = create_engine(
    settings.database_url_sync,
    **sync_kwargs,
)

SyncSessionLocal = sessionmaker(
    bind=sync_engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for obtaining an asynchronous database session in FastAPI routes."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


def get_sync_db() -> Session:
    """Helper for obtaining a synchronous database session in Celery tasks or scripts."""
    session = SyncSessionLocal()
    try:
        return session
    except Exception:
        session.rollback()
        raise
