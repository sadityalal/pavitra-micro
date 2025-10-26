from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class AddressType(str, Enum):
    SHIPPING = "shipping"
    BILLING = "billing"

class AddressDetailType(str, Enum):
    HOME = "home"
    WORK = "work"
    OTHER = "other"

class UserProfileBase(BaseModel):
    first_name: str
    last_name: str
    phone: Optional[str] = None
    username: Optional[str] = None
    country_id: Optional[int] = None
    preferred_currency: str = "INR"
    preferred_language: str = "en"

class UserProfileUpdate(UserProfileBase):
    date_of_birth: Optional[datetime] = None
    gender: Optional[str] = None

class UserProfileResponse(BaseModel):
    id: int
    uuid: str
    email: Optional[str] = None
    mobile: Optional[str] = None
    phone: Optional[str] = None
    username: Optional[str] = None
    first_name: str
    last_name: str
    email_verified: bool
    phone_verified: bool
    is_active: bool
    roles: List[str] = []
    permissions: List[str] = []
    country_id: Optional[int] = None
    preferred_currency: str = "INR"
    preferred_language: str = "en"
    avatar_url: Optional[str] = None
    date_of_birth: Optional[datetime] = None
    gender: Optional[str] = None
    last_login: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class AddressBase(BaseModel):
    address_type: AddressType = AddressType.SHIPPING
    full_name: str
    phone: str
    address_line1: str
    address_line2: Optional[str] = None
    landmark: Optional[str] = None
    city: str
    state: str
    country: str = "India"
    postal_code: str
    address_type_detail: AddressDetailType = AddressDetailType.HOME
    is_default: bool = False

class AddressCreate(AddressBase):
    pass

class AddressResponse(AddressBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class WishlistItemResponse(BaseModel):
    id: int
    product_id: int
    product_name: str
    product_slug: str
    product_image: Optional[str] = None
    product_price: float
    product_stock_status: str
    added_at: datetime

    class Config:
        from_attributes = True

class WishlistResponse(BaseModel):
    items: List[WishlistItemResponse]
    total_count: int

class CartItemResponse(BaseModel):
    id: int
    product_id: int
    variation_id: Optional[int] = None
    product_name: str
    product_slug: str
    product_image: Optional[str] = None
    product_price: float
    quantity: int
    total_price: float
    stock_quantity: int
    stock_status: str
    max_cart_quantity: int

    class Config:
        from_attributes = True

class CartResponse(BaseModel):
    items: List[CartItemResponse]
    subtotal: float
    total_items: int

class HealthResponse(BaseModel):
    status: str
    service: str
    users_count: int
    timestamp: datetime