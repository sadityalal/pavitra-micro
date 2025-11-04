import re

from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum
import ipaddress


class SessionType(str, Enum):
    GUEST = "guest"
    USER = "user"


class SessionData(BaseModel):
    session_id: str = Field(..., min_length=32, max_length=64)
    session_type: SessionType
    user_id: Optional[int] = Field(None, ge=1)
    guest_id: Optional[str] = Field(None, min_length=8, max_length=64)
    cart_items: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    last_activity: datetime
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    expires_at: datetime
    security_token: Optional[str] = None
    csrf_token: Optional[str] = None
    fingerprint: Optional[str] = None

    @validator('ip_address')
    def validate_ip_address(cls, v):
        if v and v != 'unknown':
            try:
                ipaddress.ip_address(v)
            except ValueError:
                raise ValueError('Invalid IP address format')
        return v

    @validator('session_id')
    def validate_session_id(cls, v):
        if not re.match(r'^[a-f0-9]{32,64}$', v):
            raise ValueError('Invalid session ID format')
        return v


class SessionCreate(BaseModel):
    session_type: SessionType
    user_id: Optional[int] = Field(None, ge=1)
    guest_id: Optional[str] = Field(None, min_length=8, max_length=64)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    security_token: Optional[str] = None


class SessionResponse(BaseModel):
    session_id: str
    session_type: SessionType
    user_id: Optional[int] = None
    guest_id: Optional[str] = None
    cart_items: Dict[str, Any] = {}
    created_at: datetime
    last_activity: datetime
    expires_at: datetime