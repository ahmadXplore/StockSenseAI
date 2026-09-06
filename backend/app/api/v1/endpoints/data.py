"""
StockSense AI — Canonical Multi-Market Data Endpoints
Market-independent REST endpoints for markets, exchanges, security master, OHLCV prices, and ingestion jobs.
"""

import uuid
from typing import List, Optional
from datetime import date, datetime
from fastapi import APIRouter, Depends, Query, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.data.canonical.market import (
    SUPPORTED_MARKETS, SUPPORTED_EXCHANGES, parse_security_id, build_security_id
)
from app.data.canonical.security import SecurityDTO, SecurityStatus, SecurityType
from app.data.canonical.universe import resolve_historical_universe
from app.data.providers.registry import provider_registry
from app.data.ingestion.scheduler import ingestion_scheduler
from app.data.ingestion.historical import ingest_historical
from app.data.ingestion.incremental import ingest_incremental
from app.schemas.data import (
    MarketResponse,
    ExchangeResponse,
    SecurityResponse,
    CanonicalPriceResponse,
    HistoricalUniverseResponse,
    IngestionJobRequest,
    IngestionJobResponse,
    ProviderHealthResponse,
)
from app.models.market_data import IngestionJobLog as IngestionJobLogModel
from app.core.logging import get_logger

logger = get_logger("api.data")
router = APIRouter()


# ─────────────────────────────────────────────────────────
# Markets & Exchanges
# ─────────────────────────────────────────────────────────

@router.get("/markets", response_model=List[MarketResponse], summary="List all supported global markets")
async def list_markets():
    """Returns canonical global market definitions (Pakistan, US, UK, Japan, Hong Kong, India)."""
    return [
        MarketResponse(
            id=m.id,
            code=m.code,
            name=m.name,
            country=m.country,
            default_currency=m.default_currency,
            timezone=m.timezone,
            status=m.status,
            metadata=m.metadata
        )
        for m in SUPPORTED_MARKETS.values()
    ]


@router.get("/exchanges", response_model=List[ExchangeResponse], summary="List all supported stock exchanges")
async def list_exchanges():
    """Returns supported stock exchanges across global markets."""
    return [
        ExchangeResponse(
            id=e.id,
            market_id=e.market_id,
            code=e.code,
            name=e.name,
            country=e.country,
            currency=e.currency,
            timezone=e.timezone,
            mic_code=e.mic_code,
            website=e.website,
            status=e.status,
            trading_calendar_id=e.trading_calendar_id
        )
        for e in SUPPORTED_EXCHANGES.values()
    ]


# ─────────────────────────────────────────────────────────
# Securities Master & Search
# ─────────────────────────────────────────────────────────

