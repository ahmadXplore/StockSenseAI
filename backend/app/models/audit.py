"""
StockSense AI — Audit, Data Quality & Report Export ORM Models (Schema: audit)
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, BigInteger, Boolean, DateTime, Text, Index, ForeignKey
)
from sqlalchemy.dialects.postgresql import UUID, INET, JSONB
from app.db.base import Base
from app.models.enums import ReportExportStatus, DataQualityStatus


class AnalysisRequest(Base):
    __tablename__ = "analysis_requests"
    __table_args__ = (
        Index("idx_audit_req_ticker_date", "ticker", "requested_at"),
        {"schema": "audit"}
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=True)
    ticker = Column(String(10), nullable=True)
    request_id = Column(String(100), nullable=True)
    requested_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    duration_ms = Column(Integer, nullable=True)
    status = Column(String(20), default="completed", nullable=False) # 'completed', 'failed', 'cached'
    error_message = Column(Text, nullable=True)
    ip_address = Column(INET, nullable=True)
    user_agent = Column(Text, nullable=True)
    report_id = Column(UUID(as_uuid=True), nullable=True)


class DataQualityLog(Base):
    __tablename__ = "data_quality_log"
    __table_args__ = (
        Index("idx_dq_source_date", "data_source", "logged_at"),
        {"schema": "audit"}
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    logged_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    data_source = Column(String(50), nullable=False)   # 'yfinance', 'sec_edgar', 'stooq', 'fred'
    ticker = Column(String(10), nullable=True)
    data_type = Column(String(50), nullable=False)     # 'price', 'income_statement', 'macro'
    quality_check = Column(String(100), nullable=False) # 'completeness', 'staleness', 'anomaly_split'
    status = Column(String(20), default=DataQualityStatus.PASS.value, nullable=False) # 'PASS', 'WARNING', 'FAIL'
    severity = Column(String(20), default="LOW")
    missing_count = Column(Integer, default=0)
    stale_days = Column(Integer, default=0)
    detail = Column(Text, nullable=True)
    auto_remediated = Column(Boolean, default=False)
    remediation_action = Column(Text, nullable=True)


class ReportExport(Base):
    """
    Export jobs for PDF, JSON, and CSV report downloads.
    """
    __tablename__ = "report_exports"
    __table_args__ = (
        Index("idx_export_report", "report_id"),
        {"schema": "audit"}
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    report_id = Column(UUID(as_uuid=True), ForeignKey("analysis.analysis_reports.id"), nullable=False)
    format = Column(String(10), default="pdf", nullable=False) # 'pdf', 'json', 'csv'
    status = Column(String(20), default=ReportExportStatus.PENDING.value, nullable=False)
    file_path = Column(String(500), nullable=True)
    file_size_bytes = Column(BigInteger, nullable=True)
    requested_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)
