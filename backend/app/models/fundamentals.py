"""
StockSense AI — Fundamental Data ORM Models (Schema: fundamentals)
Point-in-Time Compliance: Strict separation of period_end_date vs data_available_date.
"""

from datetime import datetime, date, timezone
from sqlalchemy import (
    Column, Integer, String, BigInteger, Numeric, Boolean, Date, DateTime, Text, ForeignKey, Index, UniqueConstraint
)
from sqlalchemy.orm import relationship
from app.db.base import Base


class IncomeStatement(Base):
    __tablename__ = "income_statements"
    __table_args__ = (
        UniqueConstraint("ticker", "fiscal_year", "fiscal_quarter", "report_type", name="uq_income_period"),
        Index("idx_income_ticker_date", "ticker", "period_end_date"),
        Index("idx_income_available_date", "ticker", "data_available_date"),
        {"schema": "fundamentals"}
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String(10), ForeignKey("market_data.companies.ticker"), nullable=False)
    fiscal_year = Column(Integer, nullable=False)
    fiscal_quarter = Column(Integer, nullable=True)  # 1-4, NULL for annual
    period_end_date = Column(Date, nullable=False)
    report_type = Column(String(10), nullable=False) # 'annual', 'quarterly', 'ttm'
    
    # CRITICAL: Point-in-Time Availability Tracking
    filing_date = Column(Date)
    announcement_date = Column(Date)
    data_available_date = Column(Date, nullable=False)
    
    # Revenue & margins
    revenue = Column(BigInteger)
    revenue_growth_yoy = Column(Numeric(8, 4))
    gross_profit = Column(BigInteger)
    gross_margin = Column(Numeric(8, 4))
    operating_income = Column(BigInteger)
    operating_margin = Column(Numeric(8, 4))
    ebitda = Column(BigInteger)
    ebitda_margin = Column(Numeric(8, 4))
    
    # Net income & EPS
    net_income = Column(BigInteger)
    net_margin = Column(Numeric(8, 4))
    eps_reported = Column(Numeric(10, 4))
    eps_diluted = Column(Numeric(10, 4))
    shares_diluted = Column(BigInteger)
    currency = Column(String(10), default="USD", nullable=False)
    
    # Consensus
    eps_consensus_estimate = Column(Numeric(10, 4))
    eps_beat_miss = Column(Numeric(10, 4))
    revenue_consensus_est = Column(BigInteger)
    revenue_beat_miss = Column(BigInteger)
    
    # Restatement & Source
    is_restated = Column(Boolean, default=False)
    original_eps_reported = Column(Numeric(10, 4))
    data_source = Column(String(100), default="sec_edgar")
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    company = relationship("Company", back_populates="income_statements")


class BalanceSheet(Base):
    __tablename__ = "balance_sheets"
    __table_args__ = (
        Index("idx_balance_ticker_available", "ticker", "data_available_date"),
        {"schema": "fundamentals"}
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String(10), ForeignKey("market_data.companies.ticker"), nullable=False)
    fiscal_year = Column(Integer, nullable=False)
    fiscal_quarter = Column(Integer, nullable=True)
    period_end_date = Column(Date, nullable=False)
    report_type = Column(String(10), nullable=False)
    data_available_date = Column(Date, nullable=False)
    
    cash_and_equivalents = Column(BigInteger)
    short_term_investments = Column(BigInteger)
    total_current_assets = Column(BigInteger)
    total_assets = Column(BigInteger)
    short_term_debt = Column(BigInteger)
    long_term_debt = Column(BigInteger)
    total_current_liabilities = Column(BigInteger)
    total_liabilities = Column(BigInteger)
    total_equity = Column(BigInteger)
    retained_earnings = Column(BigInteger)
    net_debt = Column(BigInteger)
    debt_to_equity = Column(Numeric(10, 4))
    current_ratio = Column(Numeric(8, 4))
    quick_ratio = Column(Numeric(8, 4))
    book_value_per_share = Column(Numeric(10, 4))
    currency = Column(String(10), default="USD", nullable=False)
    data_source = Column(String(100), default="sec_edgar")
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    company = relationship("Company", back_populates="balance_sheets")


class CashFlowStatement(Base):
    __tablename__ = "cash_flow_statements"
    __table_args__ = (
        Index("idx_cashflow_ticker_available", "ticker", "data_available_date"),
        {"schema": "fundamentals"}
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String(10), ForeignKey("market_data.companies.ticker"), nullable=False)
    fiscal_year = Column(Integer, nullable=False)
    fiscal_quarter = Column(Integer, nullable=True)
    period_end_date = Column(Date, nullable=False)
    report_type = Column(String(10), nullable=False)
    data_available_date = Column(Date, nullable=False)
    
    operating_cash_flow = Column(BigInteger)
    capital_expenditures = Column(BigInteger)
    free_cash_flow = Column(BigInteger)
    fcf_margin = Column(Numeric(8, 4))
    fcf_per_share = Column(Numeric(10, 4))
    dividends_paid = Column(BigInteger)
    share_repurchases = Column(BigInteger)
    net_debt_issuance = Column(BigInteger)
    total_shareholder_return = Column(BigInteger)
    currency = Column(String(10), default="USD", nullable=False)
    data_source = Column(String(100), default="sec_edgar")
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    company = relationship("Company", back_populates="cash_flow_statements")


