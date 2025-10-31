from fastapi import APIRouter, HTTPException, Depends, Form, Request, status, BackgroundTasks, Response
from typing import Optional, List
from datetime import datetime, timedelta
from shared import (
    config, db, verify_password, get_password_hash,
    create_access_token, verify_token, validate_email,
    validate_phone, sanitize_input, get_logger, rabbitmq_client, redis_client
)
from shared.auth_middleware import get_current_user, require_roles, blacklist_token
from shared.session_service import session_service, SessionType
from shared.session_middleware import get_session, get_session_id
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
        serializable_user_data = {}
        for key, value in user_data.items():
            if hasattr(value, 'isoformat'):
                serializable_user_data[key] = value.isoformat()
            else:
                serializable_user_data[key] = value

        message = {
            'event_type': 'user_registered',
            'user_id': serializable_user_data['id'],
            'email': serializable_user_data.get('email'),
            'first_name': serializable_user_data.get('first_name'),
            'timestamp': datetime.utcnow().isoformat(),
            'data': serializable_user_data
        }

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
        user_data: UserCreate = None,
        email: Optional[str] = Form(None),
        phone: Optional[str] = Form(None),
        username: Optional[str] = Form(None),
        password: str = Form(...),
        first_name: str = Form(...),
        last_name: str = Form(...),
        country_id: int = Form(1),
        background_tasks: BackgroundTasks = None,
        request: Request = None,
        response: Response = None
):
    try:
        config.refresh_cache()
        logger.info(f"DEBUG: Maintenance mode value: {config.maintenance_mode}, type: {type(config.maintenance_mode)}")
        if config.maintenance_mode:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Service is under maintenance. Registration is temporarily unavailable."
            )

        # Use form data if provided, otherwise use UserCreate object
        if user_data:
            email = user_data.email
            phone = user_data.phone
            username = user_data.username
            password = user_data.password
            first_name = user_data.first_name
            last_name = user_data.last_name
            country_id = user_data.country_id or 1

        logger.info(f"🔄 Processing registration for: {email or phone or username}")

        # Sanitize inputs
        first_name = sanitize_input(first_name)
        last_name = sanitize_input(last_name)

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

        logger.info(f"🔄 Processing registration with Argon2 hashing")

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

            password_hash = get_password_hash(password)
            logger.info(f"🔐 Password hashed successfully")

            # Insert user
            cursor.execute("""
                INSERT INTO users (email, phone, username, password_hash, first_name, last_name, country_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (email, phone, username, password_hash, first_name, last_name, country_id))
            user_id = cursor.lastrowid
            logger.info(f"✅ User created with ID: {user_id}")

            # Assign customer role by default
            cursor.execute("SELECT id FROM user_roles WHERE name = 'customer'")
            role = cursor.fetchone()
            if role:
                cursor.execute("""
                    INSERT INTO user_role_assignments (user_id, role_id, assigned_by)
                    VALUES (%s, %s, %s)
                """, (user_id, role['id'], user_id))
                logger.info(f"✅ Customer role assigned to user {user_id}")

            # Enable email notifications by default
            cursor.execute("""
                INSERT INTO user_notification_preferences (user_id, notification_method, is_enabled)
                VALUES (%s, 'email', TRUE)
                ON DUPLICATE KEY UPDATE is_enabled = TRUE
            """, (user_id,))
            logger.info(f"✅ Email notifications enabled for user {user_id}")

            # Get user roles and permissions
            cursor.execute("""
                SELECT
                    ur.name as role_name,
                    p.name as permission_name
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

            # Ensure customer role is present
            if not roles:
                roles.add('customer')

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

            # Get user data for event publishing
            cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
            user = cursor.fetchone()

            # SESSION MANAGEMENT: Create user session
            if request:
                try:
                    # Get current session (might be guest session)
                    current_session = get_session(request)
                    current_session_id = get_session_id(request)

                    # Create new user session
                    session_data = {
                        'session_type': SessionType.USER,
                        'user_id': user_id,
                        'guest_id': None,
                        'ip_address': request.client.host if request.client else 'unknown',
                        'user_agent': request.headers.get("user-agent"),
                        'cart_items': current_session.cart_items if current_session else {}
                    }

                    new_session = session_service.create_session(session_data)

                    if new_session and response:
                        # Set session cookie
                        response.set_cookie(
                            key="session_id",
                            value=new_session.session_id,
                            max_age=86400,  # 24 hours
                            httponly=True,
                            secure=not config.debug_mode,
                            samesite="lax"
                        )
                        logger.info(f"✅ User session created for new user {user_id}")

                    # Delete old guest session if it existed
                    if current_session_id and current_session and current_session.session_type == SessionType.GUEST:
                        session_service.delete_session(current_session_id)

                except Exception as e:
                    logger.error(f"❌ Session creation failed during registration: {e}")
                    # Continue without session - registration should still succeed

            # Publish registration event in background
            if background_tasks:
                background_tasks.add_task(
                    publish_user_registration_event,
                    user
                )

            logger.info(f"✅ User registered successfully: {email or phone or username}")
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
        logger.error(f"❌ Registration failed: {str(e)}")
        logger.error(f"❌ Error type: {type(e).__name__}")
        import traceback
        logger.error(f"❌ Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed due to server error"
        )


@router.get("/site-settings")
async def get_site_settings(current_user: dict = Depends(get_current_user)):
    # Manual role check
    user_roles = current_user.get('roles', [])
    if 'admin' not in user_roles and 'super_admin' not in user_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )

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
            'free_shipping_threshold': getattr(config, 'free_shipping_threshold', 0),
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


