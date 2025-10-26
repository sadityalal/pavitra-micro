from pydantic import BaseModel, ConfigDict, field_validator
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum
import re

class PaymentStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"
    PARTIALLY_REFUNDED = "partially_refunded"

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
    CASH_ON_DELIVERY = "cash_on_delivery"

class SecureCardData(BaseModel):
    """Temporary model for card data - NEVER stored in DB"""
    number: str  # Will be tokenized immediately
    expiry_month: int
    expiry_year: int
    cvv: str  # Will be used once and discarded
    name: str
    save_card: bool = False  # Whether to save card for future use
    
    @field_validator('number')
    @classmethod
    def validate_card_number(cls, v):
        # Remove spaces and dashes
        v = re.sub(r'[\s-]', '', v)
        
        # Basic Luhn algorithm check
        def luhn_check(card_number):
            def digits_of(n):
                return [int(d) for d in str(n)]
            digits = digits_of(card_number)
            odd_digits = digits[-1::-2]
            even_digits = digits[-2::-2]
            checksum = sum(odd_digits)
            for d in even_digits:
                checksum += sum(digits_of(d*2))
            return checksum % 10 == 0
        
        if not v.isdigit() or not luhn_check(v):
            raise ValueError('Invalid card number')
        
        return v
    
    @field_validator('cvv')
    @classmethod
    def validate_cvv(cls, v):
        if not v.isdigit() or len(v) not in [3, 4]:
            raise ValueError('CVV must be 3 or 4 digits')
        return v
    
    @field_validator('expiry_month')
    @classmethod
    def validate_expiry_month(cls, v):
        if not 1 <= v <= 12:
            raise ValueError('Invalid expiry month')
        return v
    
    @field_validator('expiry_year')
    @classmethod
    def validate_expiry_year(cls, v):
        current_year = datetime.now().year
        if v < current_year or v > current_year + 20:
            raise ValueError('Invalid expiry year')
        return v

class PaymentCreate(BaseModel):
    order_id: int
    amount: float
    currency: str = "INR"
    payment_method: PaymentMethod
    gateway: PaymentGateway
    card_data: Optional[SecureCardData] = None  # Only for card payments, temporary
    upi_id: Optional[str] = None  # For UPI payments
    saved_payment_method_id: Optional[int] = None  # Use saved payment method
    
    @field_validator('amount')
    @classmethod
    def validate_amount(cls, v):
        if v <= 0:
            raise ValueError('Amount must be positive')
        return round(v, 2)

class PaymentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
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

class PaymentInitiateResponse(BaseModel):
    payment_id: int
    gateway_order_id: Optional[str] = None
    razorpay_order_id: Optional[str] = None
    razorpay_key: Optional[str] = None
    stripe_client_secret: Optional[str] = None
    amount: float
    currency: str
    callback_url: str
    payment_page_url: Optional[str] = None
    token: Optional[str] = None  # For secure card tokenization

class PaymentVerifyRequest(BaseModel):
    payment_id: int
    gateway_signature: Optional[str] = None
    gateway_order_id: Optional[str] = None
    gateway_transaction_id: Optional[str] = None
    upi_id: Optional[str] = None
    cvv: Optional[str] = None  # Only for saved card payments

class RefundCreate(BaseModel):
    payment_id: int
    amount: float
    reason: str

class RefundResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    payment_id: int
    amount: float
    reason: str
    status: str
    gateway_refund_id: Optional[str] = None
    created_at: datetime

class PaymentMethodResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    method_type: str
    is_default: bool
    upi_id: Optional[str] = None
    upi_app: Optional[str] = None
    card_last_four: Optional[str] = None
    card_type: Optional[str] = None
    card_network: Optional[str] = None
    bank_name: Optional[str] = None
    expiry_month: Optional[int] = None
    expiry_year: Optional[int] = None
    card_holder_name: Optional[str] = None
    created_at: datetime

class HealthResponse(BaseModel):
    status: str
    service: str
    payments_count: int
    timestamp: datetime
    gateway_status: Dict[str, bool] = {}

class SavePaymentMethodRequest(BaseModel):
    card_data: SecureCardData
    is_default: bool = False

class TokenizedPaymentRequest(BaseModel):
    order_id: int
    amount: float
    currency: str = "INR"
    payment_method: PaymentMethod
    gateway: PaymentGateway
    token: str  # Secure token from secure_payment_handler
    cvv: Optional[str] = None  # Only for card payments
