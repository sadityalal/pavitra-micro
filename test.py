from fastapi import APIRouter, HTTPException, Depends, Form, Request, status, BackgroundTasks, Response
from typing import Optional, List
import time
import json
from datetime import datetime, timedelta
import re
import hashlib
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
        for item_key, item_data in guest_cart_items.items():
            try:
                product_id = item_data['product_id']
                variation_id = item_data.get('variation_id')
                quantity = item_data['quantity']
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
                cursor.execute("""
                    SELECT id, quantity FROM shopping_cart
                    WHERE user_id = %s AND product_id = %s
                    AND (variation_id = %s OR (variation_id IS NULL AND %s IS NULL))
                """, (user_id, product_id, variation_id, variation_id))
                existing_item = cursor.fetchone()
                if existing_item:
                    existing_quantity = existing_item['quantity']
                    new_quantity = min(existing_quantity + available_quantity, max_quantity)
                    cursor.execute("""
                        UPDATE shopping_cart
                        SET quantity = %s, updated_at = NOW()
                        WHERE id = %s
                    """, (new_quantity, existing_item['id']))
                else:
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
            current_session = get_session(request)
            current_session_id = get_session_id(request)
            migrated_items_count = 0
            if current_session and current_session.session_type == SessionType.GUEST:
                migrated_items_count = migrate_guest_cart_to_user_database(
                    current_session, user_id, cursor
                )
                logger.info(f"Migrated {migrated_items_count} cart items from guest session during registration")

            # Create new user session using secure session service
            session_data = {
                'session_type': SessionType.USER,
                'user_id': user_id,
                'guest_id': None,
                'ip_address': request.client.host if request.client else 'unknown',
                'user_agent': request.headers.get("user-agent"),
                'cart_items': {}
            }
            new_session = session_service.create_session(session_data)

            # Session cookie is now handled by middleware - no need to set it manually
            if new_session:
                logger.info(f"User session created for new user {user_id}")

            # Clean up old guest session
            if current_session_id and current_session and current_session.session_type == SessionType.GUEST:
                session_service.delete_session(current_session_id)
                logger.info("Deleted guest session after successful registration migration")

            if background_tasks:
                cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
                user = cursor.fetchone()
                background_tasks.add_task(
                    publish_user_registration_event,
                    user
                )

            # Get token expiry from database configuration
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
            logger.info(f"User registered successfully: {email or phone or username}")
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

        # Get configuration from database
        session_config = config.get_session_config()
        client_identifier = get_client_identifier(request)

        # Rate limiting check using database configuration
        if not check_rate_limit(f"login:{client_identifier}"):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many login attempts. Please try again later."
            )

        # Failed attempts check using database configuration
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

            # Reset failed attempts on successful login
            reset_failed_login(client_identifier)

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

            if not roles:
                roles.add('customer')

            # Handle session migration from guest to user
            current_session = get_session(request)
            current_session_id = get_session_id(request)
            migrated_items_count = 0

            if current_session and current_session.session_type == SessionType.GUEST:
                migrated_items_count = migrate_guest_cart_to_user_database(
                    current_session, user['id'], cursor
                )
                logger.info(f"Migrated {migrated_items_count} cart items from guest session")

            # Create new user session using database configuration
            session_data = {
                'session_type': SessionType.USER,
                'user_id': user['id'],
                'guest_id': None,
                'ip_address': request.client.host if request.client else 'unknown',
                'user_agent': request.headers.get("user-agent"),
                'cart_items': {}
            }

            new_session = session_service.create_session(session_data)
            if new_session:
                logger.info(f"User session created for user {user['id']}")

            # Clean up old guest session
            if current_session_id and current_session and current_session.session_type == SessionType.GUEST:
                session_service.delete_session(current_session_id)
                logger.info("Deleted guest session after login migration")

            # Update last login
            cursor.execute("UPDATE users SET last_login = NOW() WHERE id = %s", (user['id'],))

            # Create JWT token using database configuration
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

            logger.info(f"Login successful for user: {user['email']}")
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

        # Delete session using secure session service
        if session_id:
            session_service.delete_session(session_id)
            logger.info(f"Session deleted for user {user_id}")

        # Blacklist token
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:]
            blacklist_token(token)
            logger.info(f"JWT token invalidated for user {user_id}")

        # Cookie deletion is handled by middleware - no need to manually delete

        logger.info(f"User {user_id} logged out successfully")
        return {"message": "Logged out successfully"}
    except Exception as e:
        logger.error(f"Logout failed: {e}")
        return {"message": "Logged out successfully"}  # Always return success to client


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

    # Refresh session activity using secure session service
    session_id = get_session_id(request)
    if session_id:
        session_service.update_session_activity(session_id)
        logger.info(f"Session activity refreshed for user {payload['sub']}")

    # Get token expiry from database configuration
    session_config = config.get_session_config()
    token_expiry_hours = session_config['token_expiry_hours']

    # Create new token
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
                # Get token expiry from database configuration
                session_config = config.get_session_config()
                token_expiry_hours = session_config['token_expiry_hours']

                # Create reset token
                reset_token = create_access_token(
                    data={"sub": str(user['id']), "type": "password_reset"},
                    expires_delta=timedelta(hours=token_expiry_hours)
                )
                # Store reset token in Redis
                redis_client.setex(
                    f"password_reset:{user['id']}",
                    token_expiry_hours * 3600,  # Use database configuration
                    reset_token
                )
                logger.info(f"Password reset initiated for user {user['id']}")
            # Always return same message for security
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
                ORDER