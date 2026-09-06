"""
StockSense AI — Canonical Market Data Ingestion ETL Pipeline
8-Stage Pipeline: Extract -> Load Raw -> Validate -> Normalize -> Transform -> Canonicalize -> Deduplicate -> Quality Check -> DB
"""

from __future__ import annotations
import uuid
import json
from datetime import datetime, timezone, date
from decimal import Decimal
from typing import List, Dict, Optional, Tuple, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.data.canonical.market import MarketDTO, ExchangeDTO, build_security_id
from app.data.canonical.security import SecurityDTO
from app.data.canonical.price import CanonicalPriceDTO, RawMarketRecordDTO
from app.data.canonical.corporate_action import CorporateActionDTO
from app.data.validation.price_validation import validate_price_series
from app.data.validation.data_quality import data_quality_engine, DataQualityResult
from app.models.market_data import (
    Market as MarketModel,
    Exchange as ExchangeModel,
    SecurityMaster as SecurityMasterModel,
    PriceData as PriceDataModel,
    Company as CompanyModel,
    RawMarketData as RawMarketDataModel,
    IngestionJobLog as IngestionJobLogModel,
)
from app.core.logging import get_logger

logger = get_logger("data.ingestion.pipeline")


class IngestionPipeline:
    """
    Executes an end-to-end data ingestion run with provenance tracking and quality auditing.
    """

    async def run(
        self,
        provider_name: str,
        market_code: str,
        exchange_code: str,
        raw_prices: List[CanonicalPriceDTO],
        securities: Optional[List[SecurityDTO]] = None,
        corporate_actions: Optional[List[CorporateActionDTO]] = None,
        job_type: str = "HISTORICAL_BACKFILL",
        raw_payload: Optional[str] = None,
        db: Optional[AsyncSession] = None
    ) -> DataQualityResult:
        start_time = datetime.now(timezone.utc)
        job_id = str(uuid.uuid4())
        logger.info(f"Starting ingestion pipeline job {job_id} for {market_code}/{exchange_code} from {provider_name}")

        # Stage 1 & 2: Load Raw Stage
        if db is not None:
            raw_record = RawMarketDataModel(
                source=f"{market_code}_{exchange_code}",
                provider=provider_name,
                retrieval_timestamp=start_time,
                original_reference=f"pipeline_run_{job_id}",
                checksum=None,
                raw_payload=raw_payload[:5000] if raw_payload else None,
                record_count=len(raw_prices),
                schema_version="1.0",
                ingested=True
            )
            db.add(raw_record)

        # Stage 3, 4, 5, 6, 7: Validate, Normalize, Canonicalize, Deduplicate, Quality Check
        quality_result = data_quality_engine.evaluate(
            provider=provider_name,
            market=market_code,
            exchange=exchange_code,
            prices=raw_prices,
            securities=securities,
            corporate_actions=corporate_actions
        )

        accepted_prices, rejected_prices, logs = validate_price_series(raw_prices)

        # Stage 8: Database Persistence (if db session provided)
        if db is not None:
            # 1. Upsert Securities & Companies
            sec_list = securities or []
            for sec in sec_list:
                # Check if Security exists
                stmt = select(SecurityMasterModel).where(SecurityMasterModel.security_id == sec.security_id)
                res = await db.execute(stmt)
                existing_sec = res.scalars().first()
                if not existing_sec:
                    sec_model = SecurityMasterModel(
                        security_id=sec.security_id,
                        exchange_id=sec.exchange_id,
                        market_id=sec.market_id,
                        symbol=sec.symbol,
                        company_name=sec.company_name,
                        legal_name=sec.legal_name,
                        country=sec.country,
                        currency=sec.currency,
                        sector=sec.sector,
                        industry=sec.industry,
                        security_type=sec.security_type.value if hasattr(sec.security_type, "value") else str(sec.security_type),
                        status=sec.status.value if hasattr(sec.status, "value") else str(sec.status),
                        listing_date=sec.listing_date,
                        delisting_date=sec.delisting_date,
                        delisting_reason=sec.delisting_reason,
                        primary_exchange=sec.primary_exchange,
                        cik=sec.cik,
                        isin=sec.isin,
                        cusip=sec.cusip,
                        provider_security_id=sec.provider_security_id,
                    )
                    db.add(sec_model)

                # Ensure Company model exists for existing foreign keys
                stmt_c = select(CompanyModel).where(CompanyModel.ticker == sec.symbol)
                res_c = await db.execute(stmt_c)
                existing_c = res_c.scalars().first()
                if not existing_c:
                    comp_model = CompanyModel(
                        ticker=sec.symbol,
                        security_id=sec.security_id,
                        name=sec.company_name,
                        exchange=sec.exchange_id,
                        country=sec.country,
                        currency=sec.currency,
                        sector=sec.sector,
                        industry=sec.industry,
                        is_active=(sec.status.value == "ACTIVE" if hasattr(sec.status, "value") else sec.status == "ACTIVE"),
                        is_delisted=(sec.status.value == "DELISTED" if hasattr(sec.status, "value") else sec.status == "DELISTED"),
                        delisted_date=sec.delisting_date,
                        delisted_reason=sec.delisting_reason,
                        data_source=provider_name
                    )
                    db.add(comp_model)

            await db.flush()

            # 2. Persist Accepted Prices
            for p in accepted_prices:
                # Ensure parent Company exists
                stmt_c = select(CompanyModel).where(CompanyModel.ticker == p.ticker)
                res_c = await db.execute(stmt_c)
                if not res_c.scalars().first():
                    dummy_c = CompanyModel(
                        ticker=p.ticker,
                        security_id=p.security_id,
                        name=f"{p.ticker} Corp.",
                        exchange=exchange_code,
                        country="Pakistan" if market_code == "PK" else "USA",
                        currency=p.currency,
                        is_active=True,
                        data_source=provider_name
                    )
                    db.add(dummy_c)
                    await db.flush()

                p_model = PriceDataModel(
                    time=p.timestamp,
                    ticker=p.ticker,
                    security_id=p.security_id,
                    open=p.open,
                    high=p.high,
                    low=p.low,
                    close=p.close,
                    adj_close=p.adj_close,
                    volume=p.volume,
                    vwap=p.vwap,
                    currency=p.currency,
                    split_factor=p.split_factor,
                    dividend_amount=p.dividend_amount,
                    source_id=p.source_id,
                    data_source=p.data_source or provider_name,
                    is_adjusted=p.is_adjusted,
                    quality_flag=p.quality_flag,
                    retrieved_at=p.retrieved_at
                )
                db.add(p_model)

            # 3. Log Ingestion Job Execution
            end_time = datetime.now(timezone.utc)
            job_log = IngestionJobLogModel(
                id=job_id,
                job_type=job_type,
                market_code=market_code,
                exchange_code=exchange_code,
                provider_name=provider_name,
                start_time=start_time,
                end_time=end_time,
                status="SUCCESS" if quality_result.status != "FAILED" else "FAILED",
                records_checked=quality_result.records_checked,
                records_accepted=quality_result.records_accepted,
                records_rejected=quality_result.records_rejected,
                quality_score=Decimal(str(quality_result.quality_score)),
                error_summary="; ".join(quality_result.errors[:5]) if quality_result.errors else None,
                details_json=json.dumps({
                    "date_range": [str(d) for d in quality_result.date_range],
                    "duplicates": quality_result.duplicates_count,
                    "invalid_values": quality_result.invalid_values_count,
                    "extreme_moves": quality_result.extreme_moves_count,
                    "delisted_count": quality_result.delisted_count
                })
            )
            db.add(job_log)
            await db.commit()

        logger.info(
            f"Ingestion pipeline completed job {job_id}: score={quality_result.quality_score} "
            f"accepted={quality_result.records_accepted}/{quality_result.records_checked}"
        )
        return quality_result


ingestion_pipeline = IngestionPipeline()
