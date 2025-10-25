from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class ProductStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"

class StockStatus(str, Enum):
    IN_STOCK = "in_stock"
    LOW_STOCK = "low_stock"
    OUT_OF_STOCK = "out_of_stock"
    ON_BACKORDER = "on_backorder"

class ProductType(str, Enum):
    SIMPLE = "simple"
    VARIABLE = "variable"
    DIGITAL = "digital"

class ProductBase(BaseModel):
    name: str
    sku: str
    slug: str
    short_description: Optional[str] = None
    description: Optional[str] = None
    base_price: float
    compare_price: Optional[float] = None
    category_id: int
    brand_id: Optional[int] = None

class ProductCreate(ProductBase):
    specification: Optional[Dict[str, Any]] = None
    gst_rate: float = 18.0
    track_inventory: bool = True
    stock_quantity: int = 0
    product_type: ProductType = ProductType.SIMPLE
    is_featured: bool = False

class ProductResponse(ProductBase):
    id: int
    uuid: str
    specification: Optional[Dict[str, Any]] = None
    gst_rate: float
    is_gst_inclusive: bool
    track_inventory: bool
    stock_quantity: int
    low_stock_threshold: int
    stock_status: StockStatus
    product_type: ProductType
    weight_grams: Optional[float] = None
    main_image_url: Optional[str] = None
    image_gallery: Optional[List[str]] = None
    status: ProductStatus
    is_featured: bool
    is_trending: bool
    is_bestseller: bool
    view_count: int
    wishlist_count: int
    total_sold: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class CategoryResponse(BaseModel):
    id: int
    uuid: str
    name: str
    slug: str
    description: Optional[str] = None
    parent_id: Optional[int] = None
    image_url: Optional[str] = None
    is_active: bool
    sort_order: int

    class Config:
        from_attributes = True

class BrandResponse(BaseModel):
    id: int
    uuid: str
    name: str
    slug: str
    description: Optional[str] = None
    logo_url: Optional[str] = None
    is_active: bool

    class Config:
        from_attributes = True

class ProductSearch(BaseModel):
    query: Optional[str] = None
    category_id: Optional[int] = None
    brand_id: Optional[int] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    in_stock: Optional[bool] = None
    is_featured: Optional[bool] = None
    page: int = 1
    page_size: int = 20

class ProductListResponse(BaseModel):
    products: List[ProductResponse]
    total_count: int
    page: int
    page_size: int
    total_pages: int

class HealthResponse(BaseModel):
    status: str
    service: str
    products_count: int
    categories_count: int
    timestamp: datetime
