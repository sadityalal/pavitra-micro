from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class NotificationType(str, Enum):
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"

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
    PASSWORD_RESET = "password_reset"
    ACCOUNT_VERIFICATION = "account_verification"
    PROMOTIONAL = "promotional"
    SECURITY_ALERT = "security_alert"

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
    last_24_hours: int

class HealthResponse(BaseModel):
    status: str
    service: str
    notifications_count: int
    timestamp: datetime
