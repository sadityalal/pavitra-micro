import json
import logging
from shared import get_logger, rabbitmq_client, db, config
from .routes import email_service, sms_service, push_service, telegram_service, whatsapp_service, log_notification

logger = get_logger(__name__)

class BusinessAlertService:
    def __init__(self):
        self.admin_email = getattr(config, 'site_email', 'admin@pavitra-trading.com')
        self.telegram_chat_id = getattr(config, 'telegram_chat_id', None)
        self.enabled = getattr(config, 'telegram_notifications', False)
        self.bot_token = getattr(config, 'telegram_bot_token', None)
    
    def send_new_order_alert(self, order_data: dict):
        """Send alert to business about new order"""
        try:
            # Telegram alert to business
            telegram_msg = f"""
🛍️ <b>NEW ORDER RECEIVED</b>

Order #: {order_data.get('order_number')}
Customer: {order_data.get('customer_name')}
Amount: ₹{order_data.get('total_amount')}
Items: {order_data.get('item_count', 0)}
Time: {order_data.get('created_at')}

<a href="https://admin.pavitra-trading.com/orders/{order_data.get('id')}">View Order</a>
            """
            
            if self.telegram_chat_id and self.enabled and self.bot_token:
                self.send_telegram_message(self.telegram_chat_id, telegram_msg)
                log_notification(
                    notification_type="telegram",
                    recipient=self.telegram_chat_id,
                    message=telegram_msg,
                    template_name="business_alert",
                    status="sent"
                )
            
            # Email alert to business
            email_subject = f"New Order - {order_data.get('order_number')}"
            email_content = f"""
            <h2>New Order Received</h2>
            <p><strong>Order Number:</strong> {order_data.get('order_number')}</p>
            <p><strong>Customer:</strong> {order_data.get('customer_name')}</p>
            <p><strong>Email:</strong> {order_data.get('customer_email')}</p>
            <p><strong>Amount:</strong> ₹{order_data.get('total_amount')}</p>
            <p><strong>Items:</strong> {order_data.get('item_count', 0)}</p>
            <p><strong>Order Time:</strong> {order_data.get('created_at')}</p>
            """
            
            email_service.send_email(self.admin_email, email_subject, email_content)
            log_notification(
                notification_type="email",
                recipient=self.admin_email,
                subject=email_subject,
                template_name="business_alert",
                status="sent"
            )
            
            logger.info(f"Business alert sent for new order {order_data.get('order_number')}")
            
        except Exception as e:
            logger.error(f"Failed to send business alert: {e}")
    
    def send_low_stock_alert(self, product_data: dict):
        """Send low stock alert to business"""
        try:
            telegram_msg = f"""
⚠️ <b>LOW STOCK ALERT</b>

Product: {product_data.get('product_name')}
SKU: {product_data.get('sku')}
Current Stock: {product_data.get('current_stock')}
Threshold: {product_data.get('threshold', 5)}

<a href="https://admin.pavitra-trading.com/products/{product_data.get('id')}">Manage Stock</a>
            """
            
            if self.telegram_chat_id and self.enabled and self.bot_token:
                self.send_telegram_message(self.telegram_chat_id, telegram_msg)
                log_notification(
                    notification_type="telegram",
                    recipient=self.telegram_chat_id,
                    message=telegram_msg,
                    template_name="low_stock_alert",
                    status="sent"
                )
            
            logger.info(f"Low stock alert sent for product {product_data.get('sku')}")
            
        except Exception as e:
            logger.error(f"Failed to send low stock alert: {e}")
    
    def send_payment_alert(self, payment_data: dict):
        """Send payment alert to business"""
        try:
            status_icon = "✅" if payment_data.get('status') == 'completed' else "❌"
            telegram_msg = f"""
💰 <b>PAYMENT {payment_data.get('status', '').upper()}</b>

Order #: {payment_data.get('order_number')}
Amount: ₹{payment_data.get('amount')}
Method: {payment_data.get('payment_method')}
Status: {status_icon} {payment_data.get('status')}
Time: {payment_data.get('created_at')}

{"Failure Reason: " + payment_data.get('failure_reason', '') if payment_data.get('status') == 'failed' else ''}
            """
            
            if self.telegram_chat_id and self.enabled and self.bot_token:
                self.send_telegram_message(self.telegram_chat_id, telegram_msg)
                log_notification(
                    notification_type="telegram",
                    recipient=self.telegram_chat_id,
                    message=telegram_msg,
                    template_name="payment_alert",
                    status="sent"
                )
            
            logger.info(f"Payment alert sent for order {payment_data.get('order_number')}")
            
        except Exception as e:
            logger.error(f"Failed to send payment alert: {e}")
    
    def send_refund_alert(self, refund_data: dict):
        """Send refund alert to business"""
        try:
            telegram_msg = f"""
💸 <b>REFUND PROCESSED</b>

Order #: {refund_data.get('order_number')}
Refund Amount: ₹{refund_data.get('amount')}
Customer: {refund_data.get('customer_name')}
Reason: {refund_data.get('reason', 'N/A')}
Time: {refund_data.get('processed_at')}
            """
            
            if self.telegram_chat_id and self.enabled and self.bot_token:
                self.send_telegram_message(self.telegram_chat_id, telegram_msg)
                log_notification(
                    notification_type="telegram",
                    recipient=self.telegram_chat_id,
                    message=telegram_msg,
                    template_name="refund_alert",
                    status="sent"
                )
            
            logger.info(f"Refund alert sent for order {refund_data.get('order_number')}")
            
        except Exception as e:
            logger.error(f"Failed to send refund alert: {e}")
    
    def send_telegram_message(self, chat_id: str, message: str, parse_mode: str = "HTML") -> bool:
        """Send message via Telegram"""
        try:
            if not self.enabled or not self.bot_token:
                logger.info("Telegram notifications disabled or bot token missing")
                return False

            return telegram_service.send_message(chat_id, message, parse_mode)
        except Exception as e:
            logger.error(f"Failed to send Telegram message: {e}")
            return False

