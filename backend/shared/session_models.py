from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum

class SessionType(str, Enum):
    GUEST = "guest"
    USER = "user"

class SessionData(BaseModel):
    session_id: str
    session_type: SessionType
    user_id: Optional[int] = None
    guest_id: Optional[str] = None
    cart_items: Dict[str, Any] = {}
    created_at: datetime
    last_activity: datetime
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    expires_at: datetime

class SessionCreate(BaseModel):
    session_type: SessionType
    user_id: Optional[int] = None
    guest_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

class SessionResponse(BaseModel):
    session_id: str
    session_type: SessionType
    user_id: Optional[int] = None
    guest_id: Optional[str] = None
    cart_items: Dict[str, Any] = {}
    created_at: datetime
    last_activity: datetime
    expires_at: datetime