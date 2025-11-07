from fastapi import APIRouter, HTTPException, Depends, Form, Request, status, BackgroundTasks, Response
from typing import Optional, List
import time
import json
from datetime import datetime, timedelta
import re
import hashlib
import uuid
from shared import (
    config, db, verify_password, get_password_hash,
    create_access_token, verify_token, validate_email,
    validate_phone, sanitize_input, get_logger, rabbitmq_client, redis_client
)
from shared.auth_middleware import get_current_user, require_roles, blacklist_token
from shared.session_service import session_service, SessionType
from shared.session_middleware import get_session, get_session_id, is_new_session
from shared.security import validate_password_strength
from .models import (
    UserCreate, UserLogin, Token, UserResponse,
    RoleResponse, PermissionCheck, HealthResponse
)

router = APIRouter()
logger = get_logger(__name__)


def get_client_identifier(request: Request) -> str:
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")
    user_agent_hash = hashlib.sha256(user_agent.encode()).hexdigest()[:8]
    return f"{client_ip}:{user_agent_hash}"

def check_rate_limit(key: str) -> bool:
    try:
        session_config = config.get_session_config()
        max_attempts = session_config['rate_limit_login_attempts']
        window_seconds = session_config['rate_limit_login_window']
        current_time = int(time.time())
        window_start = current_time // window_seconds
        rate_key = f"auth_rate_limit:{key}:{window_start}"
        current_attempts = redis_client.incr(rate_key)
        if current_attempts == 1:
            redis_client.expire(rate_key, window_seconds)
        return current_attempts <= max_attempts
    except Exception as e:
        logger.error(f"Rate limit check failed: {e}")
        return True


def track_failed_login(identifier: str) -> bool:
    try:
        session_config = config.get_session_config()
        max_attempts = session_config['max_login_attempts']
        lockout_minutes = session_config['login_lockout_minutes']
        failed_window = session_config['failed_attempts_window']
        fail_key = f"login_fails:{identifier}"
        lockout_key = f"login_lockout:{identifier}"
        if redis_client.exists(lockout_key):
            return False
        failures = redis_client.incr(fail_key)
        if failures == 1:
            redis_client.expire(fail_key, failed_window)
        if failures >= max_attempts:
            redis_client.setex(lockout_key, lockout_minutes * 60, "locked")
            redis_client.delete(fail_key)
            return False
        return True
    except Exception as e:
        logger.error(f"Failed login tracking error: {e}")
        return True


def reset_failed_login(identifier: str):
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
                logger.info(f"User registration event published for user {serializable_user_data['id']}")
            else:
                logger.error(f"Failed to publish user registration event for user {serializable_user_data['id']}")
        else:
            logger.error("Cannot publish user registration event - RabbitMQ not connected")
    except Exception as e:
        logger.error(f"Failed to publish user registration event: {e}")


