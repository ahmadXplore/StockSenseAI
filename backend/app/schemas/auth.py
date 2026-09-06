"""
StockSense AI — Authentication & Biometric Schemas
"""

import uuid
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class FaceSignupRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=150, description="User's full name or display name")
    email: Optional[str] = Field(None, description="Optional email address")
    role: Optional[str] = Field("user", description="'admin' or 'user'")
    admin_pin: Optional[str] = Field(None, description="Optional master PIN (e.g. admin2026 or 9928) to authorize admin registration")
    descriptor: List[float] = Field(..., min_items=128, max_items=128, description="128-dimensional biometric face descriptor")


class FaceLoginRequest(BaseModel):
    identifier: Optional[str] = Field(None, description="User's name, username, or email")
    descriptor: List[float] = Field(..., min_items=128, max_items=128, description="128-dimensional biometric face descriptor captured from camera")
    threshold: Optional[float] = Field(0.52, description="Maximum Euclidean distance threshold for a positive face match")


class FaceUserResponse(BaseModel):
    id: str
    name: str
    email: str
    username: Optional[str] = None
    role: Optional[str] = "user"
    is_active: Optional[bool] = True
    is_admin: Optional[bool] = False
    face_enrolled_at: Optional[datetime] = None
    last_login_at: Optional[datetime] = None
    created_at: datetime


class FaceAuthResponse(BaseModel):
    success: bool
    message: str
    token: Optional[str] = None
    distance: Optional[float] = None
    confidence_pct: Optional[float] = None
    user: Optional[FaceUserResponse] = None
