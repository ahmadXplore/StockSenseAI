"""
StockSense AI — Incremental Ingestion Manager
Queries latest available canonical timestamp and ingests only missing trading sessions.
"""

from __future__ import annotations
from datetime import date, timedelta
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.market_data import PriceData as PriceDataModel
from app.data.providers.registry import provider_registry
from app.data.ingestion.pipeline import ingestion_pipeline, DataQualityResult


async def ingest_incremental(
    market: str,
    exchange: str,
    symbol: str,
    db: Optional[AsyncSession] = None
) -> DataQualityResult:
    """
    Finds the latest available date for the security in the database and requests only missing data.
    """
    clean_m = market.strip().upper()
    clean_e = exchange.strip().upper()
    clean_s = symbol.strip().upper()

    latest_date: Optional[date] = None

    if db is not None:
        stmt = (
            select(func.max(PriceDataModel.time))
            .where(PriceDataModel.ticker == clean_s)
        )
        res = await db.execute(stmt)
        max_dt = res.scalar()
        if max_dt:
            latest_date = max_dt.date() if hasattr(max_dt, "date") else max_dt

    start_date = (latest_date + timedelta(days=1)) if latest_date else (date.today() - timedelta(days=30))
    end_date = date.today()

    if start_date > end_date:
        # Up to date
        return DataQualityResult(
            provider="incremental_sync",
            market=clean_m,
            exchange=clean_e,
            date_range=(latest_date, latest_date),
            securities_count=1,
            records_checked=0,
            records_accepted=0,
            records_rejected=0,
            duplicates_count=0,
            invalid_values_count=0,
            extreme_moves_count=0,
            delisted_count=0,
            corporate_actions_count=0,
            quality_score=100.0,
            status="PASSED",
            warnings=["Data is already up to date with latest market session."]
        )

    providers = provider_registry.get_providers_for_market(clean_m)
    provider = providers[0] if providers else None
    provider_name = provider.name if provider else "unknown_provider"

    prices = await provider_registry.get_historical_prices(
        symbol=clean_s,
        market_code=clean_m,
        exchange_code=clean_e,
        start_date=start_date,
        end_date=end_date
    )

    sec_metadata = None
    if provider:
        sec_metadata = await provider.get_security_metadata(clean_s, clean_m, clean_e)
    securities = [sec_metadata] if sec_metadata else []

    return await ingestion_pipeline.run(
        provider_name=provider_name,
        market_code=clean_m,
        exchange_code=clean_e,
        raw_prices=prices,
        securities=securities,
        job_type="INCREMENTAL_UPDATE",
        db=db
    )
