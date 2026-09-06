"""
StockSense AI — News & Sentiment ORM Models (Schema: news)
Dated Sentiment History & Material Event Tracking.
"""

import uuid
from datetime import datetime, date, timezone
from sqlalchemy import (
    Column, Integer, String, BigInteger, Numeric, Boolean, Date, DateTime, Text, ForeignKey, Index, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.db.base import Base


class NewsItem(Base):
    __tablename__ = "news_items"
    __table_args__ = (
        Index("idx_news_ticker_date", "ticker", "published_at"),
        Index("idx_news_veto", "ticker", "triggers_veto"),
        Index("idx_news_available", "ticker", "data_available_date"),
        {"schema": "news"}
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ticker = Column(String(10), ForeignKey("market_data.companies.ticker"), nullable=True)
    headline = Column(Text, nullable=False)
    summary = Column(Text)
    url = Column(String(2000))
    published_at = Column(DateTime(timezone=True), nullable=False)
    data_available_date = Column(DateTime(timezone=True), nullable=False)
    retrieved_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    source_name = Column(String(100), nullable=False)
    source_type = Column(String(30))  # 'sec_filing', 'press_release', 'news', 'social'
    source_reliability = Column(Numeric(4, 2), default=0.7)  # 0.0 to 1.0 weight
    
    # Sentiment scoring
    sentiment_score = Column(Numeric(5, 4))  # -1.0 to +1.0
    sentiment_label = Column(String(10))    # 'positive', 'neutral', 'negative'
    sentiment_confidence = Column(Numeric(5, 4))
    sentiment_model = Column(String(50), default="finbert")
    
    # Event Classification
    event_type = Column(String(50))         # 'earnings', 'product', 'regulatory', 'litigation', 'management'
    event_temporality = Column(String(20))  # 'one_time', 'medium_term', 'long_term'
    is_material = Column(Boolean, default=False)
    materiality_reason = Column(Text)
    
    # Hard Veto Trigger
    triggers_veto = Column(Boolean, default=False, nullable=False)
    veto_rule = Column(String(100), nullable=True)
    
    # SEC specifics
    filing_type = Column(String(20))        # '10-K', '10-Q', '8-K', 'Form-4'
    accession_number = Column(String(50))

    company = relationship("Company", back_populates="news_items")


class SentimentAggregate(Base):
    """
    Dated historical sentiment observations to prevent future news leakage in backtests.
    """
    __tablename__ = "sentiment_aggregates"
    __table_args__ = (
        UniqueConstraint("ticker", "aggregate_date", name="uq_sentiment_ticker_date"),
        Index("idx_sentiment_available", "ticker", "data_available_date"),
        {"schema": "news"}
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String(10), ForeignKey("market_data.companies.ticker"), nullable=False)
    aggregate_date = Column(Date, nullable=False)
    data_available_date = Column(Date, nullable=False)
    
    sentiment_7d = Column(Numeric(5, 4))
    sentiment_30d = Column(Numeric(5, 4))
    sentiment_90d = Column(Numeric(5, 4))
    news_count_7d = Column(Integer, default=0)
    news_count_30d = Column(Integer, default=0)
    
    sentiment_trend = Column(String(20))  # 'improving', 'stable', 'deteriorating'
    trend_change_7d = Column(Numeric(5, 4))
    high_weight_sentiment_30d = Column(Numeric(5, 4))
    sentiment_score = Column(Numeric(5, 2))  # 0 to 100
    top_events_json = Column(JSONB)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class InsiderTransaction(Base):
    __tablename__ = "insider_transactions"
    __table_args__ = (
        Index("idx_insider_ticker_date", "ticker", "transaction_date"),
        {"schema": "news"}
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String(10), ForeignKey("market_data.companies.ticker"), nullable=False)
    transaction_date = Column(Date, nullable=False)
    filing_date = Column(Date, nullable=False)
    data_available_date = Column(Date, nullable=False)
    
    insider_name = Column(String(255), nullable=False)
    insider_title = Column(String(255))
    transaction_type = Column(String(20), nullable=False)  # 'buy', 'sell', 'option_exercise'
    shares = Column(BigInteger, nullable=False)
    price_per_share = Column(Numeric(12, 4))
    total_value = Column(BigInteger)
    shares_owned_after = Column(BigInteger)
    
    # 10b5-1 Plan Context
    is_planned_10b51 = Column(Boolean, default=False)
    is_discretionary = Column(Boolean, default=True)
    signal_strength = Column(String(10), default="neutral")  # 'strong_buy', 'neutral', 'strong_sell'
    form_type = Column(String(10), default="Form 4")
    accession_number = Column(String(50))
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
