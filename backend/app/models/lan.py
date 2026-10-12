"""
StockSense AI — LAN Device Authorization & Access Log ORM Models (Schema: audit)
Secures LAN perimeter by tracking authorized devices, pending approval requests,
and auditing network activity across the local wireless/wired network.
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, Text, Index
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base


class LANDevice(Base):
    """
    Registered client device attempting to connect to StockSense AI over the LAN.
    Access is gated until explicitly approved by an administrator or if identified as host.
    """
    __tablename__ = "lan_devices"
    __table_args__ = (
        Index("idx_lan_device_identifier", "device_identifier", unique=True),
        Index("idx_lan_device_status", "status"),
        {"schema": "audit"}
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    device_name = Column(String(100), nullable=False)
    device_identifier = Column(String(128), unique=True, index=True, nullable=False)
    token_hash = Column(String(255), nullable=True)
    current_ip = Column(String(50), nullable=False)
    user_agent = Column(Text, nullable=True)
    status = Column(String(20), default="PENDING", nullable=False)  # PENDING, APPROVED, REJECTED, REVOKED
    is_server_host = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    last_seen_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    created_by = Column(String(100), nullable=True)
    rejection_reason = Column(Text, nullable=True)
    pending_claim_token = Column(String(255), nullable=True)


class LANAccessLog(Base):
    """
    Audit log for all LAN access events, device registrations, authorization approvals,
    rejections, revivals, and unauthorized bypass attempts.
    """
    __tablename__ = "lan_access_logs"
    __table_args__ = (
        Index("idx_lan_log_timestamp", "timestamp"),
        Index("idx_lan_log_device_identifier", "device_identifier"),
        Index("idx_lan_log_action", "action"),
        {"schema": "audit"}
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    device_id = Column(UUID(as_uuid=True), nullable=True)
    device_identifier = Column(String(128), nullable=True, index=True)
    ip_address = Column(String(50), nullable=False)
    user_agent = Column(Text, nullable=True)
    endpoint = Column(String(255), nullable=False)
    method = Column(String(10), nullable=False)
    action = Column(String(50), nullable=False)  # DEVICE_REQUESTED, DEVICE_APPROVED, DEVICE_REJECTED, etc.
    status = Column(String(20), nullable=False)  # SUCCESS, BLOCKED, PENDING, FAILED
    details = Column(Text, nullable=True)
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
