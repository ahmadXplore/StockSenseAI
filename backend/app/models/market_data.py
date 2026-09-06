"""
StockSense AI — Market Data ORM Models (Schema: market_data)
Supports generic multi-market architecture: Pakistan (PSX), US (NYSE/NASDAQ),
UK (LSE), Japan (TSE), Hong Kong (HKEX), India (NSE/BSE).
"""

import uuid
from datetime import datetime, date, timezone
from sqlalchemy import (
    Column, Integer, String, BigInteger, Numeric, Boolean, Date, DateTime, Text, ForeignKey, Index, CheckConstraint
)
from sqlalchemy.orm import relationship
from app.db.base import Base


class Market(Base):
    """
    Generic canonical Market representation (e.g., Pakistan, United States, United Kingdom).
    """
    __tablename__ = "markets"
    __table_args__ = (
        Index("idx_markets_code", "code"),
        {"schema": "market_data"}
    )

    id = Column(String(20), primary_key=True)       # e.g., 'PK', 'US', 'GB', 'JP', 'HK', 'IN'
    code = Column(String(20), nullable=False, unique=True)
    name = Column(String(100), nullable=False)
    country = Column(String(100), nullable=False)
    default_currency = Column(String(10), nullable=False)  # PKR, USD, GBP, JPY, HKD, INR
    timezone = Column(String(50), nullable=False)          # Asia/Karachi, America/New_York, Europe/London
    status = Column(String(20), default="ACTIVE", nullable=False) # ACTIVE, INACTIVE, RESTRICTED
    metadata_json = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    exchanges = relationship("Exchange", back_populates="market", cascade="all, delete-orphan")
    securities = relationship("SecurityMaster", back_populates="market")


class Exchange(Base):
    """
    Generic canonical Exchange representation (e.g., PSX, NASDAQ, NYSE, LSE, TSE).
    """
    __tablename__ = "exchanges"
    __table_args__ = (
        Index("idx_exchanges_market", "market_id"),
        Index("idx_exchanges_code", "code"),
        {"schema": "market_data"}
    )

    id = Column(String(30), primary_key=True)       # e.g., 'PSX', 'NASDAQ', 'NYSE', 'LSE', 'TSE', 'HKEX', 'NSE', 'BSE'
    market_id = Column(String(20), ForeignKey("market_data.markets.id"), nullable=False)
    code = Column(String(20), nullable=False)
    name = Column(String(150), nullable=False)
    country = Column(String(100), nullable=False)
    currency = Column(String(10), nullable=False)
    timezone = Column(String(50), nullable=False)
    mic_code = Column(String(10), nullable=True)     # Market Identifier Code: XKAR, XNAS, XNYS, XLON, XJPX
    website = Column(String(255), nullable=True)
    status = Column(String(20), default="ACTIVE", nullable=False)
    trading_calendar_id = Column(String(50), default="DEFAULT")
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    market = relationship("Market", back_populates="exchanges")
    securities = relationship("SecurityMaster", back_populates="exchange", cascade="all, delete-orphan")


class SecurityMaster(Base):
    """
    Globally unique master security registry across all markets.
    security_id is globally unique (e.g. PK.PSX.ENGRO, US.NASDAQ.AAPL, US.NYSE.BRK_A).
    """
    __tablename__ = "securities"
    __table_args__ = (
        Index("idx_securities_market_exchange", "market_id", "exchange_id"),
        Index("idx_securities_symbol", "symbol"),
        Index("idx_securities_status", "status"),
        Index("idx_securities_company_name", "company_name"),
        {"schema": "market_data"}
    )

    security_id = Column(String(60), primary_key=True)  # Global unique key: <MARKET>.<EXCHANGE>.<SYMBOL>
    exchange_id = Column(String(30), ForeignKey("market_data.exchanges.id"), nullable=False)
    market_id = Column(String(20), ForeignKey("market_data.markets.id"), nullable=False)
    symbol = Column(String(30), nullable=False)
    company_name = Column(String(255), nullable=False)
    legal_name = Column(String(255), nullable=True)
    country = Column(String(100), nullable=False)
    currency = Column(String(10), nullable=False)
    sector = Column(String(100), nullable=True)
    industry = Column(String(100), nullable=True)
    security_type = Column(String(30), default="COMMON_STOCK", nullable=False) # COMMON_STOCK, ETF, INDEX, PREFERRED, ADR
    status = Column(String(30), default="ACTIVE", nullable=False) # ACTIVE, DELISTED, SUSPENDED, MERGED, ACQUIRED
    listing_date = Column(Date, nullable=True)
    delisting_date = Column(Date, nullable=True)
    delisting_reason = Column(Text, nullable=True)
    primary_exchange = Column(String(30), nullable=True)
    
    # Global Identifiers
    cik = Column(String(20), nullable=True)
    isin = Column(String(20), nullable=True)
    cusip = Column(String(20), nullable=True)
    sedol = Column(String(20), nullable=True)
    figi = Column(String(20), nullable=True)
    provider_security_id = Column(String(100), nullable=True)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    exchange = relationship("Exchange", back_populates="securities")
    market = relationship("Market", back_populates="securities")
    symbol_history = relationship("SymbolHistory", back_populates="security", cascade="all, delete-orphan")


