import json
import logging
from shared import get_logger, rabbitmq_client, db
from .routes import email_service, sms_service, push_service, log_notification

logger = get_logger(__name__)

class NotificationConsumer:
    def __init__(self):
        self.running = False
    
    def start_consuming(self):
        """Start consuming messages from RabbitMQ"""
        self.running = True
        logger.info("Starting notification consumer...")
        
        try:
            rabbitmq_client.consume_messages('notification_queue', self.process_notification)
        except Exception as e:
            logger.error(f"Notification consumer stopped: {e}")
            self.running = False
    
    def process_notification(self, message):
        """Process incoming notification messages"""
        try:
            event_type = message.get('event_type')
            logger.info(f"Processing notification event: {event_type}")
            
            if event_type == 'order_created':
                self.handle_order_created(message)
            elif event_type == 'order_updated':
                self.handle_order_updated(message)
            elif event_type == 'payment_completed':
                self.handle_payment_completed(message)
            elif event_type == 'user_registered':
                self.handle_user_registered(message)
            else:
                logger.warning(f"Unknown event type: {event_type}")
                
        except Exception as e:
            logger.error(f"Error processing notification: {e}")
    
    def handle_order_created(self, message):
        """Handle order created notification"""
        try:
            order_data = message.get('data', {})
            user_id = order_data.get('user_id')
            
            with db.get_cursor() as cursor:
                cursor.execute("""
                    SELECT u.email, u.first_name, u.phone
                    FROM users u WHERE u.id = %s
                """, (user_id,))
                user = cursor.fetchone()
                
                if user and user['email']:
                    # Send order confirmation email
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
                    """
                    
                    email_service.send_email(user['email'], subject, html_content)
                    log_notification(
                        notification_type="email",
                        recipient=user['email'],
                        subject=subject,
                        template_name="order_confirmation",
                        status="sent"
                    )
                    
        except Exception as e:
            logger.error(f"Error handling order created notification: {e}")
    
    def handle_order_updated(self, message):
        """Handle order status update notification"""
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
        """Handle payment completed notification"""
        try:
            payment_data = message.get('data', {})
            user_id = payment_data.get('user_id')
            
            with db.get_cursor() as cursor:
                cursor.execute("""
                    SELECT u.email, u.first_name, u.phone
                    FROM users u WHERE u.id = %s
                """, (user_id,))
                user = cursor.fetchone()
                
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
                    
        except Exception as e:
            logger.error(f"Error handling payment completed notification: {e}")
    
    def handle_user_registered(self, message):
        """Handle user registration notification"""
        try:
            user_data = message.get('data', {})
            email = user_data.get('email')
            first_name = user_data.get('first_name')
            
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

# Create global instance
notification_consumer = NotificationConsumer()
