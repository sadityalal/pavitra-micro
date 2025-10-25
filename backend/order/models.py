from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class OrderStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"

class PaymentStatus(str, Enum):
    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"
    REFUNDED = "refunded"
    PARTIALLY_REFUNDED = "partially_refunded"

class PaymentMethod(str, Enum):
    CREDIT_CARD = "credit_card"
    DEBIT_CARD = "debit_card"
    UPI = "upi"
    NETBANKING = "netbanking"
    CASH_ON_DELIVERY = "cash_on_delivery"
    WALLET = "wallet"

class OrderItemBase(BaseModel):
    product_id: int
    variation_id: Optional[int] = None
    quantity: int
    unit_price: float

class OrderCreate(BaseModel):
    items: List[OrderItemBase]
    shipping_address: Dict[str, Any]
    billing_address: Optional[Dict[str, Any]] = None
    payment_method: PaymentMethod
    customer_note: Optional[str] = None
    use_gst_invoice: bool = True
    gst_number: Optional[str] = None

class OrderResponse(BaseModel):
    id: int
    uuid: str
    order_number: str
    user_id: int
    subtotal: float
    shipping_amount: float
    tax_amount: float
    discount_amount: float
    total_amount: float
    status: OrderStatus
    payment_status: PaymentStatus
    payment_method: PaymentMethod
    shipping_address: Dict[str, Any]
    billing_address: Optional[Dict[str, Any]] = None
    customer_note: Optional[str] = None
    is_gst_invoice: bool
    gst_number: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class OrderItemResponse(BaseModel):
    id: int
    product_id: int
    variation_id: Optional[int] = None
    product_name: str
    product_sku: str
    product_image: Optional[str] = None
    unit_price: float
    quantity: int
    total_price: float
    gst_rate: float
    gst_amount: float
    variation_attributes: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True

class OrderWithItemsResponse(OrderResponse):
    items: List[OrderItemResponse]

class OrderListResponse(BaseModel):
    orders: List[OrderResponse]
    total_count: int
    page: int
    page_size: int
    total_pages: int

class HealthResponse(BaseModel):
    status: str
    service: str
    orders_count: int
    timestamp: datetime
