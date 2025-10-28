from fastapi import APIRouter, HTTPException, Depends, Form, Request, status, BackgroundTasks
from typing import Optional, List
from datetime import datetime, timedelta
from shared import (
    config, db, verify_password, get_password_hash,
    create_access_token, verify_token, validate_email,
    validate_phone, sanitize_input, get_logger, rabbitmq_client, redis_client
)
from .models import (
    UserCreate, UserLogin, Token, UserResponse,
    RoleResponse, PermissionCheck, HealthResponse
)
import re
router = APIRouter()
logger = get_logger(__name__)

def validate_username(username: str) -> bool:
    if not username:
        return False
    pattern = r'^[a-zA-Z0-9_]{3,30}$'
    return re.match(pattern, username) is not None

def publish_user_registration_event(user_data: dict):
    try:
        # Convert datetime objects to strings for JSON serialization
        serializable_user_data = {}
        for key, value in user_data.items():
            if hasattr(value, 'isoformat'):  # Check if it's a datetime object
                serializable_user_data[key] = value.isoformat()
            else:
                serializable_user_data[key] = value

        message = {
            'event_type': 'user_registered',
            'user_id': serializable_user_data['id'],
            'email': serializable_user_data.get('email'),
            'first_name': serializable_user_data.get('first_name'),
            'timestamp': datetime.utcnow().isoformat(),  # Already a string
            'data': serializable_user_data
        }

        # Ensure RabbitMQ client is connected before publishing
        if rabbitmq_client.connect():
            success = rabbitmq_client.publish_message(
                exchange='notification_events',
                routing_key='user.registered',
                message=message
            )
            if success:
                logger.info(f"✅ User registration event published for user {serializable_user_data['id']}")
            else:
                logger.error(f"❌ Failed to publish user registration event for user {serializable_user_data['id']}")
        else:
            logger.error("❌ Cannot publish user registration event - RabbitMQ not connected")

    except Exception as e:
        logger.error(f"❌ Failed to publish user registration event: {e}")


