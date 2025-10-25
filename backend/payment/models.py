from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum

class PaymentStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"

class PaymentAuthStatus(str, Enum):
    PENDING = "pending"
    AUTHORIZED = "authorized"
    CAPTURED = "captured"
    FAILED = "failed"

class PaymentMethod(str, Enum):
    CREDIT_CARD = "credit_card"
    DEBIT_CARD = "debit_card"
    UPI = "upi"
    NETBANKING = "netbanking"
    CASH_ON_DELIVERY = "cash_on_delivery"
    WALLET = "wallet"

class PaymentGateway(str, Enum):
    RAZORPAY = "razorpay"
    STRIPE = "stripe"
    PAYPAL = "paypal"
    CASH = "cash"

class PaymentCreate(BaseModel):
    order_id: int
    amount: float
    currency: str = "INR"
    payment_method: PaymentMethod
    gateway: PaymentGateway

class PaymentResponse(BaseModel):
    id: int
    uuid: str
    order_id: int
    user_id: int
    amount: float
    currency: str
    payment_method: str
    gateway_name: str
    gateway_transaction_id: Optional[str] = None
    gateway_order_id: Optional[str] = None
    status: PaymentStatus
    payment_status: PaymentAuthStatus
    failure_reason: Optional[str] = None
    initiated_at: datetime
    authorized_at: Optional[datetime] = None
    captured_at: Optional[datetime] = None
    failed_at: Optional[datetime] = None
    refunded_at: Optional[datetime] = None
    refund_amount: float = 0.0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class PaymentInitiateResponse(BaseModel):
    payment_id: int
    gateway_order_id: Optional[str] = None
    razorpay_order_id: Optional[str] = None
    razorpay_key: Optional[str] = None
    amount: float
    currency: str
    callback_url: str
    payment_page_url: Optional[str] = None

class PaymentVerifyRequest(BaseModel):
    payment_id: int
    gateway_signature: Optional[str] = None
    gateway_order_id: Optional[str] = None
    gateway_transaction_id: Optional[str] = None
    upi_id: Optional[str] = None

class RefundCreate(BaseModel):
    payment_id: int
    amount: float
    reason: str

class RefundResponse(BaseModel):
    id: int
    payment_id: int
    amount: float
    reason: str
    status: str
    gateway_refund_id: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class PaymentMethodResponse(BaseModel):
    id: int
    method_type: str
    is_default: bool
    upi_id: Optional[str] = None
    upi_app: Optional[str] = None
    card_last_four: Optional[str] = None
    card_type: Optional[str] = None
    card_network: Optional[str] = None
    bank_name: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class HealthResponse(BaseModel):
    status: str
    service: str
    payments_count: int
    timestamp: datetime
