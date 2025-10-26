from fastapi import APIRouter, HTTPException, Depends
from typing import List
from shared.auth_middleware import get_current_user
from shared import get_logger, db
from .models import NotificationPreferencesUpdate, NotificationMethod, UserProfileResponse

router = APIRouter()
logger = get_logger(__name__)

@router.get("/notification-preferences", response_model=UserProfileResponse)
async def get_notification_preferences(current_user: dict = Depends(get_current_user)):
    """Get user's notification preferences"""
    try:
        user_id = current_user['sub']
        
        with db.get_cursor() as cursor:
            # Get user basic info
            cursor.execute("""
                SELECT u.*, 
                       GROUP_CONCAT(DISTINCT unp.notification_method) as enabled_methods
                FROM users u
                LEFT JOIN user_notification_preferences unp ON u.id = unp.user_id AND unp.is_enabled = TRUE
                WHERE u.id = %s
                GROUP BY u.id
            """, (user_id,))
            user = cursor.fetchone()
            
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            
            # Parse enabled notification methods
            enabled_methods = []
            if user['enabled_methods']:
                enabled_methods = [NotificationMethod(method) for method in user['enabled_methods'].split(',')]
            
            # Get user roles and permissions
            cursor.execute("""
                SELECT ur.name as role_name, p.name as permission_name
                FROM user_role_assignments ura
                JOIN user_roles ur ON ura.role_id = ur.id
                LEFT JOIN role_permissions rp ON ur.id = rp.role_id
                LEFT JOIN permissions p ON rp.permission_id = p.id
                WHERE ura.user_id = %s
            """, (user_id,))
            
            roles = set()
            permissions = set()
            for row in cursor.fetchall():
                if row['role_name']:
                    roles.add(row['role_name'])
                if row['permission_name']:
                    permissions.add(row['permission_name'])
            
            return UserProfileResponse(
                id=user['id'],
                uuid=user['uuid'],
                email=user['email'],
                mobile=user['phone'],
                phone=user['phone'],
                username=user['username'],
                first_name=user['first_name'],
                last_name=user['last_name'],
                email_verified=bool(user['email_verified']),
                phone_verified=bool(user['phone_verified']),
                is_active=bool(user['is_active']),
                roles=list(roles),
                permissions=list(permissions),
                country_id=user['country_id'],
                preferred_currency=user.get('preferred_currency', 'INR'),
                preferred_language=user.get('preferred_language', 'en'),
                avatar_url=user['avatar_url'],
                date_of_birth=user['date_of_birth'],
                gender=user['gender'],
                last_login=user['last_login'],
                telegram_username=user['telegram_username'],
                telegram_phone=user['telegram_phone'],
                whatsapp_phone=user['whatsapp_phone'],
                notification_methods=enabled_methods,
                created_at=user['created_at'],
                updated_at=user['updated_at']
            )
            
    except Exception as e:
        logger.error(f"Failed to get notification preferences: {e}")
        raise HTTPException(status_code=500, detail="Failed to get notification preferences")

@router.put("/notification-preferences")
async def update_notification_preferences(
    preferences: NotificationPreferencesUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update user's notification preferences"""
    try:
        user_id = current_user['sub']
        
        with db.get_cursor() as cursor:
            # Update user's contact info
            update_fields = []
            update_params = []
            
            if preferences.telegram_username is not None:
                telegram_username = preferences.telegram_username.lstrip('@') if preferences.telegram_username else None
                update_fields.append("telegram_username = %s")
                update_params.append(telegram_username)
            
            if preferences.telegram_phone is not None:
                update_fields.append("telegram_phone = %s")
                update_params.append(preferences.telegram_phone)
            
            if preferences.whatsapp_phone is not None:
                update_fields.append("whatsapp_phone = %s")
                update_params.append(preferences.whatsapp_phone)
            
            if update_fields:
                update_fields.append("updated_at = NOW()")
                update_params.append(user_id)
                update_query = f"UPDATE users SET {', '.join(update_fields)} WHERE id = %s"
                cursor.execute(update_query, update_params)
            
            # Update notification preferences
            # First, disable all current preferences
            cursor.execute("""
                UPDATE user_notification_preferences 
                SET is_enabled = FALSE 
                WHERE user_id = %s
            """, (user_id,))
            
            # Enable selected methods
            for method in preferences.notification_methods:
                cursor.execute("""
                    INSERT INTO user_notification_preferences (user_id, notification_method, is_enabled)
                    VALUES (%s, %s, TRUE)
                    ON DUPLICATE KEY UPDATE is_enabled = TRUE
                """, (user_id, method.value))
            
            # Ensure email is always enabled (as fallback)
            cursor.execute("""
                INSERT INTO user_notification_preferences (user_id, notification_method, is_enabled)
                VALUES (%s, 'email', TRUE)
                ON DUPLICATE KEY UPDATE is_enabled = TRUE
            """, (user_id,))
            
            logger.info(f"User {user_id} updated notification preferences: {preferences.notification_methods}")
            
            return {
                "success": True,
                "message": "Notification preferences updated successfully",
                "enabled_methods": [method.value for method in preferences.notification_methods]
            }
            
    except Exception as e:
        logger.error(f"Failed to update notification preferences: {e}")
        raise HTTPException(status_code=500, detail="Failed to update notification preferences")

@router.get("/available-notification-methods")
async def get_available_notification_methods():
    """Get all available notification methods"""
    return {
        "available_methods": [
            {
                "method": "email",
                "name": "Email",
                "description": "Receive notifications via email",
                "requires_verification": True
            },
            {
                "method": "telegram",
                "name": "Telegram",
                "description": "Receive notifications via Telegram",
                "requires_verification": False,
                "requires_username": True
            },
            {
                "method": "whatsapp",
                "name": "WhatsApp",
                "description": "Receive notifications via WhatsApp",
                "requires_verification": True,
                "requires_phone": True
            },
            {
                "method": "sms",
                "name": "SMS",
                "description": "Receive notifications via SMS",
                "requires_verification": True,
                "requires_phone": True
            },
            {
                "method": "push",
                "name": "Push Notifications",
                "description": "Receive push notifications on your device",
                "requires_verification": False
            }
        ]
    }
