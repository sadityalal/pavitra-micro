from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, status
from typing import List, Optional
from shared import config, db, sanitize_input, get_logger
from .models import (
    EmailNotification, SMSNotification, PushNotification,
    NotificationResponse, NotificationStats, HealthResponse,
    NotificationType, NotificationStatus
)
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import json

router = APIRouter()
logger = get_logger(__name__)

class EmailService:
    def __init__(self):
        self.smtp_host = config.smtp_host
        self.smtp_port = config.smtp_port
        self.smtp_username = config.smtp_username
        self.smtp_password = config.smtp_password
        self.email_from = config.email_from
        self.email_from_name = config.email_from_name
    
    def send_email(self, to_email: str, subject: str, html_content: str, text_content: str = None) -> bool:
        """
        Send email using SMTP
        """
        try:
            if not all([self.smtp_host, self.smtp_username, self.smtp_password]):
                logger.warning("SMTP configuration missing, email not sent")
                return False
            
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{self.email_from_name} <{self.email_from}>"
            msg['To'] = to_email
            
            # Add text/plain part
            if text_content:
                text_part = MIMEText(text_content, 'plain')
                msg.attach(text_part)
            
            # Add text/html part
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)
            
            # Send email
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
        # SMS service configuration would go here
        # For now, we'll just log the SMS
        pass
    
    def send_sms(self, to_phone: str, message: str) -> bool:
        """
        Send SMS (simulated for now)
        In production, integrate with SMS gateway like Twilio, Msg91, etc.
        """
        try:
            # Simulate SMS sending
            logger.info(f"SMS to {to_phone}: {message}")
            
            # In production, this would call the SMS gateway API
            # For now, we'll just return success
            return True
            
        except Exception as e:
            logger.error(f"Failed to send SMS to {to_phone}: {e}")
            return False

class PushService:
    def __init__(self):
        # Push notification service configuration
        pass
    
    def send_push(self, to_user_id: int, title: str, message: str, data: dict = None) -> bool:
        """
        Send push notification (simulated for now)
        In production, integrate with FCM (Firebase Cloud Messaging)
        """
        try:
            # Simulate push notification
            logger.info(f"Push to user {to_user_id}: {title} - {message}")
            
            # In production, this would call FCM or similar service
            # For now, we'll just return success
            return True
            
        except Exception as e:
            logger.error(f"Failed to send push to user {to_user_id}: {e}")
            return False

# Initialize services
email_service = EmailService()
sms_service = SMSService()
push_service = PushService()

def log_notification(notification_type: str, recipient: str, subject: str = None, 
                    message: str = None, template_name: str = None, status: str = "sent"):
    """
    Log notification to database
    """
    try:
        with db.get_cursor() as cursor:
            cursor.execute("""
                INSERT INTO notification_logs (type, recipient, subject, message, status, template_name)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (notification_type, recipient, subject, message, status, template_name))
    except Exception as e:
        logger.error(f"Failed to log notification: {e}")

def get_email_template(template_name: str, template_data: dict) -> tuple:
    """
    Get email template content based on template name
    """
    templates = {
        "welcome_email": {
            "subject": "Welcome to {app_name}!",
            "html": """
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
                    .container { max-width: 600px; margin: 0 auto; padding: 20px; }
                    .header { background: #4CAF50; color: white; padding: 20px; text-align: center; }
                    .content { padding: 20px; background: #f9f9f9; }
                    .footer { padding: 20px; text-align: center; font-size: 12px; color: #666; }
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
                    body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
                    .container { max-width: 600px; margin: 0 auto; padding: 20px; }
                    .header { background: #2196F3; color: white; padding: 20px; text-align: center; }
                    .order-info { background: #f9f9f9; padding: 15px; margin: 10px 0; }
                    .footer { padding: 20px; text-align: center; font-size: 12px; color: #666; }
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
                    body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
                    .container { max-width: 600px; margin: 0 auto; padding: 20px; }
                    .header { background: #FF9800; color: white; padding: 20px; text-align: center; }
                    .button { background: #FF9800; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; }
                    .footer { padding: 20px; text-align: center; font-size: 12px; color: #666; }
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
    background_tasks: BackgroundTasks
):
    """
    Send email notification
    """
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
    """
    Background task to send email
    """
    try:
        success = email_service.send_email(to_email, subject, html_content)
        status = "sent" if success else "failed"
        
        log_notification(
            notification_type="email",
            recipient=to_email,
            subject=subject,
            message=html_content[:500],  # Store first 500 chars
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
    background_tasks: BackgroundTasks
):
    """
    Send SMS notification
    """
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
    """
    Background task to send SMS
    """
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
    background_tasks: BackgroundTasks
):
    """
    Send push notification
    """
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
    """
    Background task to send push notification
    """
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

@router.get("/logs", response_model=List[NotificationResponse])
async def get_notification_logs(
    notification_type: Optional[NotificationType] = None,
    recipient: Optional[str] = None,
    page: int = 1,
    page_size: int = 20
):
    """
    Get notification logs with filtering
    """
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
async def get_notification_stats(days: int = 7):
    """
    Get notification statistics
    """
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
                last_24_hours=last_24_hours
            )
            
    except Exception as e:
        logger.error(f"Failed to fetch notification stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch notification statistics"
        )

@router.post("/order/{order_id}/confirmation")
async def send_order_confirmation(order_id: int, user_id: int = 1):
    """
    Send order confirmation notification
    """
    try:
        with db.get_cursor() as cursor:
            # Get order details
            cursor.execute("""
                SELECT o.*, u.email, u.first_name, u.phone 
                FROM orders o 
                JOIN users u ON o.user_id = u.id 
                WHERE o.id = %s AND o.user_id = %s
            """, (order_id, user_id))
            
            order = cursor.fetchone()
            if not order:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Order not found"
                )
            
            # Prepare template data
            template_data = {
                "customer_name": order['first_name'],
                "order_number": order['order_number'],
                "order_date": order['created_at'].strftime("%B %d, %Y"),
                "total_amount": float(order['total_amount'])
            }
            
            # Send email notification
            email_notification = EmailNotification(
                to_email=order['email'],
                subject="Order Confirmation",
                template_name="order_confirmation",
                template_data=template_data
            )
            
            # This would typically be called in background
            # For now, we'll simulate it
            subject, html_content = get_email_template("order_confirmation", template_data)
            
            log_notification(
                notification_type="email",
                recipient=order['email'],
                subject=subject,
                template_name="order_confirmation",
                status="sent"
            )
            
            logger.info(f"Order confirmation sent for order {order_id}")
            
            return {
                "success": True,
                "message": "Order confirmation sent successfully"
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to send order confirmation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send order confirmation"
        )