class FinancialRatio(Base):
    __tablename__ = "financial_ratios"
    __table_args__ = (
        UniqueConstraint("ticker", "as_of_date", name="uq_ratios_ticker_date"),
        Index("idx_ratios_ticker_available", "ticker", "data_available_date"),
        {"schema": "fundamentals"}
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String(10), ForeignKey("market_data.companies.ticker"), nullable=False)
    as_of_date = Column(Date, nullable=False)
    data_available_date = Column(Date, nullable=False)
    
    # Valuation multiples
    pe_ratio = Column(Numeric(10, 4))
    forward_pe = Column(Numeric(10, 4))
    peg_ratio = Column(Numeric(10, 4))
    price_to_sales = Column(Numeric(10, 4))
    price_to_book = Column(Numeric(10, 4))
    price_to_fcf = Column(Numeric(10, 4))
    ev_to_ebitda = Column(Numeric(10, 4))
    ev_to_sales = Column(Numeric(10, 4))
    fcf_yield = Column(Numeric(8, 6))
    earnings_yield = Column(Numeric(8, 6))
    dividend_yield = Column(Numeric(8, 6))
    
    # Profitability & Return
    roe = Column(Numeric(8, 4))
    roa = Column(Numeric(8, 4))
    roic = Column(Numeric(8, 4))
    wacc_estimate = Column(Numeric(8, 4))
    roic_minus_wacc = Column(Numeric(8, 4))
    
    # Leverage
    debt_to_ebitda = Column(Numeric(8, 4))
    interest_coverage = Column(Numeric(8, 4))
    debt_to_equity = Column(Numeric(8, 4))
    net_debt_to_equity = Column(Numeric(8, 4))
    
    # Growth & Efficiency
    revenue_growth_yoy = Column(Numeric(8, 4))
    eps_growth_yoy = Column(Numeric(8, 4))
    fcf_growth_yoy = Column(Numeric(8, 4))
    asset_turnover = Column(Numeric(8, 4))
    inventory_turnover = Column(Numeric(8, 4))
    
    # Sector Comparison
    sector_pe_median = Column(Numeric(10, 4))
    sector_ev_ebitda_median = Column(Numeric(10, 4))
    pe_vs_sector_pct = Column(Numeric(8, 4))
    data_source = Column(String(100))
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    company = relationship("Company", back_populates="financial_ratios")


class AnalystEstimate(Base):
    __tablename__ = "analyst_estimates"
    __table_args__ = ({"schema": "fundamentals"})

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String(10), ForeignKey("market_data.companies.ticker"), nullable=False)
    estimate_date = Column(Date, nullable=False)
    fiscal_year = Column(Integer)
    fiscal_quarter = Column(Integer)
    
    eps_consensus = Column(Numeric(10, 4))
    eps_high = Column(Numeric(10, 4))
    eps_low = Column(Numeric(10, 4))
    eps_num_analysts = Column(Integer)
    revenue_consensus = Column(BigInteger)
    revenue_high = Column(BigInteger)
    revenue_low = Column(BigInteger)
    revenue_num_analysts = Column(Integer)
    price_target_mean = Column(Numeric(10, 4))
    price_target_high = Column(Numeric(10, 4))
    price_target_low = Column(Numeric(10, 4))
    buy_ratings = Column(Integer)
    hold_ratings = Column(Integer)
    sell_ratings = Column(Integer)
    eps_revision_7d = Column(Numeric(10, 4))
    eps_revision_30d = Column(Numeric(10, 4))
    revenue_revision_30d = Column(BigInteger)
    data_source = Column(String(100), default="fmp")
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    company = relationship("Company", back_populates="analyst_estimates")


class EarningsEvent(Base):
    """
    Tracks confirmed and estimated earnings announcements, consensus expectations, and beat/miss history.
    """
    __tablename__ = "earnings_events"
    __table_args__ = (
        Index("idx_earnings_ticker_date", "ticker", "event_date"),
        {"schema": "fundamentals"}
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String(10), ForeignKey("market_data.companies.ticker"), nullable=False)
    event_date = Column(Date, nullable=False)
    is_confirmed = Column(Boolean, default=False)
    fiscal_period = Column(String(20)) # e.g. 'Q3 2025'
    consensus_eps = Column(Numeric(10, 4))
    consensus_revenue = Column(BigInteger)
    actual_eps = Column(Numeric(10, 4), nullable=True)
    actual_revenue = Column(BigInteger, nullable=True)
    beat_miss_eps = Column(Numeric(10, 4), nullable=True)
    source = Column(String(50), default="finnhub")
    retrieved_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    company = relationship("Company", back_populates="earnings_events")
