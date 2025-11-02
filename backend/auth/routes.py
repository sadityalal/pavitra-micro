from fastapi import APIRouter, HTTPException, Depends, Form, Request, status, BackgroundTasks, Response
from typing import Optional, List
import time
import json
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

def blacklist_token(token: str, expire: int = 86400):
    """Blacklist a JWT token to prevent reuse"""
    try:
        # FIX: Use enhanced Redis client
        success = redis_client.setex(
            f"token_blacklist:{token}",
            expire,
            "blacklisted"
        )
        if success:
            logger.info(f"Token blacklisted successfully")
        else:
            logger.error(f"Failed to blacklist token in Redis")
        return success
    except Exception as e:
        logger.error(f"Failed to blacklist token: {e}")
        return False

def is_token_blacklisted(token: str) -> bool:
    """Check if a token is blacklisted"""
    try:
        return redis_client.exists(f"token_blacklist:{token}")
    except Exception as e:
        logger.error(f"Failed to check token blacklist: {e}")
        return False

def get_client_identifier(request: Request) -> str:
    """Get unique identifier for client for rate limiting"""
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")
    return f"{client_ip}:{hash(user_agent) % 10000}"


def check_rate_limit(key: str, max_attempts: int, window_seconds: int) -> bool:
    """Check if rate limit is exceeded"""
    try:
        current_time = int(time.time())
        window_start = current_time // window_seconds
        rate_key = f"rate_limit:{key}:{window_start}"

        current_attempts = redis_client.incr(rate_key)
        if current_attempts == 1:
            redis_client.expire(rate_key, window_seconds)

        return current_attempts <= max_attempts
    except Exception as e:
        logger.error(f"Rate limit check failed: {e}")
        return True  # Fail open


def track_failed_login(identifier: str, max_attempts: int = 5, lockout_minutes: int = 15):
    """Track failed login attempts and implement lockout"""
    try:
        fail_key = f"login_fails:{identifier}"
        lockout_key = f"login_lockout:{identifier}"

        # Check if already locked out
        if redis_client.exists(lockout_key):
            return False

        # Increment failure count
        failures = redis_client.incr(fail_key)
        if failures == 1:
            redis_client.expire(fail_key, 3600)  # 1 hour TTL for failure count

        # Lockout if max attempts reached
        if failures >= max_attempts:
            redis_client.setex(lockout_key, lockout_minutes * 60, "locked")
            redis_client.delete(fail_key)  # Reset failure count
            return False

        return True
    except Exception as e:
        logger.error(f"Failed login tracking error: {e}")
        return True


