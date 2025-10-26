from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class NotificationType(str, Enum):
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    TELEGRAM = "telegram"
    WHATSAPP = "whatsapp"

class NotificationStatus(str, Enum):
    SENT = "sent"
    FAILED = "failed"
    PENDING = "pending"

class NotificationTemplate(str, Enum):
    WELCOME_EMAIL = "welcome_email"
    ORDER_CONFIRMATION = "order_confirmation"
    ORDER_SHIPPED = "order_shipped"
    ORDER_DELIVERED = "order_delivered"
    PAYMENT_RECEIVED = "payment_received"
    PAYMENT_FAILED = "payment_failed"
    PASSWORD_RESET = "password_reset"
    ACCOUNT_VERIFICATION = "account_verification"
    PROMOTIONAL = "promotional"
    SECURITY_ALERT = "security_alert"
    ORDER_CANCELLED = "order_cancelled"
    REFUND_PROCESSED = "refund_processed"

class EmailNotification(BaseModel):
    to_email: str
    subject: str
    template_name: NotificationTemplate
    template_data: Dict[str, Any]
    cc_emails: Optional[List[str]] = None
    bcc_emails: Optional[List[str]] = None

class SMSNotification(BaseModel):
    to_phone: str
    message: str
    template_name: Optional[NotificationTemplate] = None

class PushNotification(BaseModel):
    to_user_id: int
    title: str
    message: str
    data: Optional[Dict[str, Any]] = None
    image_url: Optional[str] = None

class TelegramNotification(BaseModel):
    to_chat_id: str
    message: str
    template_name: Optional[NotificationTemplate] = None
    parse_mode: Optional[str] = "HTML"

class WhatsAppNotification(BaseModel):
    to_phone: str
    message: str
    template_name: Optional[NotificationTemplate] = None

class NotificationResponse(BaseModel):
    id: int
    type: NotificationType
    recipient: str
    subject: Optional[str] = None
    message: Optional[str] = None
    status: NotificationStatus
    template_name: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class NotificationStats(BaseModel):
    total_sent: int
    total_failed: int
    email_sent: int
    sms_sent: int
    push_sent: int
    telegram_sent: int
    whatsapp_sent: int
    last_24_hours: int

class HealthResponse(BaseModel):
    status: str
    service: str
    notifications_count: int
    timestamp: datetime

class NotificationSettings(BaseModel):
    email_enabled: bool
    sms_enabled: bool
    push_enabled: bool
    telegram_enabled: bool
    whatsapp_enabled: bool
    telegram_bot_token: Optional[str] = None
    telegram_chat_id: Optional[str] = None
    whatsapp_api_url: Optional[str] = None
    whatsapp_api_token: Optional[str] = None
