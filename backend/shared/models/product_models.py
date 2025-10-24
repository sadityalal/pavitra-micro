from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime

class CategoryBase(BaseModel):
    name: str
    slug: str
    description: Optional[str] = None
    parent_id: Optional[int] = None
    is_active: bool = True

class CategoryResponse(CategoryBase):
    id: int
    uuid: str
    image_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ProductBase(BaseModel):
    name: str
    slug: str
    sku: str
    short_description: Optional[str] = None
    description: Optional[str] = None
    base_price: float
    compare_price: Optional[float] = None
    stock_quantity: int = 0
    category_id: int
    brand_id: Optional[int] = None

class ProductCreate(ProductBase):
    pass

class ProductResponse(ProductBase):
    id: int
    uuid: str
    main_image_url: Optional[str] = None
    image_gallery: Optional[List[str]] = None
    specification: Optional[Dict] = None
    is_featured: bool = False
    is_active: bool = True
    status: str = "active"
    view_count: int = 0
    wishlist_count: int = 0
    total_sold: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ProductSearch(BaseModel):
    query: Optional[str] = None
    category: Optional[str] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    in_stock: Optional[bool] = None
    featured: Optional[bool] = None