class SymbolHistory(Base):
    """
    Audit trail of ticker symbol transitions (e.g. ABC -> XYZ) for a single security_id.
    """
    __tablename__ = "symbol_history"
    __table_args__ = (
        Index("idx_sym_hist_sec_date", "security_id", "effective_from"),
        {"schema": "market_data"}
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    security_id = Column(String(60), ForeignKey("market_data.securities.security_id"), nullable=False)
    old_symbol = Column(String(30), nullable=False)
    new_symbol = Column(String(30), nullable=False)
    effective_from = Column(Date, nullable=False)
    effective_to = Column(Date, nullable=True)
    reason = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    security = relationship("SecurityMaster", back_populates="symbol_history")


class RawMarketData(Base):
    """
    Raw data staging layer to preserve provider payloads prior to validation and canonicalization.
    """
    __tablename__ = "raw_market_data"
    __table_args__ = (
        Index("idx_raw_market_source", "source", "retrieval_timestamp"),
        Index("idx_raw_market_provider", "provider"),
        {"schema": "market_data"}
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    source = Column(String(50), nullable=False)           # 'psx_kaggle_csv', 'yfinance_api', 'alpha_vantage', 'stooq'
    provider = Column(String(50), nullable=False)         # 'kaggle_psx', 'yahoo_finance', 'alpha_vantage'
    retrieval_timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    original_reference = Column(String(255), nullable=True) # File path or URL
    checksum = Column(String(64), nullable=True)          # SHA-256
    raw_payload = Column(Text, nullable=True)             # JSON or raw CSV snippet
    record_count = Column(Integer, default=0, nullable=False)
    schema_version = Column(String(20), default="1.0", nullable=False)
    ingested = Column(Boolean, default=False, nullable=False)


class IngestionJobLog(Base):
    """
    Execution logs and quality metrics for historical backfills and incremental ETL jobs.
    """
    __tablename__ = "ingestion_jobs"
    __table_args__ = (
        Index("idx_ingest_job_status", "status", "start_time"),
        Index("idx_ingest_job_market", "market_code", "exchange_code"),
        {"schema": "market_data"}
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    job_type = Column(String(50), nullable=False)         # 'HISTORICAL_BACKFILL', 'INCREMENTAL_UPDATE', 'DATASET_VALIDATION'
    market_code = Column(String(20), nullable=False)
    exchange_code = Column(String(30), nullable=False)
    provider_name = Column(String(50), nullable=False)
    start_time = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(30), default="RUNNING", nullable=False) # 'RUNNING', 'SUCCESS', 'PARTIAL', 'FAILED'
    records_checked = Column(Integer, default=0, nullable=False)
    records_accepted = Column(Integer, default=0, nullable=False)
    records_rejected = Column(Integer, default=0, nullable=False)
    quality_score = Column(Numeric(5, 2), default=100.0, nullable=False)
    error_summary = Column(Text, nullable=True)
    details_json = Column(Text, nullable=True)


class Company(Base):
    """
    Company metadata entity. Linked to existing schemas for fundamentals, reports, news, and analysis.
    """
    __tablename__ = "companies"
    __table_args__ = (
        Index("idx_companies_ticker", "ticker"),
        Index("idx_companies_name", "name"),
        Index("idx_companies_sector", "sector"),
        Index("idx_companies_active", "is_active"),
        {"schema": "market_data"}
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String(20), nullable=False, unique=True)
    security_id = Column(String(60), nullable=True)  # References global security_id
    name = Column(String(255), nullable=False)
    exchange = Column(String(20), default="NASDAQ")  # PSX, NASDAQ, NYSE, LSE, TSE
    sector = Column(String(100))
    industry = Column(String(100))
    country = Column(String(50), default="USA")
    currency = Column(String(10), default="USD", nullable=False)
    market_cap = Column(BigInteger)                  # in native currency units
    shares_outstanding = Column(BigInteger)
    float_shares = Column(BigInteger)
    employee_count = Column(Integer)
    description = Column(Text)
    website = Column(String(255))
    cik = Column(String(20))                         # SEC CIK number
    sic_code = Column(String(10))
    isin = Column(String(20))
    cusip = Column(String(20))
    ipo_date = Column(Date)
    
    # Soft deletion & survivorship bias tracking
    is_active = Column(Boolean, default=True, nullable=False)
    is_delisted = Column(Boolean, default=False, nullable=False)
    delisted_date = Column(Date, nullable=True)
    delisted_reason = Column(Text, nullable=True)
    
    # Data provenance
    data_source = Column(String(50), default="sec_edgar")
    data_as_of = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    price_data = relationship("PriceData", back_populates="company", cascade="all, delete-orphan")
    technical_indicators = relationship("TechnicalIndicator", back_populates="company", cascade="all, delete-orphan")
    corporate_actions = relationship("CorporateAction", back_populates="company", cascade="all, delete-orphan")
    income_statements = relationship("IncomeStatement", back_populates="company", cascade="all, delete-orphan")
    balance_sheets = relationship("BalanceSheet", back_populates="company", cascade="all, delete-orphan")
    cash_flow_statements = relationship("CashFlowStatement", back_populates="company", cascade="all, delete-orphan")
    financial_ratios = relationship("FinancialRatio", back_populates="company", cascade="all, delete-orphan")
    analyst_estimates = relationship("AnalystEstimate", back_populates="company", cascade="all, delete-orphan")
    earnings_events = relationship("EarningsEvent", back_populates="company", cascade="all, delete-orphan")
    news_items = relationship("NewsItem", back_populates="company", cascade="all, delete-orphan")
    reports = relationship("AnalysisReport", back_populates="company", cascade="all, delete-orphan")


class PriceData(Base):
    """
    Canonical OHLCV historical price record.
    Preserves native currency without destructive modifications.
    """
    __tablename__ = "price_data"
    __table_args__ = (
        Index("idx_price_ticker_time", "ticker", "time"),
        Index("idx_price_sec_time", "security_id", "time"),
        Index("idx_price_ticker_source", "ticker", "time", "data_source"),
        CheckConstraint("volume >= 0", name="chk_price_volume_non_negative"),
        CheckConstraint("open >= 0 AND high >= 0 AND low >= 0 AND close >= 0", name="chk_prices_positive"),
        CheckConstraint("high >= low", name="chk_price_high_gte_low"),
        {"schema": "market_data"}
    )

    time = Column(DateTime(timezone=True), primary_key=True, nullable=False)
    ticker = Column(String(20), ForeignKey("market_data.companies.ticker"), primary_key=True, nullable=False)
    security_id = Column(String(60), nullable=True) # e.g. PK.PSX.ENGRO, US.NASDAQ.AAPL
    open = Column(Numeric(12, 4), nullable=False)
    high = Column(Numeric(12, 4), nullable=False)
    low = Column(Numeric(12, 4), nullable=False)
    close = Column(Numeric(12, 4), nullable=False)
    adj_close = Column(Numeric(12, 4), nullable=False)
    volume = Column(BigInteger, nullable=False)
    vwap = Column(Numeric(12, 4), nullable=True)
    currency = Column(String(10), default="USD", nullable=False)
    
    # Corporate action adjustment tracking
    split_factor = Column(Numeric(10, 6), default=1.0)
    dividend_amount = Column(Numeric(10, 6), default=0.0)
    
    # Data quality & provenance
    source_id = Column(String(100), nullable=True)
    data_source = Column(String(50), nullable=False)  # 'kaggle_psx', 'yfinance', 'stooq', 'alpha_vantage'
    is_adjusted = Column(Boolean, default=True, nullable=False)
    quality_flag = Column(String(20), default="ok")   # 'ok', 'suspect', 'gap', 'flagged_move'
    retrieved_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    company = relationship("Company", back_populates="price_data")


class TechnicalIndicator(Base):
    """
    Time-series technical indicators for ML feature extraction, backtesting, and technical charts.
    """
    __tablename__ = "technical_indicators"
    __table_args__ = (
        Index("idx_tech_ticker_time", "ticker", "time"),
        {"schema": "market_data"}
    )

    time = Column(DateTime(timezone=True), primary_key=True, nullable=False)
    ticker = Column(String(20), ForeignKey("market_data.companies.ticker"), primary_key=True, nullable=False)
    
    # Moving Averages & Trend
    sma_20 = Column(Numeric(12, 4))
    sma_50 = Column(Numeric(12, 4))
    sma_200 = Column(Numeric(12, 4))
    ema_12 = Column(Numeric(12, 4))
    ema_26 = Column(Numeric(12, 4))
    
    # Momentum & Oscillators
    rsi_14 = Column(Numeric(8, 4))
    macd_line = Column(Numeric(10, 4))
    macd_signal = Column(Numeric(10, 4))
    macd_histogram = Column(Numeric(10, 4))
    
    # Volatility
    bb_upper = Column(Numeric(12, 4))
    bb_middle = Column(Numeric(12, 4))
    bb_lower = Column(Numeric(12, 4))
    bb_width = Column(Numeric(8, 4))
    atr_14 = Column(Numeric(10, 4))
    realized_vol_20d = Column(Numeric(8, 4))
    realized_vol_60d = Column(Numeric(8, 4))
    
    # Volume & Structure
    obv = Column(BigInteger)
    volume_ratio = Column(Numeric(8, 4))
    support_1 = Column(Numeric(12, 4))
    support_2 = Column(Numeric(12, 4))
    resistance_1 = Column(Numeric(12, 4))
    resistance_2 = Column(Numeric(12, 4))
    
    calculated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    company = relationship("Company", back_populates="technical_indicators")


class CorporateAction(Base):
    """
    Corporate action events (splits, dividends, rights, bonus issues, mergers, delistings).
    """
    __tablename__ = "corporate_actions"
    __table_args__ = (
        Index("idx_corporate_actions_ticker", "ticker", "action_date"),
        Index("idx_corp_actions_sec_date", "security_id", "action_date"),
        {"schema": "market_data"}
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String(20), ForeignKey("market_data.companies.ticker"), nullable=False)
    security_id = Column(String(60), nullable=True)
    action_date = Column(Date, nullable=False)
    action_type = Column(String(50), nullable=False)  # 'stock_split', 'reverse_split', 'cash_dividend', 'bonus_issue', 'rights_issue', 'merger', 'spinoff', 'symbol_change', 'delisting'
    split_ratio = Column(Numeric(10, 4))
    dividend_amount = Column(Numeric(10, 6))
    dividend_type = Column(String(20))              # 'cash', 'stock'
    notes = Column(Text)
    source = Column(String(100))
    verified = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    company = relationship("Company", back_populates="corporate_actions")


class IndexConstituent(Base):
    __tablename__ = "index_constituents"
    __table_args__ = (
        Index("idx_constituents_index_date", "index_ticker", "added_date", "removed_date"),
        {"schema": "market_data"}
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    index_ticker = Column(String(20), nullable=False)  # 'SPY', 'QQQ', 'KSE100'
    ticker = Column(String(20), nullable=False)
    security_id = Column(String(60), nullable=True)
    added_date = Column(Date, nullable=False)
    removed_date = Column(Date, nullable=True)         # NULL if still an active member
    removal_reason = Column(String(100), nullable=True) # 'delisted', 'bankrupt', 'acquired', 'index_rebalance'
    weight = Column(Numeric(8, 6))
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
