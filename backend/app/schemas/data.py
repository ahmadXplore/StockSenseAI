"""
StockSense AI — Canonical Multi-Market Data API Schemas
"""

from __future__ import annotations
from datetime import date, datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class MarketResponse(BaseModel):
    id: str
    code: str
    name: str
    country: str
    default_currency: str
    timezone: str
    status: str
    metadata: Dict[str, Any] = {}


class ExchangeResponse(BaseModel):
    id: str
    market_id: str
    code: str
    name: str
    country: str
    currency: str
    timezone: str
    mic_code: Optional[str] = None
    website: Optional[str] = None
    status: str
    trading_calendar_id: str


class SecurityResponse(BaseModel):
    security_id: str
    exchange_id: str
    market_id: str
    symbol: str
    company_name: str
    legal_name: Optional[str] = None
    country: str
    currency: str
    sector: Optional[str] = None
    industry: Optional[str] = None
    security_type: str
    status: str
    listing_date: Optional[date] = None
    delisting_date: Optional[date] = None
    delisting_reason: Optional[str] = None
    primary_exchange: Optional[str] = None
    cik: Optional[str] = None
    isin: Optional[str] = None


class CanonicalPriceResponse(BaseModel):
    security_id: str
    ticker: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    adj_close: float
    volume: int
    vwap: Optional[float] = None
    currency: str
    split_factor: float = 1.0
    dividend_amount: float = 0.0
    data_source: str
    is_adjusted: bool
    quality_flag: str


class HistoricalUniverseResponse(BaseModel):
    market: str
    exchange: str
    as_of_date: date
    total_count: int
    active_count: int
    delisted_included_count: int
    is_approximate: bool
    warning: Optional[str] = None
    securities: List[SecurityResponse]


class IngestionJobRequest(BaseModel):
    market: str = Field(..., description="Market code e.g. PK, US")
    exchange: str = Field(..., description="Exchange code e.g. PSX, NASDAQ")
    symbol: Optional[str] = Field(None, description="Optional target symbol e.g. ENGRO, AAPL")
    start_date: Optional[date] = Field(None, description="Start date for backfill")
    end_date: Optional[date] = Field(None, description="End date for backfill")


class IngestionJobResponse(BaseModel):
    job_id: str
    status: str
    message: str


class ProviderHealthResponse(BaseModel):
    provider_name: str
    status: str
    latency_ms: float
    last_checked: datetime
    error_count: int
    rate_limit_remaining: Optional[int] = None
    message: Optional[str] = None
