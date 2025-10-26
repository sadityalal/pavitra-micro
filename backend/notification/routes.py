from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, status, Request
from typing import List, Optional
from shared import config, db, sanitize_input, get_logger, redis_client
from shared.auth_middleware import get_current_user
from .models import (
    EmailNotification, SMSNotification, PushNotification,
    TelegramNotification, WhatsAppNotification,
    NotificationResponse, NotificationStats, HealthResponse,
    NotificationSettings, NotificationType, NotificationStatus
)
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import json
import requests

router = APIRouter()
logger = get_logger(__name__)

def require_roles(required_roles: List[str]):
    def role_dependency(current_user: dict = Depends(get_current_user)):
        user_roles = current_user.get('roles', [])
        if not any(role in user_roles for role in required_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient role permissions"
            )
        return current_user
    return role_dependency

class EmailService:
    def __init__(self):
        self.smtp_host = config.smtp_host
        self.smtp_port = config.smtp_port
        self.smtp_username = config.smtp_username
        self.smtp_password = config.smtp_password
        self.email_from = config.email_from
        self.email_from_name = getattr(config, 'email_from_name', 'Pavitra Trading')

    def send_email(self, to_email: str, subject: str, html_content: str, text_content: str = None) -> bool:
        try:
            if not all([self.smtp_host, self.smtp_username, self.smtp_password]):
                logger.warning("SMTP configuration missing, email not sent")
                return False

            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{self.email_from_name} <{self.email_from}>"
            msg['To'] = to_email

            if text_content:
                text_part = MIMEText(text_content, 'plain')
                msg.attach(text_part)

            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)

            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)

            logger.info(f"Email sent successfully to {to_email}")
            return True
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False

class SMSService:
    def __init__(self):
        self.enabled = getattr(config, 'sms_notifications', False)

    def send_sms(self, to_phone: str, message: str) -> bool:
        try:
            if not self.enabled:
                logger.info(f"SMS notifications disabled, would send to {to_phone}: {message}")
                return True

            # Placeholder for SMS gateway integration
            # In production, integrate with services like Twilio, MSG91, etc.
            logger.info(f"SMS to {to_phone}: {message}")
            return True
        except Exception as e:
            logger.error(f"Failed to send SMS to {to_phone}: {e}")
            return False

class PushService:
    def __init__(self):
        self.enabled = getattr(config, 'push_notifications', False)

    def send_push(self, to_user_id: int, title: str, message: str, data: dict = None) -> bool:
        try:
            if not self.enabled:
                logger.info(f"Push notifications disabled, would send to user {to_user_id}: {title} - {message}")
                return True

            # Placeholder for push notification service (Firebase, OneSignal, etc.)
            logger.info(f"Push to user {to_user_id}: {title} - {message}")
            return True
        except Exception as e:
            logger.error(f"Failed to send push to user {to_user_id}: {e}")
            return False

class TelegramService:
    def __init__(self):
        self.enabled = getattr(config, 'telegram_notifications', False)
        self.bot_token = getattr(config, 'telegram_bot_token', None)
        self.default_chat_id = getattr(config, 'telegram_chat_id', None)

    def send_message(self, to_chat_id: str, message: str, parse_mode: str = "HTML") -> bool:
        try:
            if not self.enabled or not self.bot_token:
                logger.info(f"Telegram notifications disabled or bot token missing")
                return False

            chat_id = to_chat_id or self.default_chat_id
            if not chat_id:
                logger.error("No chat ID provided for Telegram message")
                return False

            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            payload = {
                'chat_id': chat_id,
                'text': message,
                'parse_mode': parse_mode
            }

            response = requests.post(url, json=payload, timeout=10)
            if response.status_code == 200:
                logger.info(f"Telegram message sent successfully to {chat_id}")
                return True
            else:
                logger.error(f"Telegram API error: {response.status_code} - {response.text}")
                return False

        except Exception as e:
            logger.error(f"Failed to send Telegram message: {e}")
            return False

class WhatsAppService:
    def __init__(self):
        self.enabled = getattr(config, 'whatsapp_notifications', False)
        self.api_url = getattr(config, 'whatsapp_api_url', None)
        self.api_token = getattr(config, 'whatsapp_api_token', None)

    def send_message(self, to_phone: str, message: str) -> bool:
        try:
            if not self.enabled or not self.api_url or not self.api_token:
                logger.info(f"WhatsApp notifications disabled or configuration missing")
                return False

            # Placeholder for WhatsApp Business API integration
            # In production, integrate with WhatsApp Business API or services like Twilio WhatsApp
            logger.info(f"WhatsApp to {to_phone}: {message}")
            return True
        except Exception as e:
            logger.error(f"Failed to send WhatsApp message: {e}")
            return False

