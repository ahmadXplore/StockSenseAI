"""
StockSense AI — SQLite Local Database Initializer
Creates stocksense.db with all 32 tables for local testing without Docker/PostgreSQL.
"""

import os
import asyncio
from sqlalchemy import event, Table
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID, INET
from sqlalchemy.ext.asyncio import create_async_engine

# Compile PostgreSQL types for SQLite
@compiles(ARRAY, "sqlite")
def compile_array_sqlite(type_, compiler, **kw):
    return "TEXT"

@compiles(JSONB, "sqlite")
def compile_jsonb_sqlite(type_, compiler, **kw):
    return "TEXT"

@compiles(INET, "sqlite")
def compile_inet_sqlite(type_, compiler, **kw):
    return "TEXT"

@compiles(UUID, "sqlite")
def compile_uuid_sqlite(type_, compiler, **kw):
    return "TEXT"

# Strip schema prefixes for SQLite
@event.listens_for(Table, "before_create")
def remove_schema_for_sqlite(target, connection, **kw):
    if connection.dialect.name == "sqlite":
        target.schema = None


async def init_db():
    from app.db.base import Base
    import app.models # Load all 32 models

    db_path = "stocksense.db"
    if os.path.exists(db_path):
        os.remove(db_path)

    engine = create_async_engine("sqlite+aiosqlite:///./stocksense.db", echo=False)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    print("✅ Successfully created local SQLite database: backend/stocksense.db with all 32 tables!")
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(init_db())