def migrate_guest_cart_to_user_database(guest_session, user_id: int, cursor) -> int:
    try:
        if not guest_session or not guest_session.cart_items:
            return 0

        migrated_count = 0
        guest_cart_items = guest_session.cart_items.copy()

        # First, get user's existing cart items to avoid duplicates
        cursor.execute("""
            SELECT product_id, variation_id, quantity 
            FROM shopping_cart 
            WHERE user_id = %s
        """, (user_id,))
        existing_user_items = {(row['product_id'], row['variation_id']): row['quantity'] for row in cursor.fetchall()}

        for item_key, item_data in guest_cart_items.items():
            try:
                product_id = item_data['product_id']
                variation_id = item_data.get('variation_id')
                quantity = item_data['quantity']

                # Check if user already has this item
                existing_quantity = existing_user_items.get((product_id, variation_id), 0)

                cursor.execute(
                    "SELECT id, stock_quantity, max_cart_quantity FROM products WHERE id = %s AND status = 'active'",
                    (product_id,)
                )
                product = cursor.fetchone()
                if not product:
                    continue

                max_quantity = product['max_cart_quantity'] or 20
                available_quantity = min(quantity, product['stock_quantity']) if product[
                                                                                     'stock_quantity'] > 0 else quantity

                # Calculate new quantity without exceeding max
                new_quantity = min(existing_quantity + available_quantity, max_quantity)

                if existing_quantity > 0:
                    # Update existing item
                    cursor.execute("""
                        UPDATE shopping_cart
                        SET quantity = %s, updated_at = NOW()
                        WHERE user_id = %s AND product_id = %s
                        AND (variation_id = %s OR (variation_id IS NULL AND %s IS NULL))
                    """, (new_quantity, user_id, product_id, variation_id, variation_id))
                else:
                    # Insert new item
                    cursor.execute("""
                        INSERT INTO shopping_cart (user_id, product_id, variation_id, quantity)
                        VALUES (%s, %s, %s, %s)
                    """, (user_id, product_id, variation_id, available_quantity))

                migrated_count += 1
                logger.info(f"Migrated cart item: product {product_id}, quantity {available_quantity}")

            except Exception as e:
                logger.error(f"Failed to migrate cart item {item_key}: {e}")
                continue

        return migrated_count

    except Exception as e:
        logger.error(f"Cart migration failed: {e}")
        return 0


def _validate_registration_data(email: Optional[str], phone: Optional[str], username: Optional[str],
                                password: str) -> None:
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
    password_validation = validate_password_strength(password)
    if not password_validation["valid"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=password_validation["message"]
        )


def _check_existing_users(cursor, email: Optional[str], phone: Optional[str], username: Optional[str]) -> None:
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

def _setup_user_account(cursor, user_id: int) -> tuple[list, list]:
    cursor.execute("SELECT id FROM user_roles WHERE name = 'customer'")
    role = cursor.fetchone()
    if role:
        cursor.execute("""
            INSERT INTO user_role_assignments (user_id, role_id, assigned_by)
            VALUES (%s, %s, %s)
        """, (user_id, role['id'], user_id))
        logger.info(f"Customer role assigned to user {user_id}")
    cursor.execute("""
        INSERT INTO user_notification_preferences (user_id, notification_method, is_enabled)
        VALUES (%s, 'email', TRUE)
        ON DUPLICATE KEY UPDATE is_enabled = TRUE
    """, (user_id,))
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
    return list(roles), list(permissions)


