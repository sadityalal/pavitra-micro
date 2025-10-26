from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
from decimal import Decimal


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
    product_id: int = Field(..., gt=0)
    variation_id: Optional[int] = Field(None, gt=0)
    quantity: int = Field(..., gt=0, le=100)
    unit_price: Decimal = Field(..., ge=0)


class OrderCreate(BaseModel):
    items: List[OrderItemBase] = Field(..., min_items=1)
    shipping_address: Dict[str, Any]
    billing_address: Optional[Dict[str, Any]] = None
    payment_method: PaymentMethod
    customer_note: Optional[str] = Field(None, max_length=500)
    use_gst_invoice: bool = True
    gst_number: Optional[str] = Field(None, pattern=r'^[0-9A-Z]{15}$')


class OrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    uuid: str
    order_number: str
    user_id: int
    subtotal: Decimal
    shipping_amount: Decimal
    tax_amount: Decimal
    discount_amount: Decimal
    total_amount: Decimal
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


class OrderItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: int
    variation_id: Optional[int] = None
    product_name: str
    product_sku: str
    product_image: Optional[str] = None
    unit_price: Decimal
    quantity: int
    total_price: Decimal
    gst_rate: Decimal
    gst_amount: Decimal
    variation_attributes: Optional[Dict[str, Any]] = None


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


class OrderStatusUpdate(BaseModel):
    status: OrderStatus
    admin_note: Optional[str] = Field(None, max_length=500)


class OrderCancelRequest(BaseModel):
    reason: str = Field(..., max_length=500)