def reset_failed_login(identifier: str):
    """Reset failed login attempts on successful login"""
    try:
        redis_client.delete(f"login_fails:{identifier}")
        redis_client.delete(f"login_lockout:{identifier}")
    except Exception as e:
        logger.error(f"Failed to reset login attempts: {e}")


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

        if user_data:
            email = user_data.email
            phone = user_data.phone
            username = user_data.username
            password = user_data.password
            first_name = user_data.first_name
            last_name = user_data.last_name
            country_id = user_data.country_id or 1

        logger.info(f"🔄 Processing registration for: {email or phone or username}")
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

        common_passwords = ['password', '12345678', 'qwerty', 'admin', 'letmein']
        if password.lower() in common_passwords:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password is too common. Please choose a stronger password."
            )

        logger.info(f"🔄 Processing registration with Argon2 hashing")
        with db.get_cursor() as cursor:
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
            cursor.execute("""
                INSERT INTO users (email, phone, username, password_hash, first_name, last_name, country_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (email, phone, username, password_hash, first_name, last_name, country_id))
            user_id = cursor.lastrowid
            logger.info(f"✅ User created with ID: {user_id}")

            cursor.execute("SELECT id FROM user_roles WHERE name = 'customer'")
            role = cursor.fetchone()
            if role:
                cursor.execute("""
                    INSERT INTO user_role_assignments (user_id, role_id, assigned_by)
                    VALUES (%s, %s, %s)
                """, (user_id, role['id'], user_id))
                logger.info(f"✅ Customer role assigned to user {user_id}")

            cursor.execute("""
                INSERT INTO user_notification_preferences (user_id, notification_method, is_enabled)
                VALUES (%s, 'email', TRUE)
                ON DUPLICATE KEY UPDATE is_enabled = TRUE
            """, (user_id,))
            logger.info(f"✅ Email notifications enabled for user {user_id}")

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

            if not roles:
                roles.add('customer')

            access_token = create_access_token(
                data={
                    "sub": str(user_id),
                    "email": email,
                    "roles": list(roles),
                    "permissions": list(permissions)
                },
                expires_delta=timedelta(hours=24)
            )

            # SESSION MANAGEMENT: Create user session and transfer cart
            if request:
                try:
                    current_session = get_session(request)
                    current_session_id = get_session_id(request)

                    # Start with empty cart for the new user session
                    user_cart_items = {}

                    # If there's a guest session with cart items, transfer them to user session
                    if current_session and current_session.session_type == SessionType.GUEST:
                        if current_session.cart_items:
                            user_cart_items = current_session.cart_items.copy()
                            logger.info(
                                f"✅ Migrated guest cart to user session during registration: {len(user_cart_items)} items")

                    # Create new user session with the transferred cart
                    session_data = {
                        'session_type': SessionType.USER,
                        'user_id': user_id,
                        'guest_id': None,
                        'ip_address': request.client.host if request.client else 'unknown',
                        'user_agent': request.headers.get("user-agent"),
                        'cart_items': user_cart_items  # This preserves the cart
                    }

                    new_session = session_service.create_session(session_data)

                    if new_session and response:
                        response.set_cookie(
                            key="session_id",
                            value=new_session.session_id,
                            max_age=86400,
                            httponly=True,
                            secure=not config.debug_mode,
                            samesite="lax",
                            path="/"
                        )
                        logger.info(
                            f"✅ User session created for new user {user_id} with cart: {len(user_cart_items)} items")

                    # Delete the old guest session after successful transfer
                    if current_session_id and current_session and current_session.session_type == SessionType.GUEST:
                        session_service.delete_session(current_session_id)
                        logger.info(f"✅ Deleted guest session after successful registration migration")

                except Exception as e:
                    logger.error(f"❌ Session creation failed during registration: {e}")

            if background_tasks:
                cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
                user = cursor.fetchone()
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

        client_identifier = get_client_identifier(request)
        if not check_rate_limit(f"login:{client_identifier}", max_attempts=10,
                                window_seconds=900):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many login attempts. Please try again later."
            )

        if not track_failed_login(client_identifier):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Account temporarily locked due to too many failed attempts. Please try again in 15 minutes."
            )

        logger.info(f"🔐 Login attempt for: {login_data.login_id}")
        with db.get_cursor() as cursor:
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

            reset_failed_login(client_identifier)

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

            if not roles:
                roles.add('customer')
                logger.info(f"✅ Assigned default customer role to user {user['id']}")

            access_token = create_access_token(
                data={
                    "sub": str(user['id']),
                    "email": user['email'],
                    "roles": list(roles),
                    "permissions": list(permissions)
                },
                expires_delta=timedelta(hours=24)
            )

            # ENHANCED SESSION MANAGEMENT: Create user session and preserve cart
            if request:
                try:
                    current_session = get_session(request)
                    current_session_id = get_session_id(request)

                    # Start with empty cart for the new user session
                    user_cart_items = {}

                    # STEP 1: Try to recover preserved cart from Redis first (from previous logout)
                    try:
                        preserved_cart_data = redis_client.get(f"preserved_cart:{user['id']}")
                        if preserved_cart_data:
                            user_cart_items = json.loads(preserved_cart_data)  # This needs json import
                            logger.info(
                                f"🛒 Recovered preserved cart for user {user['id']}: {len(user_cart_items)} items")
                            # Clean up the preserved cart data after recovery
                            redis_client.delete(f"preserved_cart:{user['id']}")
                            logger.info(f"✅ Cleared preserved cart data for user {user['id']}")
                    except Exception as e:
                        logger.error(f"❌ Failed to recover preserved cart from Redis: {e}")

                    # STEP 2: If no preserved cart, check for existing user session cart
                    if not user_cart_items:
                        existing_user_session = session_service.get_session_by_user_id(user['id'])
                        if existing_user_session and existing_user_session.cart_items:
                            user_cart_items = existing_user_session.cart_items.copy()
                            logger.info(f"🛒 Using existing user session cart: {len(user_cart_items)} items")

                    # STEP 3: If still no cart, check for guest session cart migration
                    if not user_cart_items and current_session and current_session.session_type == SessionType.GUEST:
                        if current_session.cart_items:
                            user_cart_items = current_session.cart_items.copy()
                            logger.info(
                                f"✅ Migrated guest cart to user session during login: {len(user_cart_items)} items")

                    # STEP 4: Create new user session with the recovered/migrated cart
                    session_data = {
                        'session_type': SessionType.USER,
                        'user_id': user['id'],
                        'guest_id': None,
                        'ip_address': request.client.host if request.client else 'unknown',
                        'user_agent': request.headers.get("user-agent"),
                        'cart_items': user_cart_items  # This preserves the cart from any source
                    }

                    new_session = session_service.create_session(session_data)
                    if new_session and response:
                        response.set_cookie(
                            key="session_id",
                            value=new_session.session_id,
                            max_age=86400,
                            httponly=True,
                            secure=not config.debug_mode,
                            samesite="lax",
                            path="/"
                        )
                        logger.info(
                            f"✅ User session created for user {user['id']} with cart: {len(user_cart_items)} items")

                    # STEP 5: Clean up old sessions
                    # Delete current guest session if it exists
                    if current_session_id and current_session and current_session.session_type == SessionType.GUEST:
                        session_service.delete_session(current_session_id)
                        logger.info(f"✅ Deleted guest session after successful login migration")

                    # Delete any other existing user sessions for this user (prevent multiple sessions)
                    try:
                        all_user_sessions = session_service.get_all_user_sessions(user['id'])
                        for old_session in all_user_sessions:
                            if old_session.session_id != new_session.session_id:
                                session_service.delete_session(old_session.session_id)
                                logger.info(f"✅ Deleted duplicate user session: {old_session.session_id}")
                    except Exception as e:
                        logger.warning(f"Could not clean up duplicate sessions: {e}")

                except Exception as e:
                    logger.error(f"❌ Session creation failed during login: {e}")
                    # Don't fail the login if session creation fails, but log it
                    # User can still login but might have cart issues

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
        auth_header = request.headers.get("Authorization")

        # Preserve cart data before deleting session
        session_id = get_session_id(request)
        preserved_cart = {}

        if session_id:
            # Get current session to preserve cart
            current_session = session_service.get_session(session_id)
            if current_session and current_session.cart_items:
                preserved_cart = current_session.cart_items.copy()
                logger.info(f"🛒 Preserving cart with {len(preserved_cart)} items during logout for user {user_id}")

            # Delete the session but preserve cart data for future sessions
            session_service.delete_session(session_id)
            logger.info(f"✅ Session deleted for user {user_id}")

        # Store preserved cart in Redis for future login
        if preserved_cart:
            try:
                # Use your Redis client's setex method with JSON serialization
                success = redis_client.setex(
                    f"preserved_cart:{user_id}",
                    86400,  # 24 hours expiration
                    json.dumps(preserved_cart)
                )
                if success:
                    logger.info(f"💾 Cart data preserved in Redis for user {user_id}")
                else:
                    logger.error(f"❌ Failed to preserve cart in Redis for user {user_id}")
            except Exception as e:
                logger.error(f"❌ Failed to preserve cart in Redis: {e}")

        # Blacklist JWT token
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:]
            blacklist_token(token)
            logger.info(f"✅ JWT token invalidated for user {user_id}")

        # Clear session cookie
        response.delete_cookie(
            key="session_id",
            path="/",
            secure=not config.debug_mode,
            httponly=True,
            samesite="lax"
        )

        logger.info(f"✅ User {user_id} logged out successfully (cart preserved)")
        return {"message": "Logged out successfully"}

    except Exception as e:
        logger.error(f"❌ Logout failed: {e}")
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

        # FIX: Verify token first to avoid unnecessary database operations
        payload = verify_token(token)
        if not payload or payload.get('type') != 'password_reset':
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid reset token"
            )

        user_id = int(payload['sub'])

        # FIX: Use the enhanced Redis client methods
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
            cursor.execute(
                "INSERT INTO password_history (user_id, password_hash) VALUES (%s, %s)",
                (user_id, new_password_hash)
            )

            # FIX: Delete the token AFTER successful password change
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