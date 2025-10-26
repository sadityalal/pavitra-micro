from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from enum import Enum

class AuthType(str, Enum):
    EMAIL = "email"
    MOBILE = "mobile"
    USERNAME = "username"

class UserRole(str, Enum):
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    CUSTOMER = "customer"
    VENDOR = "vendor"
    CONTENT_MANAGER = "content_manager"
    SUPPORT_STAFF = "support_staff"

class UserBase(BaseModel):
    first_name: str
    last_name: str
    phone: Optional[str] = None
    username: Optional[str] = None
    country_id: Optional[int] = None

class UserCreate(UserBase):
    email: Optional[str] = None
    mobile: Optional[str] = None
    password: str
    auth_type: AuthType

class UserResponse(UserBase):
    id: int
    uuid: str
    email: Optional[str] = None
    mobile: Optional[str] = None
    email_verified: bool
    phone_verified: bool
    is_active: bool
    roles: List[str] = []
    permissions: List[str] = []
    country_id: Optional[int]
    preferred_currency: str = "INR"
    preferred_language: str = "en"
    avatar_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class UserLogin(BaseModel):
    login_id: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    user_roles: List[str] = []
    user_permissions: List[str] = []

class RoleResponse(BaseModel):
    id: int
    name: str
    description: str
    permissions: List[str] = []

    class Config:
        from_attributes = True

class PermissionCheck(BaseModel):
    permission: str
    has_access: bool

class HealthResponse(BaseModel):
    status: str
    service: str
    environment: str
    users_count: int
    timestamp: datetime