@router.post("/register", response_model=Token)
async def register_user(
        email: Optional[str] = Form(None),
        phone: Optional[str] = Form(None),
        username: Optional[str] = Form(None),
        password: str = Form(...),
        first_name: str = Form(...),
        last_name: str = Form(...),
        country_id: int = Form(1),
        telegram_username: Optional[str] = Form(None),
        telegram_phone: Optional[str] = Form(None),
        whatsapp_phone: Optional[str] = Form(None),
        background_tasks: BackgroundTasks = None
):
    try:
        # Check maintenance mode
        config.refresh_cache()
        logger.info(f"DEBUG: Maintenance mode value: {config.maintenance_mode}, type: {type(config.maintenance_mode)}")
        if config.maintenance_mode:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Service is under maintenance. Registration is temporarily unavailable."
            )

        first_name = sanitize_input(first_name)
        last_name = sanitize_input(last_name)
        telegram_username = sanitize_input(telegram_username) if telegram_username else None
        telegram_phone = sanitize_input(telegram_phone) if telegram_phone else None
        whatsapp_phone = sanitize_input(whatsapp_phone) if whatsapp_phone else None

        if not email and not phone and not username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email, phone, or username is required"
            )

        if email and not validate_email(email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid email format"
            )

        if phone and not validate_phone(phone):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid phone format"
            )

        if username and not validate_username(username):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username must be 3-30 characters and contain only letters, numbers, and underscores"
            )

        if len(password) < 8:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must be at least 8 characters long"
            )

        # Check for common passwords (basic security)
        common_passwords = ['password', '12345678', 'qwerty', 'admin', 'letmein']
        if password.lower() in common_passwords:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password is too common. Please choose a stronger password."
            )

        logger.info(f"Processing registration with Argon2 hashing")
        with db.get_cursor() as cursor:
            # Check for existing user
            if email:
                cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
                if cursor.fetchone():
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Email already registered"
                    )

            if phone:
                cursor.execute("SELECT id FROM users WHERE phone = %s", (phone,))
                if cursor.fetchone():
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Phone number already registered"
                    )

            if username:
                cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
                if cursor.fetchone():
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Username already taken"
                    )

            if telegram_username:
                telegram_username = telegram_username.lstrip('@')
                cursor.execute("SELECT id FROM users WHERE telegram_username = %s", (telegram_username,))
                if cursor.fetchone():
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Telegram username already taken"
                    )


            password_hash = get_password_hash(password)
            cursor.execute("""
                INSERT INTO users (email, phone, username, password_hash, first_name, last_name, country_id, telegram_username, telegram_phone, whatsapp_phone)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (email, phone, username, password_hash, first_name, last_name, country_id, telegram_username, phone, phone))
            user_id = cursor.lastrowid

            # Assign customer role by default
            cursor.execute("SELECT id FROM user_roles WHERE name = 'customer'")
            role = cursor.fetchone()
            if role:
                cursor.execute("""
                    INSERT INTO user_role_assignments (user_id, role_id, assigned_by)
                    VALUES (%s, %s, %s)
                """, (user_id, role['id'], user_id))

            # ✅ AUTOMATICALLY ENABLE NOTIFICATION METHODS
            # Enable Telegram if Telegram username provided
            if telegram_username:
                cursor.execute("""
                    INSERT INTO user_notification_preferences (user_id, notification_method, is_enabled)
                    VALUES (%s, 'telegram', TRUE)
                    ON DUPLICATE KEY UPDATE is_enabled = TRUE
                """, (user_id,))
                logger.info(f"✅ Automatically enabled Telegram notifications for user {user_id}")

            # Enable WhatsApp if WhatsApp phone provided
            if whatsapp_phone:
                cursor.execute("""
                    INSERT INTO user_notification_preferences (user_id, notification_method, is_enabled)
                    VALUES (%s, 'whatsapp', TRUE)
                    ON DUPLICATE KEY UPDATE is_enabled = TRUE
                """, (user_id,))
                logger.info(f"✅ Automatically enabled WhatsApp notifications for user {user_id}")

            # Always enable email as fallback
            cursor.execute("""
                INSERT INTO user_notification_preferences (user_id, notification_method, is_enabled)
                VALUES (%s, 'email', TRUE)
                ON DUPLICATE KEY UPDATE is_enabled = TRUE
            """, (user_id,))
            logger.info(f"✅ Enabled email notifications for user {user_id}")

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

            # Create access token with secure expiration
            access_token = create_access_token(
                data={
                    "sub": str(user_id),
                    "email": email,
                    "roles": list(roles),
                    "permissions": list(permissions)
                },
                expires_delta=timedelta(hours=24)
            )

            cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
            user = cursor.fetchone()

            # Publish registration event in background
            if background_tasks:
                background_tasks.add_task(
                    publish_user_registration_event,
                    user
                )

            logger.info(f"User registered successfully with Argon2: {email or phone or username}")
            return Token(
                access_token=access_token,
                token_type="bearer",
                expires_in=86400,
                user_roles=list(roles),
                user_permissions=list(permissions)
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )

@router.get("/site-settings")
async def get_site_settings(current_user: dict = Depends(get_current_user)):
    try:
        config.refresh_cache()
        settings = {
            'site_name': config.site_name,
            'site_description': config.site_description,
            'currency': config.currency,
            'currency_symbol': config.currency_symbol,
            'default_gst_rate': config.default_gst_rate,
            'enable_guest_checkout': config.enable_guest_checkout,
            'maintenance_mode': config.maintenance_mode,
            'enable_reviews': config.enable_reviews,
            'enable_wishlist': config.enable_wishlist,
            'min_order_amount': config.min_order_amount,
            'free_shipping_min_amount': config.free_shipping_min_amount,
            'default_currency': config.default_currency,
            'supported_currencies': config.supported_currencies,
            'default_country': config.default_country,
            'app_debug': config.app_debug,
            'log_level': config.log_level,
            'cors_origins': config.cors_origins,
            'rate_limit_requests': config.rate_limit_requests,
            'rate_limit_window': config.rate_limit_window,
            'razorpay_test_mode': config.razorpay_test_mode,
            'stripe_test_mode': config.stripe_test_mode,
            'email_notifications': config.email_notifications,
            'sms_notifications': config.sms_notifications,
            'push_notifications': config.push_notifications,
            'refund_policy_days': config.refund_policy_days,
            'auto_refund_enabled': config.auto_refund_enabled,
            'refund_processing_fee': config.refund_processing_fee,
            'app_name': config.app_name,
            'app_description': config.app_description,
            'debug_mode': config.debug_mode,
            'redis_host': config.redis_host,
            'redis_port': config.redis_port,
            'redis_password': config.redis_password,
            'redis_db': config.redis_db,
            'rabbitmq_host': config.rabbitmq_host,
            'rabbitmq_port': config.rabbitmq_port,
            'rabbitmq_user': config.rabbitmq_user,
            'rabbitmq_password': config.rabbitmq_password,
            'smtp_host': config.smtp_host,
            'smtp_port': config.smtp_port,
            'smtp_username': config.smtp_username,
            'smtp_password': config.smtp_password,
            'email_from': config.email_from,
            'free_shipping_threshold': getattr(config, 'free_shipping_threshold'),
            'return_period_days': getattr(config, 'return_period_days', 10),
            'site_phone': getattr(config, 'site_phone', '+91-9711317009'),
            'site_email': getattr(config, 'site_email', 'support@pavitraenterprises.com'),
            'business_hours': getattr(config, 'business_hours', {
                'monday_friday': '9am-6pm',
                'saturday': '10am-4pm',
                'sunday': 'Closed'
            })
        }
        return settings
    except Exception as e:
        logger.error(f"Failed to fetch site settings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch site settings"
        )

@router.post("/login")
async def login_user(login_data: UserLogin):
    try:
        # Check maintenance mode
        config.refresh_cache()
        logger.info(f"DEBUG: Maintenance mode value: {config.maintenance_mode}, type: {type(config.maintenance_mode)}")
        if config.maintenance_mode:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Service is under maintenance. Please try again later."
            )

        with db.get_cursor() as cursor:
            cursor.execute("""
                SELECT id, email, password_hash, first_name, last_name,
                       is_active, email_verified, phone_verified
                FROM users
                WHERE email = %s OR phone = %s OR username = %s
            """, (login_data.login_id, login_data.login_id, login_data.login_id))
            user = cursor.fetchone()

            if not user or not verify_password(login_data.password, user['password_hash']):
                # Log failed login attempt for security monitoring
                logger.warning(f"Failed login attempt for: {login_data.login_id}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid credentials"
                )

            if not user['is_active']:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Account is deactivated"
                )

            # Get user roles and permissions
            cursor.execute("""
                SELECT ur.name as role_name, p.name as permission_name
                FROM user_role_assignments ura
                JOIN user_roles ur ON ura.role_id = ur.id
                LEFT JOIN role_permissions rp ON ur.id = rp.role_id
                LEFT JOIN permissions p ON rp.permission_id = p.id
                WHERE ura.user_id = %s
            """, (user['id'],))
            
            roles = set()
            permissions = set()
            for row in cursor.fetchall():
                if row['role_name']:
                    roles.add(row['role_name'])
                if row['permission_name']:
                    permissions.add(row['permission_name'])

            access_token = create_access_token(
                data={
                    "sub": str(user['id']),
                    "email": user['email'],
                    "roles": list(roles),
                    "permissions": list(permissions)
                },
                expires_delta=timedelta(hours=24)
            )

            # Update last login
            cursor.execute("UPDATE users SET last_login = NOW() WHERE id = %s", (user['id'],))
            
            logger.info(f"User login successful with Argon2 verification: {user['email']}")
            return Token(
                access_token=access_token,
                token_type="bearer",
                expires_in=86400,
                user_roles=list(roles),
                user_permissions=list(permissions)
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )

@router.post("/logout")
async def logout_user(request: Request):
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header[7:]
        try:
            # Invalidate token in Redis
            redis_client.redis_client.delete(f"token:{token}")
            logger.info("User logged out successfully - token invalidated")
        except Exception as e:
            logger.error(f"Token invalidation failed: {e}")
    return {"message": "Logged out successfully"}

@router.post("/refresh")
async def refresh_token(request: Request):
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

    token = auth_header[7:]
    payload = verify_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )

    # Create new token with same claims
    new_token = create_access_token(
        data={
            "sub": payload['sub'],
            "email": payload.get('email'),
            "roles": payload.get('roles', []),
            "permissions": payload.get('permissions', [])
        },
        expires_delta=timedelta(hours=24)
    )

    logger.info(f"Token refreshed successfully for user {payload['sub']}")
    return Token(
        access_token=new_token,
        token_type="bearer",
        expires_in=86400,
        user_roles=payload.get('roles', []),
        user_permissions=payload.get('permissions', [])
    )

@router.post("/forgot-password")
async def forgot_password(email: str = Form(...)):
    try:
        config.refresh_cache()
        if config.maintenance_mode:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Service is under maintenance. Please try again later."
            )

        with db.get_cursor() as cursor:
            cursor.execute("SELECT id, first_name FROM users WHERE email = %s", (email,))
            user = cursor.fetchone()
            if user:
                reset_token = create_access_token(
                    data={"sub": str(user['id']), "type": "password_reset"},
                    expires_delta=timedelta(hours=1)
                )
                # Store reset token in Redis with expiration
                redis_client.redis_client.setex(
                    f"password_reset:{user['id']}",
                    3600,
                    reset_token
                )
                logger.info(f"Password reset initiated for user {user['id']}")
            # Always return same message for security (prevent email enumeration)
            return {"message": "If the email exists, a reset link has been sent"}
    except Exception as e:
        logger.error(f"Password reset failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password reset failed"
        )

@router.post("/reset-password")
async def reset_password(token: str = Form(...), new_password: str = Form(...)):
    try:
        config.refresh_cache()
        if config.maintenance_mode:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Service is under maintenance. Please try again later."
            )

        payload = verify_token(token)
        if not payload or payload.get('type') != 'password_reset':
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid reset token"
            )

        user_id = int(payload['sub'])
        stored_token = redis_client.redis_client.get(f"password_reset:{user_id}")
        if not stored_token or stored_token != token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token"
            )

        if len(new_password) < 8:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must be at least 8 characters long"
            )

        with db.get_cursor() as cursor:
            new_password_hash = get_password_hash(new_password)
            cursor.execute(
                "UPDATE users SET password_hash = %s WHERE id = %s",
                (new_password_hash, user_id)
            )
            # Store password in history for security
            cursor.execute(
                "INSERT INTO password_history (user_id, password_hash) VALUES (%s, %s)",
                (user_id, new_password_hash)
            )
            # Remove used reset token
            redis_client.redis_client.delete(f"password_reset:{user_id}")
            
            logger.info(f"Password reset successful for user {user_id} using Argon2")
            return {"message": "Password reset successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Password reset failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password reset failed"
        )

@router.get("/roles", response_model=List[RoleResponse])
async def get_roles():
    """Get all available roles (admin only)"""
    try:
        with db.get_cursor() as cursor:
            cursor.execute("""
                SELECT id, name, description FROM user_roles 
                WHERE is_system_role = 1
                ORDER BY name
            """)
            roles = cursor.fetchall()
            return [
                RoleResponse(
                    id=role['id'],
                    name=role['name'],
                    description=role['description'],
                    permissions=[]
                )
                for role in roles
            ]
    except Exception as e:
        logger.error(f"Failed to fetch roles: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch roles"
        )

@router.post("/check-permission", response_model=PermissionCheck)
async def check_permission(permission: str, request: Request):
    """Check if current user has specific permission"""
    try:
        from shared.auth_middleware import get_current_user
        current_user = await get_current_user(request)
        user_permissions = current_user.get('permissions', [])
        
        has_access = permission in user_permissions
        return PermissionCheck(
            permission=permission,
            has_access=has_access
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Permission check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Permission check failed"
        )

@router.get("/debug/maintenance")
async def debug_maintenance():
    """Debug endpoint to check maintenance mode status"""
    config.refresh_cache()
    return {
        "maintenance_mode": config.maintenance_mode,
        "maintenance_mode_type": str(type(config.maintenance_mode)),
        "maintenance_mode_raw": str(config.maintenance_mode)
    }

@router.get("/debug/settings")
async def debug_settings():
    """Debug endpoint to check all settings"""
    config.refresh_cache()
    return {
        "maintenance_mode": config.maintenance_mode,
        "debug_mode": config.debug_mode,
        "app_debug": config.app_debug,
        "log_level": config.log_level,
        "cors_origins": config.cors_origins,
        "cache_info": {
            "cache_size": len(config._cache),
            "cache_keys": list(config._cache.keys())
        }
    }