# Global instance
business_alerts = BusinessAlertService()

class NotificationConsumer:
    def __init__(self):
        self.running = False

    def start_consuming(self):
        self.running = True
        logger.info("Starting notification consumer...")
        try:
            rabbitmq_client.consume_messages('notification_queue', self.process_notification)
        except Exception as e:
            logger.error(f"Notification consumer stopped: {e}")
            self.running = False

    def process_notification(self, message):
        try:
            event_type = message.get('event_type')
            logger.info(f"Processing notification event: {event_type}")

            if event_type == 'order_created':
                self.handle_order_created(message)
            elif event_type == 'order_updated':
                self.handle_order_updated(message)
            elif event_type == 'payment_completed':
                self.handle_payment_completed(message)
            elif event_type == 'payment_failed':
                self.handle_payment_failed(message)
            elif event_type == 'user_registered':
                self.handle_user_registered(message)
            elif event_type == 'password_reset':
                self.handle_password_reset(message)
            elif event_type == 'order_cancelled':
                self.handle_order_cancelled(message)
            elif event_type == 'refund_processed':
                self.handle_refund_processed(message)
            elif event_type == 'low_stock':
                self.handle_low_stock(message)
            else:
                logger.warning(f"Unknown event type: {event_type}")

        except Exception as e:
            logger.error(f"Error processing notification: {e}")

    def handle_order_created(self, message):
        try:
            order_data = message.get('data', {})
            user_id = order_data.get('user_id')
            
            with db.get_cursor() as cursor:
                cursor.execute("""
                    SELECT u.email, u.first_name, u.phone
                    FROM users u WHERE u.id = %s
                """, (user_id,))
                user = cursor.fetchone()
                
                # CUSTOMER NOTIFICATION - Email confirmation
                if user and user['email']:
                    template_data = {
                        'customer_name': user['first_name'],
                        'order_number': order_data.get('order_number'),
                        'order_date': order_data.get('created_at'),
                        'total_amount': order_data.get('total_amount')
                    }
                    
                    subject = f"Order Confirmation - {order_data.get('order_number')}"
                    html_content = f"""
                    <h1>Order Confirmed!</h1>
                    <p>Hello {user['first_name']},</p>
                    <p>Thank you for your order. We're getting it ready for you.</p>
                    <p><strong>Order Number:</strong> {order_data.get('order_number')}</p>
                    <p><strong>Total Amount:</strong> ₹{order_data.get('total_amount')}</p>
                    <p>We'll notify you when your order ships.</p>
                    """
                    
                    email_service.send_email(user['email'], subject, html_content)
                    log_notification(
                        notification_type="email",
                        recipient=user['email'],
                        subject=subject,
                        template_name="order_confirmation",
                        status="sent"
                    )
                
                # BUSINESS ALERT - Notify admin about new order
                business_order_data = {
                    'id': order_data.get('id'),
                    'order_number': order_data.get('order_number'),
                    'customer_name': user['first_name'] if user else 'Unknown',
                    'customer_email': user['email'] if user else 'Unknown',
                    'total_amount': order_data.get('total_amount'),
                    'item_count': order_data.get('item_count', 1),
                    'created_at': order_data.get('created_at')
                }
                business_alerts.send_new_order_alert(business_order_data)
                    
        except Exception as e:
            logger.error(f"Error handling order created notification: {e}")

    def handle_order_updated(self, message):
        try:
            order_data = message.get('data', {})
            user_id = order_data.get('user_id')
            new_status = order_data.get('status')
            
            with db.get_cursor() as cursor:
                cursor.execute("""
                    SELECT u.email, u.first_name, u.phone
                    FROM users u WHERE u.id = %s
                """, (user_id,))
                user = cursor.fetchone()
                
                if user and user['email']:
                    subject = f"Order Update - {order_data.get('order_number')}"
                    html_content = f"""
                    <h1>Order Status Updated</h1>
                    <p>Hello {user['first_name']},</p>
                    <p>Your order status has been updated.</p>
                    <p><strong>Order Number:</strong> {order_data.get('order_number')}</p>
                    <p><strong>New Status:</strong> {new_status}</p>
                    """
                    
                    email_service.send_email(user['email'], subject, html_content)
                    log_notification(
                        notification_type="email",
                        recipient=user['email'],
                        subject=subject,
                        template_name="order_status_update",
                        status="sent"
                    )
                    
        except Exception as e:
            logger.error(f"Error handling order updated notification: {e}")

    def handle_payment_completed(self, message):
        try:
            payment_data = message.get('data', {})
            user_id = payment_data.get('user_id')
            
            with db.get_cursor() as cursor:
                cursor.execute("""
                    SELECT u.email, u.first_name, u.phone
                    FROM users u WHERE u.id = %s
                """, (user_id,))
                user = cursor.fetchone()
                
                # CUSTOMER NOTIFICATION
                if user and user['email']:
                    subject = "Payment Received - Thank You!"
                    html_content = f"""
                    <h1>Payment Received</h1>
                    <p>Hello {user['first_name']},</p>
                    <p>We have successfully received your payment.</p>
                    <p><strong>Amount:</strong> ₹{payment_data.get('amount')}</p>
                    <p><strong>Payment Method:</strong> {payment_data.get('payment_method')}</p>
                    """
                    
                    email_service.send_email(user['email'], subject, html_content)
                    log_notification(
                        notification_type="email",
                        recipient=user['email'],
                        subject=subject,
                        template_name="payment_received",
                        status="sent"
                    )
                
                # BUSINESS ALERT
                business_payment_data = {
                    'order_number': payment_data.get('order_number'),
                    'amount': payment_data.get('amount'),
                    'payment_method': payment_data.get('payment_method'),
                    'status': 'completed',
                    'created_at': payment_data.get('created_at')
                }
                business_alerts.send_payment_alert(business_payment_data)
                    
        except Exception as e:
            logger.error(f"Error handling payment completed notification: {e}")

    def handle_payment_failed(self, message):
        try:
            payment_data = message.get('data', {})
            user_id = payment_data.get('user_id')
            
            with db.get_cursor() as cursor:
                cursor.execute("""
                    SELECT u.email, u.first_name, u.phone
                    FROM users u WHERE u.id = %s
                """, (user_id,))
                user = cursor.fetchone()
                
                # CUSTOMER NOTIFICATION
                if user and user['email']:
                    subject = "Payment Failed - Please Try Again"
                    html_content = f"""
                    <h1>Payment Failed</h1>
                    <p>Hello {user['first_name']},</p>
                    <p>We were unable to process your payment.</p>
                    <p><strong>Reason:</strong> {payment_data.get('failure_reason', 'Unknown error')}</p>
                    <p>Please try again or use a different payment method.</p>
                    """
                    
                    email_service.send_email(user['email'], subject, html_content)
                    log_notification(
                        notification_type="email",
                        recipient=user['email'],
                        subject=subject,
                        template_name="payment_failed",
                        status="sent"
                    )
                
                # BUSINESS ALERT
                business_payment_data = {
                    'order_number': payment_data.get('order_number'),
                    'amount': payment_data.get('amount'),
                    'payment_method': payment_data.get('payment_method'),
                    'status': 'failed',
                    'failure_reason': payment_data.get('failure_reason', 'Unknown error'),
                    'created_at': payment_data.get('created_at')
                }
                business_alerts.send_payment_alert(business_payment_data)
                    
        except Exception as e:
            logger.error(f"Error handling payment failed notification: {e}")

    def handle_user_registered(self, message):
        try:
            user_data = message.get('data', {})
            email = user_data.get('email')
            first_name = user_data.get('first_name')
            
            # CUSTOMER NOTIFICATION - Welcome email
            if email:
                subject = "Welcome to Pavitra Trading!"
                html_content = f"""
                <h1>Welcome to Pavitra Trading!</h1>
                <p>Hello {first_name},</p>
                <p>Thank you for registering with us. We're excited to have you as a member!</p>
                <p>Start exploring our products and enjoy a seamless shopping experience.</p>
                """
                
                email_service.send_email(email, subject, html_content)
                log_notification(
                    notification_type="email",
                    recipient=email,
                    subject=subject,
                    template_name="welcome_email",
                    status="sent"
                )
                
        except Exception as e:
            logger.error(f"Error handling user registered notification: {e}")

    def handle_password_reset(self, message):
        try:
            reset_data = message.get('data', {})
            email = reset_data.get('email')
            reset_url = reset_data.get('reset_url')
            first_name = reset_data.get('first_name', 'User')
            
            # CUSTOMER NOTIFICATION - Password reset email
            if email and reset_url:
                subject = "Password Reset Request"
                html_content = f"""
                <h1>Password Reset</h1>
                <p>Hello {first_name},</p>
                <p>We received a request to reset your password.</p>
                <p>Click the link below to reset your password:</p>
                <p><a href="{reset_url}">Reset Password</a></p>
                <p>This link will expire in 1 hour.</p>
                <p>If you didn't request this, please ignore this email.</p>
                """
                
                email_service.send_email(email, subject, html_content)
                log_notification(
                    notification_type="email",
                    recipient=email,
                    subject=subject,
                    template_name="password_reset",
                    status="sent"
                )
                
        except Exception as e:
            logger.error(f"Error handling password reset notification: {e}")

    def handle_order_cancelled(self, message):
        try:
            order_data = message.get('data', {})
            user_id = order_data.get('user_id')
            
            with db.get_cursor() as cursor:
                cursor.execute("""
                    SELECT u.email, u.first_name, u.phone
                    FROM users u WHERE u.id = %s
                """, (user_id,))
                user = cursor.fetchone()
                
                # CUSTOMER NOTIFICATION
                if user and user['email']:
                    subject = f"Order Cancelled - {order_data.get('order_number')}"
                    html_content = f"""
                    <h1>Order Cancelled</h1>
                    <p>Hello {user['first_name']},</p>
                    <p>Your order has been cancelled as requested.</p>
                    <p><strong>Order Number:</strong> {order_data.get('order_number')}</p>
                    <p><strong>Reason:</strong> {order_data.get('cancellation_reason', 'Customer request')}</p>
                    """
                    
                    email_service.send_email(user['email'], subject, html_content)
                    log_notification(
                        notification_type="email",
                        recipient=user['email'],
                        subject=subject,
                        template_name="order_cancelled",
                        status="sent"
                    )
                    
        except Exception as e:
            logger.error(f"Error handling order cancelled notification: {e}")

    def handle_refund_processed(self, message):
        try:
            refund_data = message.get('data', {})
            user_id = refund_data.get('user_id')
            
            with db.get_cursor() as cursor:
                cursor.execute("""
                    SELECT u.email, u.first_name, u.phone
                    FROM users u WHERE u.id = %s
                """, (user_id,))
                user = cursor.fetchone()
                
                # CUSTOMER NOTIFICATION
                if user and user['email']:
                    subject = f"Refund Processed - {refund_data.get('order_number')}"
                    html_content = f"""
                    <h1>Refund Processed</h1>
                    <p>Hello {user['first_name']},</p>
                    <p>Your refund has been processed successfully.</p>
                    <p><strong>Order Number:</strong> {refund_data.get('order_number')}</p>
                    <p><strong>Refund Amount:</strong> ₹{refund_data.get('amount')}</p>
                    <p><strong>Refund Method:</strong> {refund_data.get('payment_method')}</p>
                    <p>It may take 5-7 business days for the refund to reflect in your account.</p>
                    """
                    
                    email_service.send_email(user['email'], subject, html_content)
                    log_notification(
                        notification_type="email",
                        recipient=user['email'],
                        subject=subject,
                        template_name="refund_processed",
                        status="sent"
                    )
                
                # BUSINESS ALERT
                business_refund_data = {
                    'order_number': refund_data.get('order_number'),
                    'amount': refund_data.get('amount'),
                    'customer_name': user['first_name'] if user else 'Unknown',
                    'reason': refund_data.get('reason', 'N/A'),
                    'processed_at': refund_data.get('processed_at')
                }
                business_alerts.send_refund_alert(business_refund_data)
                    
        except Exception as e:
            logger.error(f"Error handling refund processed notification: {e}")

    def handle_low_stock(self, message):
        try:
            product_data = message.get('data', {})
            
            # BUSINESS ALERT ONLY - Low stock notification
            business_alerts.send_low_stock_alert(product_data)
                    
        except Exception as e:
            logger.error(f"Error handling low stock notification: {e}")

notification_consumer = NotificationConsumer()