@router.get("/frontend-settings")
async def get_frontend_settings():
    try:
        config.refresh_cache()
        frontend_settings = {
            'site_name': config.site_name,
            'currency': config.currency,
            'currency_symbol': config.currency_symbol,
            'min_order_amount': config.min_order_amount,
            'free_shipping_min_amount': config.free_shipping_min_amount,
            'free_shipping_threshold': getattr(config, 'free_shipping_threshold', 0),
            'return_period_days': getattr(config, 'return_period_days', 10),
            'enable_reviews': config.enable_reviews,
            'enable_wishlist': config.enable_wishlist,
            'enable_guest_checkout': config.enable_guest_checkout,
            'site_phone': getattr(config, 'site_phone', '+91-9711317009'),
            'site_email': getattr(config, 'site_email', 'support@pavitraenterprises.com'),
            'business_hours': getattr(config, 'business_hours', {
                'monday_friday': '9am-6pm',
                'saturday': '10am-4pm',
                'sunday': 'Closed'
            })
        }
        return frontend_settings
    except Exception as e:
        logger.error(f"Failed to fetch frontend settings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch frontend settings"
        )


@router.post("/login")
async def login_user(
        login_data: UserLogin,
        request: Request = None,
        response: Response = None
):
    try:
        config.refresh_cache()
        logger.info(f"DEBUG: Maintenance mode value: {config.maintenance_mode}, type: {type(config.maintenance_mode)}")
        if config.maintenance_mode:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Service is under maintenance. Please try again later."
            )

        logger.info(f"🔐 Login attempt for: {login_data.login_id}")

        with db.get_cursor() as cursor:
            # Enhanced query to find user by email, phone, or username
            cursor.execute("""
                SELECT
                    id, email, password_hash, first_name, last_name,
                    is_active, email_verified, phone_verified
                FROM users
                WHERE email = %s OR phone = %s OR username = %s
            """, (login_data.login_id, login_data.login_id, login_data.login_id))
            user = cursor.fetchone()

            if not user:
                logger.warning(f"❌ User not found: {login_data.login_id}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid credentials"
                )

            logger.info(f"✅ User found: {user['email']}, checking password...")

            # Verify password
            if not verify_password(login_data.password, user['password_hash']):
                logger.warning(f"❌ Invalid password for user: {user['email']}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid credentials"
                )

            if not user['is_active']:
                logger.warning(f"❌ Account deactivated: {user['email']}")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Account is deactivated"
                )

            # Get user roles and permissions
            cursor.execute("""
                SELECT
                    ur.name as role_name,
                    p.name as permission_name
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

            # Ensure customer role is assigned
            if not roles:
                roles.add('customer')
                logger.info(f"✅ Assigned default customer role to user {user['id']}")

            # Create access token
            access_token = create_access_token(
                data={
                    "sub": str(user['id']),
                    "email": user['email'],
                    "roles": list(roles),
                    "permissions": list(permissions)
                },
                expires_delta=timedelta(hours=24)
            )

            # SESSION MANAGEMENT: Create user session
            if request:
                try:
                    # Get current session (might be guest session)
                    current_session = get_session(request)
                    current_session_id = get_session_id(request)

                    # Create new user session
                    session_data = {
                        'session_type': SessionType.USER,
                        'user_id': user['id'],
                        'guest_id': None,
                        'ip_address': request.client.host if request.client else 'unknown',
                        'user_agent': request.headers.get("user-agent"),
                        'cart_items': current_session.cart_items if current_session else {}
                    }

                    new_session = session_service.create_session(session_data)

                    if new_session and response:
                        # Set session cookie
                        response.set_cookie(
                            key="session_id",
                            value=new_session.session_id,
                            max_age=86400,  # 24 hours
                            httponly=True,
                            secure=not config.debug_mode,
                            samesite="lax"
                        )
                        logger.info(f"✅ User session created for user {user['id']}")

                    # Delete old guest session if it existed
                    if current_session_id and current_session and current_session.session_type == SessionType.GUEST:
                        session_service.delete_session(current_session_id)

                except Exception as e:
                    logger.error(f"❌ Session creation failed during login: {e}")
                    # Continue without session - login should still succeed

            # Update last login
            cursor.execute("UPDATE users SET last_login = NOW() WHERE id = %s", (user['id'],))
            logger.info(f"✅ Login successful for user: {user['email']}")

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
        logger.error(f"❌ Login failed: {str(e)}")
        logger.error(f"❌ Error type: {type(e).__name__}")
        import traceback
        logger.error(f"❌ Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed due to server error"
        )


@router.post("/logout")
async def logout_user(
        request: Request,
        response: Response,
        current_user: dict = Depends(get_current_user)
):
    try:
        user_id = current_user['sub']

        # Invalidate JWT token
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:]
            blacklist_token(token)
            logger.info(f"✅ JWT token invalidated for user {user_id}")

        # SESSION MANAGEMENT: Delete user session
        session_id = get_session_id(request)
        if session_id:
            session_service.delete_session(session_id)
            logger.info(f"✅ Session deleted for user {user_id}")

        # Clear session cookie
        response.delete_cookie("session_id")

        logger.info(f"✅ User {user_id} logged out successfully")
        return {"message": "Logged out successfully"}

    except Exception as e:
        logger.error(f"❌ Logout failed: {e}")
        # Still return success even if some cleanup failed
        return {"message": "Logged out successfully"}


@router.post("/refresh")
async def refresh_token(
        request: Request,
        response: Response = None
):
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

    # SESSION MANAGEMENT: Refresh session activity
    session_id = get_session_id(request)
    if session_id:
        session_service.update_session_activity(session_id)
        logger.info(f"✅ Session activity refreshed for user {payload['sub']}")

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

    logger.info(f"✅ Token refreshed successfully for user {payload['sub']}")
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
                redis_client.setex(
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
        stored_token = redis_client.get(f"password_reset:{user_id}")
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
            redis_client.delete(f"password_reset:{user_id}")
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
    try:
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
    config.refresh_cache()
    return {
        "maintenance_mode": config.maintenance_mode,
        "maintenance_mode_type": str(type(config.maintenance_mode)),
        "maintenance_mode_raw": str(config.maintenance_mode)
    }


@router.get("/debug/settings")
async def debug_settings():
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


# New session-related endpoints
@router.get("/session/info")
async def get_session_info(request: Request, current_user: dict = Depends(get_current_user)):
    """Get current session information"""
    try:
        session = get_session(request)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        return {
            "session_id": session.session_id,
            "session_type": session.session_type,
            "user_id": session.user_id,
            "guest_id": session.guest_id,
            "created_at": session.created_at,
            "last_activity": session.last_activity,
            "expires_at": session.expires_at,
            "cart_items_count": len(session.cart_items) if session.cart_items else 0
        }
    except Exception as e:
        logger.error(f"Failed to get session info: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get session information"
        )


@router.post("/session/refresh")
async def refresh_user_session(request: Request, response: Response):
    """Refresh session activity and extend expiration"""
    try:
        session_id = get_session_id(request)
        if not session_id:
            raise HTTPException(status_code=404, detail="Session not found")

        success = session_service.update_session_activity(session_id)
        if not success:
            raise HTTPException(status_code=404, detail="Session not found")

        return {"message": "Session refreshed successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to refresh session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to refresh session"
        )