@router.get("/securities/search", response_model=List[SecurityResponse], summary="Search securities across global markets")
async def search_securities(
    q: str = Query(..., min_length=1, description="Symbol or Company name search query"),
    market: Optional[str] = Query(None, description="Optional market code filter (PK, US, etc.)"),
    exchange: Optional[str] = Query(None, description="Optional exchange code filter (PSX, NASDAQ, etc.)")
):
    """Searches securities across Pakistan (PSX via .KA suffix) and all international markets via Yahoo Finance live directory."""
    from app.core.live_data import fetch_yahoo_finance_search
    from app.data.canonical.security import SecurityStatus, SecurityType

    results: list[SecurityDTO] = []
    seen_ids: set[str] = set()

    # 1. Canonical provider registry (PSX 1100+ stocks + international seeds)
    if market:
        providers = provider_registry.get_providers_for_market(market)
        for p in providers:
            res = await p.search_securities(query=q, market_code=market, exchange_code=exchange)
            results.extend(res)
    else:
        results = await provider_registry.search_all_markets(query=q)

    seen_ids = {s.security_id for s in results}

    # 2. Yahoo Finance live global search (fills in any non-PSX/international market results)
    try:
        yf_matches = await fetch_yahoo_finance_search(q, market_code=market)
        for ym in yf_matches:
            sym = ym["ticker"]
            mkt = ym["market_code"]
            exch = ym["exchange"]
            sec_id = build_security_id(mkt, exch, sym)
            if sec_id not in seen_ids:
                seen_ids.add(sec_id)
                results.append(SecurityDTO(
                    security_id=sec_id,
                    exchange_id=exch,
                    market_id=mkt,
                    symbol=sym,
                    company_name=ym["name"],
                    legal_name=ym["name"],
                    country={"PK": "Pakistan", "UK": "United Kingdom", "JP": "Japan", "HK": "Hong Kong", "IN": "India"}.get(mkt, "USA"),
                    currency=ym["currency"],
                    sector=ym.get("sector") or "Equities",
                    industry="Equities",
                    security_type=SecurityType.COMMON_STOCK,
                    status=SecurityStatus.ACTIVE,
                    primary_exchange=exch,
                    provider_security_id=f"{exch}:{sym}",
                ))
    except Exception:
        pass

    return [
        SecurityResponse(
            security_id=s.security_id,
            exchange_id=s.exchange_id,
            market_id=s.market_id,
            symbol=s.symbol,
            company_name=s.company_name,
            legal_name=s.legal_name,
            country=s.country,
            currency=s.currency,
            sector=s.sector,
            industry=s.industry,
            security_type=s.security_type.value if hasattr(s.security_type, "value") else str(s.security_type),
            status=s.status.value if hasattr(s.status, "value") else str(s.status),
            listing_date=s.listing_date,
            delisting_date=s.delisting_date,
            delisting_reason=s.delisting_reason,
            primary_exchange=s.primary_exchange,
            cik=s.cik,
            isin=s.isin,
        )
        for s in results[:50]
    ]


@router.get("/securities/{security_id}", response_model=SecurityResponse, summary="Get security metadata by global security_id")
async def get_security(security_id: str):
    """Retrieves point-in-time security metadata using globally unique security_id."""
    market_code, exchange_code, symbol = parse_security_id(security_id)
    providers = provider_registry.get_providers_for_market(market_code)
    sec = None
    for p in providers:
        sec = await p.get_security_metadata(symbol, market_code, exchange_code)
        if sec:
            break

    if not sec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Security '{security_id}' not found in canonical master."
        )

    return SecurityResponse(
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
    )


@router.get("/securities/{security_id}/prices", response_model=List[CanonicalPriceResponse], summary="Get canonical historical prices")
async def get_security_prices(
    security_id: str,
    start: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    end: Optional[date] = Query(None, description="End date (YYYY-MM-DD)")
):
    """Retrieves canonical OHLCV prices in native security currency."""
    market_code, exchange_code, symbol = parse_security_id(security_id)
    prices = await provider_registry.get_historical_prices(
        symbol=symbol,
        market_code=market_code,
        exchange_code=exchange_code,
        start_date=start,
        end_date=end,
    )

    return [
        CanonicalPriceResponse(
            security_id=p.security_id,
            ticker=p.ticker,
            timestamp=p.timestamp,
            open=float(p.open),
            high=float(p.high),
            low=float(p.low),
            close=float(p.close),
            adj_close=float(p.adj_close),
            volume=p.volume,
            vwap=float(p.vwap) if p.vwap else None,
            currency=p.currency,
            split_factor=float(p.split_factor),
            dividend_amount=float(p.dividend_amount),
            data_source=p.data_source,
            is_adjusted=p.is_adjusted,
            quality_flag=p.quality_flag
        )
        for p in prices
    ]


