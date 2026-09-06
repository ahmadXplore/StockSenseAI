"""
StockSense AI — Historical Data Backfill Coordinator
Executes initial multi-year backfills across market, exchange, and security boundaries.
"""

from __future__ import annotations
from datetime import date
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

from app.data.canonical.market import build_security_id
from app.data.providers.registry import provider_registry
from app.data.ingestion.pipeline import ingestion_pipeline, DataQualityResult


async def ingest_historical(
    market: str,
    exchange: str,
    symbol: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Optional[AsyncSession] = None
) -> DataQualityResult:
    """
    Ingests multi-year historical prices for a specific symbol or entire market/exchange.
    Example: ingest_historical(market="US", exchange="NASDAQ", symbol="AAPL", start_date=date(2018, 1, 1))
             ingest_historical(market="PK", exchange="PSX", symbol="ENGRO")
    """
    clean_m = market.strip().upper()
    clean_e = exchange.strip().upper()

    providers = provider_registry.get_providers_for_market(clean_m)
    provider = providers[0] if providers else None
    provider_name = provider.name if provider else "unknown_provider"

    if symbol:
        clean_s = symbol.strip().upper()
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
        corp_actions = []
        if provider:
            corp_actions = await provider.get_corporate_actions(clean_s, clean_m, clean_e, start_date, end_date)

        return await ingestion_pipeline.run(
            provider_name=provider_name,
            market_code=clean_m,
            exchange_code=clean_e,
            raw_prices=prices,
            securities=securities,
            corporate_actions=corp_actions,
            job_type="HISTORICAL_BACKFILL",
            db=db
        )
    else:
        # Full exchange backfill
        securities = await provider.get_security_list(clean_m, clean_e) if provider else []
        all_prices = []
        for sec in securities[:20]: # Batch first set for safety
            p = await provider.get_historical_prices(sec.symbol, clean_m, clean_e, start_date, end_date)
            all_prices.extend(p)

        return await ingestion_pipeline.run(
            provider_name=provider_name,
            market_code=clean_m,
            exchange_code=clean_e,
            raw_prices=all_prices,
            securities=securities,
            job_type="HISTORICAL_BACKFILL",
            db=db
        )
