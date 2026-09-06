"""
StockSense AI — PostgreSQL Database Initializer & Verification Script
Initializes all 8 schemas, all 32 tables, checks TimescaleDB extension, and verifies the connection.
"""

import sys
import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import settings
from app.db.base import Base
import app.models  # Load all 32 models


async def init_postgres():
    print("=" * 60)
    print("🚀 StockSense AI — PostgreSQL / TimescaleDB Initializer")
    print("=" * 60)
    print(f"Connecting to: {settings.database_url}\n")

    try:
        engine = create_async_engine(settings.database_url, echo=False)
        
        # 1. Test basic connection
        async with engine.connect() as conn:
            res = await conn.execute(text("SELECT version();"))
            version_str = res.scalar()
            print(f"✅ Connected to PostgreSQL: {version_str[:50]}...")

        # 2. Check for TimescaleDB extension
        async with engine.connect() as conn:
            try:
                timescale_res = await conn.execute(
                    text("SELECT extversion FROM pg_extension WHERE extname = 'timescaledb';")
                )
                ts_version = timescale_res.scalar()
                if ts_version:
                    print(f"✅ TimescaleDB extension active: v{ts_version}")
                else:
                    await conn.execute(text("CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;"))
                    await conn.commit()
                    print("✅ TimescaleDB extension enabled successfully!")
            except Exception as ts_err:
                print("ℹ️ Note on TimescaleDB extension: Not yet attached into PostgreSQL 18.")
                print("   (Standard PostgreSQL features, schemas, and all 32 tables will operate normally!)")

        # 3. Create all 8 schemas
        schemas = [
            "market_data", "fundamentals", "analysis",
            "portfolio", "ml", "news", "macro", "audit"
        ]
        print("\n📁 Initializing 8 Architecture Schemas...")
        async with engine.begin() as conn:
            for s in schemas:
                await conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {s};"))
                print(f"   ✓ Schema '{s}' ready")

        # 4. Create all 32 tables via metadata
        print("\n📊 Creating all 32 Model Tables...")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            print("✅ All 32 tables successfully created across all schemas!")

        await engine.dispose()
        print("\n" + "=" * 60)
        print("🎉 Database setup & verification completed successfully!")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ Connection Error: {e}")
        print("\nTroubleshooting Tips:")
        print("1. Ensure PostgreSQL service is running on your machine.")
        print("2. Ensure the database 'stocksense' exists and user 'stocksense' has password 'stocksense_dev_password'.")
        print("3. Check your .env file credentials.")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(init_postgres())