@router.get("/markets/{market}/securities", response_model=List[SecurityResponse], summary="List securities by market")
async def list_securities_by_market(market: str):
    """Returns securities for a given market (PK, US, etc.)."""
    providers = provider_registry.get_providers_for_market(market)
    results = []
    for p in providers:
        for exch in p.supported_exchanges:
            res = await p.get_security_list(market, exch)
            results.extend(res)

    return [
        SecurityResponse(
            security_id=s.security_id,
            exchange_id=s.exchange_id,
            market_id=s.market_id,
            symbol=s.symbol,
            company_name=s.company_name,
            country=s.country,
            currency=s.currency,
            sector=s.sector,
            industry=s.industry,
            security_type=s.security_type.value if hasattr(s.security_type, "value") else str(s.security_type),
            status=s.status.value if hasattr(s.status, "value") else str(s.status),
            listing_date=s.listing_date,
            delisting_date=s.delisting_date,
            delisting_reason=s.delisting_reason,
            primary_exchange=s.primary_exchange,
        )
        for s in results[:100]
    ]


@router.get("/markets/{market}/universe", response_model=HistoricalUniverseResponse, summary="Point-in-time historical universe")
async def get_historical_universe(
    market: str,
    as_of: date = Query(..., description="Point-in-time evaluation date (YYYY-MM-DD)"),
    exchange: Optional[str] = Query(None, description="Optional exchange filter")
):
    """Resolves active and delisted universe for a past date to prevent survivorship bias."""
    clean_m = market.strip().upper()
    clean_e = exchange.strip().upper() if exchange else "PSX" if clean_m == "PK" else "NASDAQ"

    providers = provider_registry.get_providers_for_market(clean_m)
    all_securities: List[SecurityDTO] = []
    for p in providers:
        res = await p.get_security_list(clean_m, clean_e)
        all_securities.extend(res)

    universe_result = resolve_historical_universe(
        market=clean_m,
        exchange=clean_e,
        as_of_date=as_of,
        securities=all_securities,
        has_exact_constituent_history=True
    )

    return HistoricalUniverseResponse(
        market=universe_result.market,
        exchange=universe_result.exchange,
        as_of_date=universe_result.as_of_date,
        total_count=universe_result.total_count,
        active_count=universe_result.active_count,
        delisted_included_count=universe_result.delisted_included_count,
        is_approximate=universe_result.is_approximate,
        warning=universe_result.warning,
        securities=[
            SecurityResponse(
                security_id=s.security_id,
                exchange_id=s.exchange_id,
                market_id=s.market_id,
                symbol=s.symbol,
                company_name=s.company_name,
                country=s.country,
                currency=s.currency,
                security_type=s.security_type.value if hasattr(s.security_type, "value") else str(s.security_type),
                status=s.status.value if hasattr(s.status, "value") else str(s.status),
                listing_date=s.listing_date,
                delisting_date=s.delisting_date,
                delisting_reason=s.delisting_reason,
                primary_exchange=s.primary_exchange,
            )
            for s in universe_result.securities[:100]
        ]
    )


# ─────────────────────────────────────────────────────────
# Ingestion & Provider Operations
# ─────────────────────────────────────────────────────────

@router.post("/ingest/historical", response_model=IngestionJobResponse, summary="Trigger async historical backfill job")
async def trigger_historical_backfill(
    req: IngestionJobRequest,
    background_tasks: BackgroundTasks
):
    """Triggers non-blocking background historical ingestion job."""
    job_id = str(uuid.uuid4())
    ingestion_scheduler.schedule_historical_backfill(
        job_id=job_id,
        market=req.market,
        exchange=req.exchange,
        symbol=req.symbol,
        start_date=req.start_date,
        end_date=req.end_date
    )
    return IngestionJobResponse(
        job_id=job_id,
        status="ACCEPTED",
        message=f"Historical backfill scheduled asynchronously for {req.market}/{req.exchange}"
    )


@router.get("/providers/health", response_model=List[ProviderHealthResponse], summary="Check operational health of all data providers")
async def get_providers_health():
    """Returns real-time health and latency statistics for all registered providers."""
    healths = await provider_registry.get_all_provider_health()
    return [
        ProviderHealthResponse(
            provider_name=h.provider_name,
            status=h.status.value if hasattr(h.status, "value") else str(h.status),
            latency_ms=h.latency_ms,
            last_checked=h.last_checked,
            error_count=h.error_count,
            rate_limit_remaining=h.rate_limit_remaining,
            message=h.message
        )
        for h in healths
    ]
