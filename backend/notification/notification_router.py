from typing import Dict, Any, List, Optional
from shared import get_logger, db
from .models import NotificationType

logger = get_logger(__name__)

class NotificationRouter:
    def __init__(self):
        # Define priority for different notification types
        self.notification_priority = {
            'order_confirmations': ['telegram', 'whatsapp', 'sms', 'email'],
            'payment_notifications': ['telegram', 'whatsapp', 'sms', 'email'],
            'shipping_updates': ['sms', 'whatsapp', 'telegram', 'email'],
            'promotional': ['email', 'whatsapp', 'telegram'],
            'security_alerts': ['telegram', 'sms', 'email', 'whatsapp'],
            'welcome_messages': ['email', 'whatsapp', 'telegram', 'sms']
        }
    
    def get_user_notification_methods(self, user_id: int, notification_type: str) -> List[str]:
        """Get user's preferred notification methods for a specific notification type"""
        try:
            with db.get_cursor() as cursor:
                # Get user's enabled notification methods
                cursor.execute("""
                    SELECT unp.notification_method, u.email, u.phone, u.email_verified, 
                           u.phone_verified, u.telegram_username, u.telegram_phone
                    FROM user_notification_preferences unp
                    JOIN users u ON unp.user_id = u.id
                    WHERE unp.user_id = %s AND unp.is_enabled = TRUE
                    ORDER BY unp.priority_order, unp.notification_method
                """, (user_id,))
                
                user_preferences = cursor.fetchall()
                
                if not user_preferences:
                    # Fallback: if no preferences set, use email only
                    return ['email']
                
                available_methods = []
                user_data = user_preferences[0] if user_preferences else {}
                
                for pref in user_preferences:
                    method = pref['notification_method']
                    
                    # Validate if method can be used
                    if self._can_use_notification_method(method, user_data):
                        available_methods.append(method)
                
                # Apply priority for this notification type
                type_priority = self.notification_priority.get(notification_type, ['email'])
                ordered_methods = [method for method in type_priority if method in available_methods]
                
                # If no methods match the priority, use available methods in their order
                if not ordered_methods and available_methods:
                    ordered_methods = available_methods
                
                logger.info(f"User {user_id} methods for {notification_type}: {ordered_methods}")
                return ordered_methods
                
        except Exception as e:
            logger.error(f"Error getting user notification methods: {e}")
            return ['email']  # Fallback to email
    
    def _can_use_notification_method(self, method: str, user_data: Dict) -> bool:
        """Check if a notification method can be used for this user"""
        if method == 'email':
            return bool(user_data.get('email') and user_data.get('email_verified'))
        
        elif method == 'sms':
            return bool(user_data.get('phone') and user_data.get('phone_verified'))
        
        elif method == 'whatsapp':
            return bool(user_data.get('phone') and user_data.get('phone_verified'))
        
        elif method == 'telegram':
            return bool(user_data.get('telegram_username') or user_data.get('telegram_phone'))
        
        elif method == 'push':
            return True  # Push can always be attempted
        
        return False
    
    def get_notification_recipient(self, user_id: int, method: str) -> Optional[str]:
        """Get the recipient address for a specific notification method"""
        try:
            with db.get_cursor() as cursor:
                cursor.execute("""
                    SELECT email, phone, telegram_username, telegram_phone
                    FROM users WHERE id = %s
                """, (user_id,))
                user = cursor.fetchone()
                
                if not user:
                    return None
                
                if method == 'email':
                    return user['email']
                elif method == 'sms':
                    return user['phone']
                elif method == 'whatsapp':
                    return user['phone']
                elif method == 'telegram':
                    return user['telegram_username'] or user['telegram_phone']
                
                return None
                
        except Exception as e:
            logger.error(f"Error getting recipient for user {user_id}, method {method}: {e}")
            return None

# Global instance
notification_router = NotificationRouter()
