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
    preferred_currency: str
    preferred_language: str
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

class AddressBase(BaseModel):
    address_type: str
    full_name: str
    phone: str
    address_line1: str
    address_line2: Optional[str] = None
    landmark: Optional[str] = None
    city: str
    state: str
    country: str = "India"
    postal_code: str
    is_default: bool = False

class AddressResponse(AddressBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class FileUploadResponse(BaseModel):
    file_id: int
    file_name: str
    file_path: str
    file_url: str
    file_size: int
    mime_type: str

class CountryResponse(BaseModel):
    id: int
    country_name: str
    country_code: str
    currency_code: str
    currency_symbol: str
    tax_type: str
    default_tax_rate: float

    class Config:
        from_attributes = True

class UserTaxInfo(BaseModel):
    tax_number: str
    tax_type: str
    business_name: Optional[str] = None
    business_address: Optional[str] = None

    class Config:
        from_attributes = True