# Initialize services
email_service = EmailService()
sms_service = SMSService()
push_service = PushService()
telegram_service = TelegramService()
whatsapp_service = WhatsAppService()

def log_notification(notification_type: str, recipient: str, subject: str = None,
                    message: str = None, template_name: str = None, status: str = "sent"):
    try:
        with db.get_cursor() as cursor:
            cursor.execute("""
                INSERT INTO notification_logs (type, recipient, subject, message, status, template_name)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (notification_type, recipient, subject, message, status, template_name))
    except Exception as e:
        logger.error(f"Failed to log notification: {e}")

def get_email_template(template_name: str, template_data: dict) -> tuple:
    templates = {
        "welcome_email": {
            "subject": "Welcome to {app_name}!",
            "html": """
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; }
                    .container { max-width: 600px; margin: 0 auto; padding: 20px; background: #ffffff; }
                    .header { background: #4CAF50; color: white; padding: 20px; text-align: center; border-radius: 5px 5px 0 0; }
                    .content { padding: 20px; background: #f9f9f9; border-radius: 0 0 5px 5px; }
                    .footer { padding: 20px; text-align: center; font-size: 12px; color: #666; border-top: 1px solid #eee; }
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>Welcome to {app_name}!</h1>
                    </div>
                    <div class="content">
                        <p>Hello {first_name},</p>
                        <p>Thank you for joining {app_name}. We're excited to have you as a member!</p>
                        <p>Start exploring our products and enjoy a seamless shopping experience.</p>
                        <p>If you have any questions, feel free to contact our support team.</p>
                    </div>
                    <div class="footer">
                        <p>&copy; {current_year} {app_name}. All rights reserved.</p>
                    </div>
                </div>
            </body>
            </html>
            """
        },
        "order_confirmation": {
            "subject": "Order Confirmation - {order_number}",
            "html": """
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; }
                    .container { max-width: 600px; margin: 0 auto; padding: 20px; background: #ffffff; }
                    .header { background: #4CAF50; color: white; padding: 20px; text-align: center; border-radius: 5px 5px 0 0; }
                    .content { padding: 20px; background: #f9f9f9; border-radius: 0 0 5px 5px; }
                    .order-info { background: white; padding: 15px; border: 1px solid #ddd; border-radius: 5px; margin: 15px 0; }
                    .footer { padding: 20px; text-align: center; font-size: 12px; color: #666; border-top: 1px solid #eee; }
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>Order Confirmed!</h1>
                    </div>
                    <div class="content">
                        <p>Hello {customer_name},</p>
                        <p>Thank you for your order. We're getting it ready for you.</p>
                        <div class="order-info">
                            <h3>Order Details</h3>
                            <p><strong>Order Number:</strong> {order_number}</p>
                            <p><strong>Order Date:</strong> {order_date}</p>
                            <p><strong>Total Amount:</strong> {currency_symbol}{total_amount}</p>
                        </div>
                        <p>We'll notify you when your order ships.</p>
                    </div>
                    <div class="footer">
                        <p>&copy; {current_year} {app_name}. All rights reserved.</p>
                    </div>
                </div>
            </body>
            </html>
            """
        },
        "password_reset": {
            "subject": "Password Reset Request",
            "html": """
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; }
                    .container { max-width: 600px; margin: 0 auto; padding: 20px; background: #ffffff; }
                    .header { background: #ff6b6b; color: white; padding: 20px; text-align: center; border-radius: 5px 5px 0 0; }
                    .content { padding: 20px; background: #f9f9f9; border-radius: 0 0 5px 5px; }
                    .button { background: #4CAF50; color: white; padding: 12px 24px; text-decoration: none; border-radius: 4px; display: inline-block; }
                    .footer { padding: 20px; text-align: center; font-size: 12px; color: #666; border-top: 1px solid #eee; }
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>Password Reset</h1>
                    </div>
                    <div class="content">
                        <p>Hello,</p>
                        <p>We received a request to reset your password for your {app_name} account.</p>
                        <p>Click the button below to reset your password:</p>
                        <p style="text-align: center;">
                            <a href="{reset_url}" class="button">Reset Password</a>
                        </p>
                        <p>This link will expire in 1 hour.</p>
                        <p>If you didn't request this, please ignore this email.</p>
                    </div>
                    <div class="footer">
                        <p>&copy; {current_year} {app_name}. All rights reserved.</p>
                    </div>
                </div>
            </body>
            </html>
            """
        }
    }

    template = templates.get(template_name, templates["welcome_email"])
    # Replace template variables
    template_data.update({
        "app_name": config.app_name,
        "current_year": datetime.now().year,
        "currency_symbol": config.currency_symbol
    })
    subject = template["subject"].format(**template_data)
    html_content = template["html"].format(**template_data)
    return subject, html_content

@router.get("/health", response_model=HealthResponse)
async def health():
    try:
        with db.get_cursor() as cursor:
            cursor.execute("SELECT COUNT(*) as count FROM notification_logs")
            notifications_count = cursor.fetchone()['count']
            return HealthResponse(
                status="healthy",
                service="notification",
                notifications_count=notifications_count,
                timestamp=datetime.utcnow()
            )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthResponse(
            status="unhealthy",
            service="notification",
            notifications_count=0,
            timestamp=datetime.utcnow()
        )

@router.post("/email")
async def send_email_notification(
    email_data: EmailNotification,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
):
    try:
        # Get template content
        subject, html_content = get_email_template(
            email_data.template_name.value,
            email_data.template_data
        )

        # Send email in background
        background_tasks.add_task(
            send_email_background,
            email_data.to_email,
            subject,
            html_content,
            email_data.template_name.value
        )

        logger.info(f"Email notification queued for {email_data.to_email}")
        return {
            "success": True,
            "message": "Email notification queued successfully",
            "recipient": email_data.to_email
        }
    except Exception as e:
        logger.error(f"Failed to queue email notification: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send email notification"
        )

def send_email_background(to_email: str, subject: str, html_content: str, template_name: str):
    try:
        success = email_service.send_email(to_email, subject, html_content)
        status = "sent" if success else "failed"
        log_notification(
            notification_type="email",
            recipient=to_email,
            subject=subject,
            message=html_content[:500],
            template_name=template_name,
            status=status
        )
    except Exception as e:
        logger.error(f"Background email sending failed: {e}")
        log_notification(
            notification_type="email",
            recipient=to_email,
            subject=subject,
            template_name=template_name,
            status="failed"
        )

@router.post("/sms")
async def send_sms_notification(
    sms_data: SMSNotification,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
):
    try:
        # Send SMS in background
        background_tasks.add_task(
            send_sms_background,
            sms_data.to_phone,
            sms_data.message,
            sms_data.template_name.value if sms_data.template_name else None
        )

        logger.info(f"SMS notification queued for {sms_data.to_phone}")
        return {
            "success": True,
            "message": "SMS notification queued successfully",
            "recipient": sms_data.to_phone
        }
    except Exception as e:
        logger.error(f"Failed to queue SMS notification: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send SMS notification"
        )

def send_sms_background(to_phone: str, message: str, template_name: str = None):
    try:
        success = sms_service.send_sms(to_phone, message)
        status = "sent" if success else "failed"
        log_notification(
            notification_type="sms",
            recipient=to_phone,
            message=message,
            template_name=template_name,
            status=status
        )
    except Exception as e:
        logger.error(f"Background SMS sending failed: {e}")
        log_notification(
            notification_type="sms",
            recipient=to_phone,
            template_name=template_name,
            status="failed"
        )

@router.post("/push")
async def send_push_notification(
    push_data: PushNotification,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
):
    try:
        # Send push in background
        background_tasks.add_task(
            send_push_background,
            push_data.to_user_id,
            push_data.title,
            push_data.message,
            push_data.data
        )

        logger.info(f"Push notification queued for user {push_data.to_user_id}")
        return {
            "success": True,
            "message": "Push notification queued successfully",
            "recipient": f"user_{push_data.to_user_id}"
        }
    except Exception as e:
        logger.error(f"Failed to queue push notification: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send push notification"
        )

def send_push_background(to_user_id: int, title: str, message: str, data: dict = None):
    try:
        success = push_service.send_push(to_user_id, title, message, data)
        status = "sent" if success else "failed"
        log_notification(
            notification_type="push",
            recipient=f"user_{to_user_id}",
            subject=title,
            message=message,
            status=status
        )
    except Exception as e:
        logger.error(f"Background push sending failed: {e}")
        log_notification(
            notification_type="push",
            recipient=f"user_{to_user_id}",
            subject=title,
            status="failed"
        )

@router.post("/telegram")
async def send_telegram_notification(
    telegram_data: TelegramNotification,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(require_roles(["admin", "super_admin"]))
):
    try:
        # Send telegram in background
        background_tasks.add_task(
            send_telegram_background,
            telegram_data.to_chat_id,
            telegram_data.message,
            telegram_data.template_name.value if telegram_data.template_name else None,
            telegram_data.parse_mode
        )

        logger.info(f"Telegram notification queued for chat {telegram_data.to_chat_id}")
        return {
            "success": True,
            "message": "Telegram notification queued successfully",
            "recipient": f"chat_{telegram_data.to_chat_id}"
        }
    except Exception as e:
        logger.error(f"Failed to queue telegram notification: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send telegram notification"
        )

def send_telegram_background(to_chat_id: str, message: str, template_name: str = None, parse_mode: str = "HTML"):
    try:
        success = telegram_service.send_message(to_chat_id, message, parse_mode)
        status = "sent" if success else "failed"
        log_notification(
            notification_type="telegram",
            recipient=to_chat_id,
            message=message,
            template_name=template_name,
            status=status
        )
    except Exception as e:
        logger.error(f"Background telegram sending failed: {e}")
        log_notification(
            notification_type="telegram",
            recipient=to_chat_id,
            template_name=template_name,
            status="failed"
        )

@router.post("/whatsapp")
async def send_whatsapp_notification(
    whatsapp_data: WhatsAppNotification,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(require_roles(["admin", "super_admin"]))
):
    try:
        # Send whatsapp in background
        background_tasks.add_task(
            send_whatsapp_background,
            whatsapp_data.to_phone,
            whatsapp_data.message,
            whatsapp_data.template_name.value if whatsapp_data.template_name else None
        )

        logger.info(f"WhatsApp notification queued for {whatsapp_data.to_phone}")
        return {
            "success": True,
            "message": "WhatsApp notification queued successfully",
            "recipient": whatsapp_data.to_phone
        }
    except Exception as e:
        logger.error(f"Failed to queue WhatsApp notification: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send WhatsApp notification"
        )

def send_whatsapp_background(to_phone: str, message: str, template_name: str = None):
    try:
        success = whatsapp_service.send_message(to_phone, message)
        status = "sent" if success else "failed"
        log_notification(
            notification_type="whatsapp",
            recipient=to_phone,
            message=message,
            template_name=template_name,
            status=status
        )
    except Exception as e:
        logger.error(f"Background WhatsApp sending failed: {e}")
        log_notification(
            notification_type="whatsapp",
            recipient=to_phone,
            template_name=template_name,
            status="failed"
        )

@router.get("/logs", response_model=List[NotificationResponse])
async def get_notification_logs(
    notification_type: Optional[NotificationType] = None,
    recipient: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    current_user: dict = Depends(require_roles(["admin", "super_admin"]))
):
    try:
        with db.get_cursor() as cursor:
            query_conditions = ["1=1"]
            query_params = []
            if notification_type:
                query_conditions.append("type = %s")
                query_params.append(notification_type.value)
            if recipient:
                query_conditions.append("recipient LIKE %s")
                query_params.append(f"%{sanitize_input(recipient)}%")

            where_clause = " AND ".join(query_conditions)
            offset = (page - 1) * page_size

            cursor.execute(f"""
                SELECT * FROM notification_logs
                WHERE {where_clause}
                ORDER BY created_at DESC
                LIMIT %s OFFSET %s
            """, query_params + [page_size, offset])
            logs = cursor.fetchall()

            return [
                NotificationResponse(
                    id=log['id'],
                    type=log['type'],
                    recipient=log['recipient'],
                    subject=log['subject'],
                    message=log['message'],
                    status=log['status'],
                    template_name=log['template_name'],
                    created_at=log['created_at']
                )
                for log in logs
            ]
    except Exception as e:
        logger.error(f"Failed to fetch notification logs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch notification logs"
        )

@router.get("/stats", response_model=NotificationStats)
async def get_notification_stats(
    days: int = 7,
    current_user: dict = Depends(require_roles(["admin", "super_admin"]))
):
    try:
        with db.get_cursor() as cursor:
            # Total counts
            cursor.execute("SELECT COUNT(*) as total FROM notification_logs")
            total_count = cursor.fetchone()['total']

            cursor.execute("SELECT COUNT(*) as failed FROM notification_logs WHERE status = 'failed'")
            failed_count = cursor.fetchone()['failed']

            # Count by type
            cursor.execute("SELECT COUNT(*) as count FROM notification_logs WHERE type = 'email'")
            email_count = cursor.fetchone()['count']

            cursor.execute("SELECT COUNT(*) as count FROM notification_logs WHERE type = 'sms'")
            sms_count = cursor.fetchone()['count']

            cursor.execute("SELECT COUNT(*) as count FROM notification_logs WHERE type = 'push'")
            push_count = cursor.fetchone()['count']

            cursor.execute("SELECT COUNT(*) as count FROM notification_logs WHERE type = 'telegram'")
            telegram_count = cursor.fetchone()['count']

            cursor.execute("SELECT COUNT(*) as count FROM notification_logs WHERE type = 'whatsapp'")
            whatsapp_count = cursor.fetchone()['count']

            # Last 24 hours
            cursor.execute("""
                SELECT COUNT(*) as count FROM notification_logs
                WHERE created_at >= NOW() - INTERVAL 1 DAY
            """)
            last_24_hours = cursor.fetchone()['count']

            return NotificationStats(
                total_sent=total_count - failed_count,
                total_failed=failed_count,
                email_sent=email_count,
                sms_sent=sms_count,
                push_sent=push_count,
                telegram_sent=telegram_count,
                whatsapp_sent=whatsapp_count,
                last_24_hours=last_24_hours
            )
    except Exception as e:
        logger.error(f"Failed to fetch notification stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch notification statistics"
        )

@router.get("/settings", response_model=NotificationSettings)
async def get_notification_settings(
    current_user: dict = Depends(require_roles(["admin", "super_admin"]))
):
    try:
        return NotificationSettings(
            email_enabled=getattr(config, 'email_notifications', True),
            sms_enabled=getattr(config, 'sms_notifications', False),
            push_enabled=getattr(config, 'push_notifications', False),
            telegram_enabled=getattr(config, 'telegram_notifications', False),
            whatsapp_enabled=getattr(config, 'whatsapp_notifications', False),
            telegram_bot_token=getattr(config, 'telegram_bot_token', None),
            telegram_chat_id=getattr(config, 'telegram_chat_id', None),
            whatsapp_api_url=getattr(config, 'whatsapp_api_url', None),
            whatsapp_api_token=getattr(config, 'whatsapp_api_token', None)
        )
    except Exception as e:
        logger.error(f"Failed to fetch notification settings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch notification settings"
        )

@router.post("/test/email")
async def test_email_notification(
    email: str,
    current_user: dict = Depends(require_roles(["admin", "super_admin"]))
):
    try:
        subject = "Test Email from Pavitra Trading"
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
                .container { max-width: 600px; margin: 0 auto; padding: 20px; }
                .header { background: #4CAF50; color: white; padding: 20px; text-align: center; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Test Email</h1>
                </div>
                <p>This is a test email from Pavitra Trading notification service.</p>
                <p>If you received this email, your email configuration is working correctly.</p>
            </div>
        </body>
        </html>
        """

        success = email_service.send_email(email, subject, html_content)
        if success:
            return {"success": True, "message": "Test email sent successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send test email"
            )
    except Exception as e:
        logger.error(f"Test email failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send test email"
        )

@router.get("/debug/test")
async def debug_test():
    import traceback
    try:
        from shared import config, db, get_logger
        logger = get_logger(__name__)

        maintenance_mode = config.maintenance_mode
        debug_mode = config.debug_mode

        db_status = "unknown"
        notification_count = 0
        
        try:
            with db.get_cursor() as cursor:
                cursor.execute("SELECT 1 as test")
                db_status = "connected"
                cursor.execute("SELECT COUNT(*) as count FROM notification_logs")
                notification_count = cursor.fetchone()['count']
        except Exception as db_error:
            db_status = f"error: {str(db_error)}"
            logger.error(f"Database error: {db_error}")

        redis_status = "unknown"
        try:
            from shared.redis_client import redis_client
            redis_status = "connected" if redis_client._ensure_connection() else "disconnected"
        except Exception as redis_error:
            redis_status = f"error: {str(redis_error)}"

        return {
            "status": "ok",
            "maintenance_mode": maintenance_mode,
            "debug_mode": debug_mode,
            "database": db_status,
            "notification_count": notification_count,
            "redis": redis_status,
            "service": "notification",
            "email_config": {
                "smtp_host": bool(config.smtp_host),
                "smtp_username": bool(config.smtp_username),
                "smtp_password": bool(config.smtp_password)
            }
        }
    except Exception as e:
        error_traceback = traceback.format_exc()
        return {
            "status": "error",
            "error_type": type(e).__name__,
            "error_message": str(e),
            "traceback": error_traceback,
            "service": "notification"
        }
