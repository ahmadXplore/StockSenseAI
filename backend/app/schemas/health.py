"""
StockSense AI — Health Schemas
"""

from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime


class HealthResponse(BaseModel):
    status: str = Field(..., example="healthy")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    version: str = Field("1.0.0")
    database: str = Field(..., example="connected")
    redis: str = Field(..., example="connected")
    environment: str = Field(..., example="development")


class ServiceHealth(BaseModel):
    service: str
    status: str
    latency_ms: Optional[float] = None
    detail: Optional[str] = None