@router.post("/register", response_model=Token)
async def register_user(
        user_data: UserCreate,
        background_tasks: BackgroundTasks = None,
        request: Request = None,
        response: Response = None
):
    try:
        config.refresh_cache()
        if config.maintenance_mode:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Service is under maintenance. Registration is temporarily unavailable."
            )

        # Extract data from UserCreate object (JSON)
        email = user_data.email
        phone = user_data.phone
        username = user_data.username
        password = user_data.password
        first_name = user_data.first_name
        last_name = user_data.last_name
        country_id = user_data.country_id or 1
        auth_type = user_data.auth_type

        logger.info(f"Processing registration for: {email or phone or username}")

        first_name = sanitize_input(first_name)
        last_name = sanitize_input(last_name)

        _validate_registration_data(email, phone, username, password)

        with db.get_cursor() as cursor:
            _check_existing_users(cursor, email, phone, username)

            password_hash = get_password_hash(password)
            cursor.execute("""
                INSERT INTO users (email, phone, username, password_hash, first_name, last_name, country_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (email, phone, username, password_hash, first_name, last_name, country_id))
            user_id = cursor.lastrowid
            logger.info(f"User created with ID: {user_id}")

            roles, permissions = _setup_user_account(cursor, user_id)

            # Get IP and user agent for session
            ip_address = request.client.host if request.client else 'unknown'
            user_agent = request.headers.get("user-agent", "")

            # Get or create user session - ONE SESSION PER USER
            user_session = session_service.get_or_create_user_session(user_id, ip_address, user_agent)
            if not user_session:
                logger.error(f"Failed to create user session for user {user_id}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create user session"
                )

            logger.info(f"✅ Created/retrieved user session: {user_session.session_id} for user {user_id}")

            # ENHANCED CART MIGRATION LOGIC FOR REGISTRATION
            current_session = get_session(request)
            migrated_items_count = 0

            # Method 1: Check current session from middleware
            if current_session and current_session.session_type == SessionType.GUEST:
                if current_session.cart_items:
                    migrated_items_count = migrate_guest_cart_to_user_database(
                        current_session, user_id, cursor
                    )
                    logger.info(
                        f"🔄 Registration - Method 1: Migrated {migrated_items_count} cart items from current guest session")
                    # Clear the guest session cart after migration
                    session_service.update_session_data(current_session.session_id, {
                        'cart_items': {}
                    })

            # Method 2: If no session found or no items migrated, search by IP and User-Agent
            if migrated_items_count == 0:
                guest_session = session_service.find_guest_session_by_ip(ip_address, user_agent)
                if guest_session and guest_session.cart_items:
                    additional_migrated = migrate_guest_cart_to_user_database(
                        guest_session, user_id, cursor
                    )
                    migrated_items_count += additional_migrated
                    logger.info(
                        f"🔄 Registration - Method 2: Migrated {additional_migrated} cart items from IP-based guest session")
                    # Clear the guest session cart after migration
                    session_service.update_session_data(guest_session.session_id, {
                        'cart_items': {}
                    })

            # Method 3: Check guest_id cookie as fallback
            if migrated_items_count == 0:
                guest_id = request.cookies.get("guest_id")
                if guest_id:
                    guest_session = session_service.get_session_by_guest_id(guest_id)
                    if guest_session and guest_session.cart_items:
                        additional_migrated = migrate_guest_cart_to_user_database(
                            guest_session, user_id, cursor
                        )
                        migrated_items_count += additional_migrated
                        logger.info(
                            f"🔄 Registration - Method 3: Migrated {additional_migrated} cart items from guest_id-based session")

            # Update user session with migrated cart if any items were migrated
            if migrated_items_count > 0:
                # Refresh user session cart data from database
                cursor.execute("""
                    SELECT
                        sc.product_id,
                        sc.variation_id,
                        sc.quantity
                    FROM shopping_cart sc
                    JOIN products p ON sc.product_id = p.id
                    WHERE sc.user_id = %s AND p.status = 'active'
                """, (user_id,))
                user_cart_items = cursor.fetchall()

                # Convert to session cart format
                session_cart_items = {}
                for item in user_cart_items:
                    item_key = f"{item['product_id']}_{item['variation_id']}" if item['variation_id'] else str(
                        item['product_id'])
                    session_cart_items[item_key] = {
                        'product_id': item['product_id'],
                        'variation_id': item['variation_id'],
                        'quantity': item['quantity']
                    }

                session_service.update_session_data(user_session.session_id, {
                    'cart_items': session_cart_items
                })

                logger.info(
                    f"✅ Registration - Total {migrated_items_count} cart items migrated successfully for user {user_id}")

            if user_session and response:
                session_config = config.get_session_config()
                session_timeout = session_config.get('user_session_duration', 2592000)
                response.set_cookie(
                    key="session_id",
                    value=user_session.session_id,
                    max_age=session_timeout,
                    httponly=True,
                    secure=not config.debug_mode,
                    samesite="Lax",
                    path="/"
                )
                request.state.session = user_session
                request.state.session_id = user_session.session_id
                logger.info(f"Set user session cookie for user {user_id}: {user_session.session_id}")

            if background_tasks:
                cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
                user = cursor.fetchone()
                background_tasks.add_task(
                    publish_user_registration_event,
                    user
                )

            session_config = config.get_session_config()
            token_expiry_hours = session_config['token_expiry_hours']
            access_token = create_access_token(
                data={
                    "sub": str(user_id),
                    "email": email,
                    "roles": roles,
                    "permissions": permissions
                },
                expires_delta=timedelta(hours=token_expiry_hours)
            )

            logger.info(
                f"User registered successfully: {email or phone or username} with {migrated_items_count} cart items migrated")

            return Token(
                access_token=access_token,
                token_type="bearer",
                expires_in=token_expiry_hours * 3600,
                user_roles=roles,
                user_permissions=permissions
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed due to server error"
        )


@router.get("/site-settings")
async def get_site_settings(current_user: dict = Depends(get_current_user)):
    user_roles = current_user.get('roles', [])
    if 'admin' not in user_roles and 'super_admin' not in user_roles and 'manager' not in user_roles:
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
            'free_shipping_threshold': config.free_shipping_threshold,
            'return_period_days': config.return_period_days,
            'site_phone': config.site_phone,
            'site_email': config.site_email,
            'business_hours': config.business_hours,
            'max_cart_quantity_per_product': config.max_cart_quantity_per_product,
            'max_cart_items_total': config.max_cart_items_total,
            'cart_session_timeout_minutes': config.cart_session_timeout_minutes,
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
            'debug_mode': config.debug_mode
        }
        return settings
    except Exception as e:
        logger.error(f"Failed to fetch site settings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch site settings"
        )


@router.get("/admin/all-settings")
async def get_all_settings(current_user: dict = Depends(get_current_user)):
    user_roles = current_user.get('roles', [])
    allowed_roles = ['admin', 'super_admin', 'manager']
    if not any(role in user_roles for role in allowed_roles):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin, super_admin, or manager access required"
        )

    try:
        config.refresh_cache()
        all_settings = {
            'site_settings': {
                'enable_reviews': config.enable_reviews,
                'enable_wishlist': config.enable_wishlist,
                'enable_guest_checkout': config.enable_guest_checkout,
                'max_cart_quantity_per_product': config.max_cart_quantity_per_product,
                'max_cart_items_total': config.max_cart_items_total,
                'cart_session_timeout_minutes': config.cart_session_timeout_minutes,
                'debug_mode': config.debug_mode,
                'app_debug': config.app_debug,
                'log_level': config.log_level,
                'cors_origins': config.cors_origins,
                'rate_limit_requests': config.rate_limit_requests,
                'rate_limit_window': config.rate_limit_window,
                'razorpay_test_mode': config.razorpay_test_mode,
                'stripe_test_mode': config.stripe_test_mode,
                'razorpay_key_id': config.razorpay_key_id,
                'razorpay_secret': config.razorpay_secret,
                'stripe_publishable_key': config.stripe_publishable_key,
                'stripe_secret_key': config.stripe_secret_key,
                'email_notifications': config.email_notifications,
                'sms_notifications': config.sms_notifications,
                'push_notifications': config.push_notifications,
                'telegram_notifications': config.telegram_notifications,
                'whatsapp_notifications': config.whatsapp_notifications,
                'max_upload_size': config.max_upload_size,
                'allowed_file_types': config.allowed_file_types,
                'refund_policy_days': config.refund_policy_days,
                'auto_refund_enabled': config.auto_refund_enabled,
                'refund_processing_fee': config.refund_processing_fee,
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
                'telegram_bot_token': config.telegram_bot_token,
                'telegram_chat_id': config.telegram_chat_id,
                'whatsapp_api_url': config.whatsapp_api_url,
                'whatsapp_api_token': config.whatsapp_api_token,
                'maintenance_mode': config.maintenance_mode
            },
            'frontend_settings': {
                'app_name': config.app_name,
                'app_description': config.app_description,
                'email_from': config.email_from,
                'email_from_name': config.email_from_name,
                'default_currency': config.default_currency,
                'supported_currencies': config.supported_currencies,
                'default_country': config.default_country,
                'default_gst_rate': config.default_gst_rate,
                'site_name': config.site_name,
                'site_description': config.site_description,
                'currency': config.currency,
                'currency_symbol': config.currency_symbol,
                'site_phone': config.site_phone,
                'site_email': config.site_email,
                'business_hours': config.business_hours,
                'min_order_amount': config.min_order_amount,
                'free_shipping_min_amount': config.free_shipping_min_amount,
                'free_shipping_threshold': config.free_shipping_threshold,
                'return_period_days': config.return_period_days
            },
            'environment_settings': {
                'db_host': config.db_host,
                'db_port': config.db_port,
                'db_name': config.db_name,
                'db_user': config.db_user,
                'jwt_algorithm': config.jwt_algorithm,
                'auth_service_port': config.get_service_port('auth'),
                'user_service_port': config.get_service_port('user')
            },
            'configuration_status': config.get_configuration_status()
        }
        return all_settings
    except Exception as e:
        logger.error(f"Failed to fetch all settings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch all settings"
        )


@router.get("/frontend-settings")
async def get_frontend_settings():
    try:
        config.refresh_cache()
        frontend_settings = {
            'site_name': config.site_name,
            'site_description': config.site_description,
            'currency': config.currency,
            'currency_symbol': config.currency_symbol,
            'min_order_amount': config.min_order_amount,
            'free_shipping_min_amount': config.free_shipping_min_amount,
            'free_shipping_threshold': config.free_shipping_threshold,
            'return_period_days': config.return_period_days,
            'enable_reviews': config.enable_reviews,
            'enable_wishlist': config.enable_wishlist,
            'enable_guest_checkout': config.enable_guest_checkout,
            'site_phone': config.site_phone,
            'site_email': config.site_email,
            'business_hours': config.business_hours,
            'max_cart_quantity_per_product': config.max_cart_quantity_per_product,
            'max_cart_items_total': config.max_cart_items_total,
            'maintenance_mode': config.maintenance_mode
        }
        return frontend_settings
    except Exception as e:
        logger.error(f"Failed to fetch frontend settings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch frontend settings"
        )


@router.post("/login", response_model=Token)
async def login_user(
        login_data: UserLogin,
        request: Request = None,
        response: Response = None
):
    try:
        config.refresh_cache()
        if config.maintenance_mode:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Service is under maintenance. Please try again later."
            )

        session_config = config.get_session_config()
        client_identifier = get_client_identifier(request)

        if not check_rate_limit(f"login:{client_identifier}"):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many login attempts. Please try again later."
            )

        if not track_failed_login(client_identifier):
            lockout_minutes = session_config['login_lockout_minutes']
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Account temporarily locked due to too many failed attempts. Please try again in {lockout_minutes} minutes."
            )

        logger.info(f"Login attempt for: {login_data.login_id}")

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
                logger.warning(f"User not found: {login_data.login_id}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid credentials"
                )

            if not verify_password(login_data.password, user['password_hash']):
                logger.warning(f"Invalid password for user: {user['email']}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid credentials"
                )

            if not user['is_active']:
                logger.warning(f"Account deactivated: {user['email']}")
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

            ip_address = request.client.host if request.client else 'unknown'
            user_agent = request.headers.get("user-agent", "")
            user_session = session_service.get_or_create_user_session(user['id'], ip_address, user_agent)

            if not user_session:
                logger.error(f"Failed to get/create user session for user {user['id']}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create user session"
                )

            logger.info(f"✅ Using user session: {user_session.session_id} for user {user['id']}")
            current_session = get_session(request)
            migrated_items_count = 0
            if current_session and current_session.session_type == SessionType.GUEST:
                if current_session.cart_items:
                    migrated_items_count = migrate_guest_cart_to_user_database(
                        current_session, user['id'], cursor
                    )
                    logger.info(f"🔄 Method 1: Migrated {migrated_items_count} cart items from current guest session")
                    session_service.update_session_data(current_session.session_id, {
                        'cart_items': {}
                    })

            if migrated_items_count == 0:
                guest_session = session_service.find_guest_session_by_ip(ip_address, user_agent)
                if guest_session and guest_session.cart_items:
                    additional_migrated = migrate_guest_cart_to_user_database(
                        guest_session, user['id'], cursor
                    )
                    migrated_items_count += additional_migrated
                    logger.info(f"🔄 Method 2: Migrated {additional_migrated} cart items from IP-based guest session")
                    session_service.update_session_data(guest_session.session_id, {
                        'cart_items': {}
                    })

            if migrated_items_count == 0:
                guest_id = request.cookies.get("guest_id")
                if guest_id:
                    guest_session = session_service.get_session_by_guest_id(guest_id)
                    if guest_session and guest_session.cart_items:
                        additional_migrated = migrate_guest_cart_to_user_database(
                            guest_session, user['id'], cursor
                        )
                        migrated_items_count += additional_migrated
                        logger.info(
                            f"🔄 Method 3: Migrated {additional_migrated} cart items from guest_id-based session")

            if migrated_items_count > 0:
                cursor.execute("""
                    SELECT
                        sc.*,
                        p.name as product_name,
                        p.slug as product_slug,
                        p.main_image_url as product_image,
                        p.base_price as product_price,
                        p.stock_quantity,
                        p.stock_status,
                        p.max_cart_quantity
                    FROM shopping_cart sc
                    JOIN products p ON sc.product_id = p.id
                    WHERE sc.user_id = %s AND p.status = 'active'
                """, (user['id'],))
                user_cart_items = cursor.fetchall()
                session_cart_items = {}
                for item in user_cart_items:
                    item_key = f"{item['product_id']}_{item['variation_id']}" if item['variation_id'] else str(
                        item['product_id'])
                    session_cart_items[item_key] = {
                        'product_id': item['product_id'],
                        'variation_id': item['variation_id'],
                        'quantity': item['quantity']
                    }

                session_service.update_session_data(user_session.session_id, {
                    'cart_items': session_cart_items
                })
                logger.info(f"✅ Total {migrated_items_count} cart items migrated successfully for user {user['id']}")

            if user_session and response:
                session_config = config.get_session_config()
                session_timeout = session_config.get('user_session_duration', 2592000)
                cookie_value = f"session_id={user_session.session_id}; Max-Age={session_timeout}; HttpOnly; Path=/; SameSite=Lax"
                if not config.debug_mode:
                    cookie_value += "; Secure"

                response.headers.append("Set-Cookie", cookie_value)
                guest_cookie = f"guest_id={user_session.session_id}; Max-Age={session_timeout}; HttpOnly; Path=/; SameSite=Lax"
                if not config.debug_mode:
                    guest_cookie += "; Secure"
                response.headers.append("Set-Cookie", guest_cookie)
                response.headers["X-Session-ID"] = user_session.session_id
                response.headers["X-Secure-Session-ID"] = user_session.session_id

                request.state.session = user_session
                request.state.session_id = user_session.session_id
                logger.info(f"✅ Chrome session cookies set for user {user['id']}: {user_session.session_id}")

            cursor.execute("UPDATE users SET last_login = NOW() WHERE id = %s", (user['id'],))
            token_expiry_hours = session_config['token_expiry_hours']
            access_token = create_access_token(
                data={
                    "sub": str(user['id']),
                    "email": user['email'],
                    "roles": list(roles),
                    "permissions": list(permissions)
                },
                expires_delta=timedelta(hours=token_expiry_hours)
            )

            logger.info(f"Login successful for user: {user['email']} with {migrated_items_count} cart items migrated")

            return Token(
                access_token=access_token,
                token_type="bearer",
                expires_in=token_expiry_hours * 3600,
                user_roles=list(roles),
                user_permissions=list(permissions)
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login failed: {str(e)}")
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
        session_id = get_session_id(request)

        # 1. Delete the current user session
        if session_id:
            session_service.delete_session(session_id)
            logger.info(f"Session deleted for user {user_id}")

        # 2. Blacklist the JWT token
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:]
            blacklist_token(token)
            logger.info(f"JWT token invalidated for user {user_id}")

        # 3. Clear cookies
        response.delete_cookie(
            key="session_id",
            path="/",
            secure=not config.debug_mode,
            httponly=True,
            samesite="Lax"
        )
        response.delete_cookie(
            key="guest_id",
            path="/",
            secure=not config.debug_mode,
            httponly=True,
            samesite="Lax"
        )

        # 4. DO NOT create new guest session automatically
        # Let the next request create a fresh guest session

        logger.info(f"User {user_id} logged out successfully - session fully cleared")
        return {"message": "Logged out successfully"}

    except Exception as e:
        logger.error(f"Logout failed: {e}")
        # Still try to clear cookies even if other operations fail
        response.delete_cookie(key="session_id", path="/")
        response.delete_cookie(key="guest_id", path="/")
        return {"message": "Logged out successfully"}



@router.post("/refresh", response_model=Token)
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

    session_id = get_session_id(request)
    if session_id:
        session_service.update_session_activity(session_id)
        logger.info(f"Session activity refreshed for user {payload['sub']}")

    session_config = config.get_session_config()
    token_expiry_hours = session_config['token_expiry_hours']
    new_token = create_access_token(
        data={
            "sub": payload['sub'],
            "email": payload.get('email'),
            "roles": payload.get('roles', []),
            "permissions": payload.get('permissions', [])
        },
        expires_delta=timedelta(hours=token_expiry_hours)
    )

    logger.info(f"Token refreshed successfully for user {payload['sub']}")
    return Token(
        access_token=new_token,
        token_type="bearer",
        expires_in=token_expiry_hours * 3600,
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
                session_config = config.get_session_config()
                token_expiry_hours = session_config['token_expiry_hours']
                reset_token = create_access_token(
                    data={"sub": str(user['id']), "type": "password_reset"},
                    expires_delta=timedelta(hours=token_expiry_hours)
                )
                redis_client.setex(
                    f"password_reset:{user['id']}",
                    token_expiry_hours * 3600,
                    reset_token
                )
                logger.info(f"Password reset initiated for user {user['id']}")

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
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                                detail="Service is under maintenance. Please try again later.")

        payload = verify_token(token)
        if not payload or payload.get('type') != 'password_reset':
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid reset token")

        user_id = int(payload['sub'])

        try:
            stored_token = redis_client.get(f"password_reset:{user_id}")
        except Exception as redis_error:
            logger.error(f"Redis unavailable during password reset: {redis_error}")
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                                detail="Service temporarily unavailable")

        if not stored_token or stored_token != token:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired reset token")

        if len(new_password) < 8:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="Password must be at least 8 characters long")

        with db.get_cursor() as cursor:
            new_password_hash = get_password_hash(new_password)
            cursor.execute("UPDATE users SET password_hash = %s WHERE id = %s", (new_password_hash, user_id))
            cursor.execute("INSERT INTO password_history (user_id, password_hash) VALUES (%s, %s)",
                           (user_id, new_password_hash))

            try:
                redis_client.delete(f"password_reset:{user_id}")
            except Exception as e:
                logger.warning(f"Failed to delete reset token from Redis: {e}")

            logger.info(f"Password reset successful for user {user_id}")
            return {"message": "Password reset successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Password reset failed: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Password reset failed")


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
            "cache_size": len(config._cache) if hasattr(config, '_cache') else 0,
            "cache_keys": list(config._cache.keys()) if hasattr(config, '_cache') else []
        }
    }


@router.get("/session/info")
async def get_session_info(request: Request, current_user: dict = Depends(get_current_user)):
    try:
        user_id = current_user['sub']

        # FIRST: Try to get existing session for this user
        session = session_service.get_session_by_user_id(user_id)

        # SECOND: If no session exists, create a new one
        if not session:
            session_data = {
                'session_type': SessionType.USER,
                'user_id': user_id,
                'guest_id': None,
                'ip_address': request.client.host if request.client else 'unknown',
                'user_agent': request.headers.get("user-agent"),
                'cart_items': {}
            }
            session = session_service.create_session(session_data)

            if not session:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create session"
                )
            logger.info(f"Created new session for user {user_id}: {session.session_id}")
        else:
            logger.info(f"Retrieved existing session for user {user_id}: {session.session_id}")

        # Return session information
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

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get session info: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get session information"
        )


@router.post("/session/refresh")
async def refresh_user_session(request: Request, response: Response):
    try:
        session_id = get_session_id(request)
        if not session_id:
            raise HTTPException(status_code=404, detail="Session not found")

        success = session_service.update_session_activity(session_id)
        if not success:
            raise HTTPException(status_code=404, detail="Session expired")

        return {"message": "Session refreshed successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to refresh session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to refresh session"
        )


@router.get("/debug/session-test")
async def debug_session_test(request: Request):
    """Debug endpoint to test session handling"""
    session_id = get_session_id(request)
    session = get_session(request)
    is_new = is_new_session(request)

    cookies = dict(request.cookies)
    headers = dict(request.headers)

    return {
        "session_id": session_id,
        "session_exists": session is not None,
        "is_new_session": is_new,
        "session_type": session.session_type if session else None,
        "user_id": session.user_id if session else None,
        "guest_id": session.guest_id if session else None,
        "cookies_received": cookies,
        "headers_received": {k: v for k, v in headers.items() if k.lower() not in ['authorization', 'cookie']},
        "client_ip": request.client.host if request.client else 'unknown'
    }


@router.get("/health", response_model=HealthResponse)
async def health_check():
    try:
        with db.get_cursor() as cursor:
            cursor.execute("SELECT COUNT(*) as users_count FROM users")
            users_count = cursor.fetchone()['users_count']

            health_data = db.health_check()

            return HealthResponse(
                status="healthy" if health_data.get('status') == 'healthy' else "unhealthy",
                service="auth",
                environment="development" if config.debug_mode else "production",
                users_count=users_count,
                timestamp=datetime.utcnow()
            )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthResponse(
            status="unhealthy",
            service="auth",
            environment="development" if config.debug_mode else "production",
            users_count=0,
            timestamp=datetime.utcnow()
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    try:
        user_id = current_user['sub']
        with db.get_cursor() as cursor:
            cursor.execute("""
                SELECT 
                    id, uuid, email, first_name, last_name, phone,
                    email_verified, phone_verified, is_active,
                    country_id, preferred_currency, preferred_language,
                    avatar_url, created_at, updated_at
                FROM users 
                WHERE id = %s
            """, (user_id,))
            user_data = cursor.fetchone()

            if not user_data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )

            return UserResponse(
                id=user_data['id'],
                uuid=user_data['uuid'],
                email=user_data['email'],
                first_name=user_data['first_name'],
                last_name=user_data['last_name'],
                phone=user_data['phone'],
                email_verified=bool(user_data['email_verified']),
                phone_verified=bool(user_data['phone_verified']),
                is_active=bool(user_data['is_active']),
                roles=current_user.get('roles', []),
                permissions=current_user.get('permissions', []),
                country_id=user_data['country_id'],
                preferred_currency=user_data['preferred_currency'],
                preferred_language=user_data['preferred_language'],
                avatar_url=user_data['avatar_url'],
                created_at=user_data['created_at'],
                updated_at=user_data['updated_at']
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get user info: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user information"
        )