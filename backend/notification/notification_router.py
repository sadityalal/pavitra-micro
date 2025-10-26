from typing import Dict, Any, List, Optional
from shared import get_logger, db

logger = get_logger(__name__)

class NotificationRouter:
    def __init__(self):
        # Define priority for different notification types
        self.notification_priority = {
            'order_confirmations': ['telegram', 'whatsapp', 'sms', 'email'],
            'payment_notifications': ['telegram', 'whatsapp', 'sms', 'email'],
            'shipping_updates': ['whatsapp', 'sms', 'telegram', 'email'],
            'promotional': ['email', 'whatsapp', 'telegram'],
            'security_alerts': ['telegram', 'sms', 'email', 'whatsapp'],
            'welcome_messages': ['email', 'whatsapp', 'telegram', 'sms'],
            'password_reset': ['email', 'sms'],
            'account_verification': ['email', 'sms']
        }
    
    def get_user_notification_channels(self, user_id: int, notification_type: str) -> List[str]:
        """Get user's preferred notification channels for a specific notification type"""
        try:
            with db.get_cursor() as cursor:
                # Get user's enabled notification methods and contact info
                cursor.execute("""
                    SELECT 
                        u.email, u.phone, u.email_verified, u.phone_verified,
                        u.telegram_username, u.telegram_phone, u.whatsapp_phone,
                        GROUP_CONCAT(unp.notification_method) as enabled_methods
                    FROM users u
                    LEFT JOIN user_notification_preferences unp ON u.id = unp.user_id AND unp.is_enabled = TRUE
                    WHERE u.id = %s
                    GROUP BY u.id
                """, (user_id,))
                
                user = cursor.fetchone()
                if not user:
                    return ['email']  # Fallback to email
                
                # Parse enabled methods
                enabled_methods = user['enabled_methods'].split(',') if user['enabled_methods'] else ['email']
                
                available_channels = []
                
                # Check each enabled method for availability
                for method in enabled_methods:
                    if method == 'email' and user['email'] and user['email_verified']:
                        available_channels.append('email')
                    
                    elif method == 'sms' and user['phone'] and user['phone_verified']:
                        available_channels.append('sms')
                    
                    elif method == 'telegram' and (user['telegram_username'] or user['telegram_phone']):
                        available_channels.append('telegram')
                    
                    elif method == 'whatsapp' and user['whatsapp_phone'] and user['phone_verified']:
                        available_channels.append('whatsapp')
                
                # If no channels available, fallback to email
                if not available_channels and user['email']:
                    available_channels.append('email')
                
                # Apply priority for this notification type
                channel_priority = self.notification_priority.get(notification_type, ['email'])
                ordered_channels = [ch for ch in channel_priority if ch in available_channels]
                
                logger.info(f"User {user_id} - Type: {notification_type} - Channels: {ordered_channels}")
                return ordered_channels
                
        except Exception as e:
            logger.error(f"Error getting user channels: {e}")
            return ['email']  # Fallback to email
    
    def get_notification_contacts(self, user_id: int, channel: str) -> Dict[str, str]:
        """Get contact information for a specific channel"""
        try:
            with db.get_cursor() as cursor:
                cursor.execute("""
                    SELECT email, phone, telegram_username, telegram_phone, whatsapp_phone
                    FROM users WHERE id = %s
                """, (user_id,))
                
                user = cursor.fetchone()
                if not user:
                    return {}
                
                contacts = {}
                if channel == 'email' and user['email']:
                    contacts['email'] = user['email']
                elif channel == 'sms' and user['phone']:
                    contacts['phone'] = user['phone']
                elif channel == 'telegram':
                    if user['telegram_username']:
                        contacts['username'] = user['telegram_username']
                    if user['telegram_phone']:
                        contacts['phone'] = user['telegram_phone']
                elif channel == 'whatsapp' and user['whatsapp_phone']:
                    contacts['phone'] = user['whatsapp_phone']
                
                return contacts
                
        except Exception as e:
            logger.error(f"Error getting contacts: {e}")
            return {}

# Global instance
notification_router = NotificationRouter()
