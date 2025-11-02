from fastapi import APIRouter, HTTPException, Depends, Form, Request, status, BackgroundTasks, Response
from typing import Optional, List
import time
import json
from datetime import datetime, timedelta
import re

from shared import (
    config, db, verify_password, get_password_hash,
    create_access_token, verify_token, validate_email,
    validate_phone, sanitize_input, get_logger, rabbitmq_client, redis_client
)
from shared.auth_middleware import get_current_user, require_roles, blacklist_token
from shared.session_service import session_service, SessionType
from shared.session_middleware import get_session, get_session_id
from shared.security import validate_password_strength
from .models import (
    UserCreate, UserLogin, Token, UserResponse,
    RoleResponse, PermissionCheck, HealthResponse
)

router = APIRouter()
logger = get_logger(__name__)

# Constants for better maintainability
RATE_LIMIT_WINDOW = 900  # 15 minutes
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_MINUTES = 15
TOKEN_EXPIRY_HOURS = 24
SESSION_TIMEOUT = 3600


def get_client_identifier(request: Request) -> str:
    """Generate a unique identifier for rate limiting based on client IP and user agent."""
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")
    return f"{client_ip}:{hash(user_agent) % 10000}"


def check_rate_limit(key: str, max_attempts: int, window_seconds: int) -> bool:
    """Check if request is within rate limits."""
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
        return True  # Fail open to avoid blocking users


def track_failed_login(identifier: str, max_attempts: int = MAX_LOGIN_ATTEMPTS,
                       lockout_minutes: int = LOCKOUT_MINUTES) -> bool:
    """Track failed login attempts and implement lockout."""
    try:
        fail_key = f"login_fails:{identifier}"
        lockout_key = f"login_lockout:{identifier}"

        # Check if already locked out
        if redis_client.exists(lockout_key):
            return False

        # Increment failure count
        failures = redis_client.incr(fail_key)
        if failures == 1:
            redis_client.expire(fail_key, 3600)  # 1 hour TTL for failure counter

        # Implement lockout if max attempts reached
        if failures >= max_attempts:
            redis_client.setex(lockout_key, lockout_minutes * 60, "locked")
            redis_client.delete(fail_key)
            return False

        return True
    except Exception as e:
        logger.error(f"Failed login tracking error: {e}")
        return True  # Fail open


def reset_failed_login(identifier: str):
    """Reset failed login attempts counter."""
    try:
        redis_client.delete(f"login_fails:{identifier}")
        redis_client.delete(f"login_lockout:{identifier}")
    except Exception as e:
        logger.error(f"Failed to reset login attempts: {e}")


def validate_username(username: str) -> bool:
    """Validate username format."""
    if not username:
        return False
    pattern = r'^[a-zA-Z0-9_]{3,30}$'
    return re.match(pattern, username) is not None


def publish_user_registration_event(user_data: dict):
    """Publish user registration event to message queue."""
    try:
        # Convert non-serializable objects to strings
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
    """Migrate guest cart items to user's database cart."""
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

                # Check product availability
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

                # Check for existing cart item
                cursor.execute("""
                    SELECT id, quantity FROM shopping_cart
                    WHERE user_id = %s AND product_id = %s
                    AND (variation_id = %s OR (variation_id IS NULL AND %s IS NULL))
                """, (user_id, product_id, variation_id, variation_id))

                existing_item = cursor.fetchone()

                if existing_item:
                    # Update existing item quantity
                    existing_quantity = existing_item['quantity']
                    new_quantity = min(existing_quantity + available_quantity, max_quantity)
                    cursor.execute("""
                        UPDATE shopping_cart
                        SET quantity = %s, updated_at = NOW()
                        WHERE id = %s
                    """, (new_quantity, existing_item['id']))
                else:
                    # Insert new cart item
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
    """Validate registration data and raise appropriate exceptions."""
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

    # Password validation
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
    """Check if user with same email, phone, or username already exists."""
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
    """Set up user account with roles, permissions, and preferences."""
    # Assign customer role
    cursor.execute("SELECT id FROM user_roles WHERE name = 'customer'")
    role = cursor.fetchone()
    if role:
        cursor.execute("""
            INSERT INTO user_role_assignments (user_id, role_id, assigned_by)
            VALUES (%s, %s, %s)
        """, (user_id, role['id'], user_id))
        logger.info(f"Customer role assigned to user {user_id}")

    # Set notification preferences
    cursor.execute("""
        INSERT INTO user_notification_preferences (user_id, notification_method, is_enabled)
        VALUES (%s, 'email', TRUE)
        ON DUPLICATE KEY UPDATE is_enabled = TRUE
    """, (user_id,))

    # Get roles and permissions
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
    """Register a new user account."""
    try:
        config.refresh_cache()
        if config.maintenance_mode:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Service is under maintenance. Registration is temporarily unavailable."
            )

        # Handle both form data and JSON body
        if user_data:
            email = user_data.email
            phone = user_data.phone
            username = user_data.username
            password = user_data.password
            first_name = user_data.first_name
            last_name = user_data.last_name
            country_id = user_data.country_id or 1

        logger.info(f"Processing registration for: {email or phone or username}")

        # Sanitize inputs
        first_name = sanitize_input(first_name)
        last_name = sanitize_input(last_name)

        # Validate input data
        _validate_registration_data(email, phone, username, password)

        with db.get_cursor() as cursor:
            # Check for existing users
            _check_existing_users(cursor, email, phone, username)

            # Create user
            password_hash = get_password_hash(password)
            cursor.execute("""
                INSERT INTO users (email, phone, username, password_hash, first_name, last_name, country_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (email, phone, username, password_hash, first_name, last_name, country_id))

            user_id = cursor.lastrowid
            logger.info(f"User created with ID: {user_id}")

            # Set up user account
            roles, permissions = _setup_user_account(cursor, user_id)

            # Handle session migration
            current_session = get_session(request)
            current_session_id = get_session_id(request)
            migrated_items_count = 0

            if current_session and current_session.session_type == SessionType.GUEST:
                migrated_items_count = migrate_guest_cart_to_user_database(
                    current_session, user_id, cursor
                )
                logger.info(f"Migrated {migrated_items_count} cart items from guest session during registration")

            # Create new user session
            session_data = {
                'session_type': SessionType.USER,
                'user_id': user_id,
                'guest_id': None,
                'ip_address': request.client.host if request.client else 'unknown',
                'user_agent': request.headers.get("user-agent"),
                'cart_items': {}
            }

            new_session = session_service.create_session(session_data)
            if new_session and response:
                response.set_cookie(
                    key="session_id",
                    value=new_session.session_id,
                    max_age=SESSION_TIMEOUT,
                    httponly=True,
                    secure=not config.debug_mode,
                    samesite="Lax",
                    path="/"
                )
                logger.info(f"User session created for new user {user_id}")

            # Delete old guest session
            if current_session_id and current_session and current_session.session_type == SessionType.GUEST:
                session_service.delete_session(current_session_id)
                logger.info("Deleted guest session after successful registration migration")

            # Publish registration event
            if background_tasks:
                cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
                user = cursor.fetchone()
                background_tasks.add_task(
                    publish_user_registration_event,
                    user
                )

            # Create access token
            access_token = create_access_token(
                data={
                    "sub": str(user_id),
                    "email": email,
                    "roles": roles,
                    "permissions": permissions
                },
                expires_delta=timedelta(hours=TOKEN_EXPIRY_HOURS)
            )

            logger.info(f"User registered successfully: {email or phone or username}")
            return Token(
                access_token=access_token,
                token_type="bearer",
                expires_in=TOKEN_EXPIRY_HOURS * 3600,
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
    """Get site settings (admin only)."""
    user_roles = current_user.get('roles', [])
    if 'admin' not in user_roles and 'super_admin' not in user_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )

    try:
        config.refresh_cache()
        settings = {
            # Store Configuration (Admin Only)
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
            # Cart & Business Limits (Admin Only)
            'max_cart_quantity_per_product': config.max_cart_quantity_per_product,
            'max_cart_items_total': config.max_cart_items_total,
            'cart_session_timeout_minutes': config.cart_session_timeout_minutes,
            # Backend/Infrastructure Settings (Admin Only)
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


@router.get("/frontend-settings")
async def get_frontend_settings():
    """Get frontend settings (public)."""
    try:
        config.refresh_cache()
        frontend_settings = {
            # Public Store Information
            'site_name': config.site_name,
            'site_description': config.site_description,
            # Currency & Pricing (Public)
            'currency': config.currency,
            'currency_symbol': config.currency_symbol,
            'min_order_amount': config.min_order_amount,
            # Shipping (Public)
            'free_shipping_min_amount': config.free_shipping_min_amount,
            'free_shipping_threshold': config.free_shipping_threshold,
            # Returns & Policies (Public)
            'return_period_days': config.return_period_days,
            # Features (Public)
            'enable_reviews': config.enable_reviews,
            'enable_wishlist': config.enable_wishlist,
            'enable_guest_checkout': config.enable_guest_checkout,
            # Contact Information (Public)
            'site_phone': config.site_phone,
            'site_email': config.site_email,
            # Business Hours (Public)
            'business_hours': config.business_hours,
            # Cart Limits (Public - needed for UI validation)
            'max_cart_quantity_per_product': config.max_cart_quantity_per_product,
            'max_cart_items_total': config.max_cart_items_total,
            # Maintenance Mode (Public - needed for UI messaging)
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
    """Authenticate user and return access token."""
    try:
        config.refresh_cache()
        if config.maintenance_mode:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Service is under maintenance. Please try again later."
            )

        client_identifier = get_client_identifier(request)

        # Rate limiting
        if not check_rate_limit(f"login:{client_identifier}", max_attempts=10, window_seconds=RATE_LIMIT_WINDOW):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many login attempts. Please try again later."
            )

        # Failed login tracking
        if not track_failed_login(client_identifier):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Account temporarily locked due to too many failed attempts. Please try again in 15 minutes."
            )

        logger.info(f"Login attempt for: {login_data.login_id}")

        with db.get_cursor() as cursor:
            # Find user by email, phone, or username
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

            # Verify password
            if not verify_password(login_data.password, user['password_hash']):
                logger.warning(f"Invalid password for user: {user['email']}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid credentials"
                )

            # Check if account is active
            if not user['is_active']:
                logger.warning(f"Account deactivated: {user['email']}")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Account is deactivated"
                )

            # Reset failed login counter on successful login
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

            # Handle session and cart migration
            current_session = get_session(request)
            current_session_id = get_session_id(request)
            migrated_items_count = 0

            if current_session and current_session.session_type == SessionType.GUEST:
                migrated_items_count = migrate_guest_cart_to_user_database(
                    current_session, user['id'], cursor
                )
                logger.info(f"Migrated {migrated_items_count} cart items from guest session")

            # Create new user session
            session_data = {
                'session_type': SessionType.USER,
                'user_id': user['id'],
                'guest_id': None,
                'ip_address': request.client.host if request.client else 'unknown',
                'user_agent': request.headers.get("user-agent"),
                'cart_items': {}  # Empty since we're using database now
            }

            new_session = session_service.create_session(session_data)
            if new_session and response:
                response.set_cookie(
                    key="session_id",
                    value=new_session.session_id,
                    max_age=SESSION_TIMEOUT,
                    httponly=True,
                    secure=not config.debug_mode,
                    samesite="Lax",
                    path="/"
                )

            # Delete old guest session
            if current_session_id and current_session and current_session.session_type == SessionType.GUEST:
                session_service.delete_session(current_session_id)
                logger.info("Deleted guest session after login migration")

            # Update last login timestamp
            cursor.execute("UPDATE users SET last_login = NOW() WHERE id = %s", (user['id'],))

            # Create access token
            access_token = create_access_token(
                data={
                    "sub": str(user['id']),
                    "email": user['email'],
                    "roles": list(roles),
                    "permissions": list(permissions)
                },
                expires_delta=timedelta(hours=TOKEN_EXPIRY_HOURS)
            )

            logger.info(f"Login successful for user: {user['email']}")
            return Token(
                access_token=access_token,
                token_type="bearer",
                expires_in=TOKEN_EXPIRY_HOURS * 3600,
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
    """Logout user and invalidate session/token."""
    try:
        user_id = current_user['sub']
        auth_header = request.headers.get("Authorization")
        session_id = get_session_id(request)

        # Delete session
        if session_id:
            session_service.delete_session(session_id)
            logger.info(f"Session deleted for user {user_id}")

        # Blacklist token
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:]
            blacklist_token(token)
            logger.info(f"JWT token invalidated for user {user_id}")

        # Clear session cookie
        response.delete_cookie(
            key="session_id",
            path="/",
            secure=not config.debug_mode,
            httponly=True,
            samesite="Lax"
        )

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
    """Refresh access token."""
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

    # Refresh session activity
    session_id = get_session_id(request)
    if session_id:
        session_service.update_session_activity(session_id)
        logger.info(f"Session activity refreshed for user {payload['sub']}")

    # Create new token
    new_token = create_access_token(
        data={
            "sub": payload['sub'],
            "email": payload.get('email'),
            "roles": payload.get('roles', []),
            "permissions": payload.get('permissions', [])
        },
        expires_delta=timedelta(hours=TOKEN_EXPIRY_HOURS)
    )

    logger.info(f"Token refreshed successfully for user {payload['sub']}")
    return Token(
        access_token=new_token,
        token_type="bearer",
        expires_in=TOKEN_EXPIRY_HOURS * 3600,
        user_roles=payload.get('roles', []),
        user_permissions=payload.get('permissions', [])
    )


@router.post("/forgot-password")
async def forgot_password(email: str = Form(...)):
    """Initiate password reset process."""
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
                # Create reset token
                reset_token = create_access_token(
                    data={"sub": str(user['id']), "type": "password_reset"},
                    expires_delta=timedelta(hours=1)
                )

                # Store reset token in Redis
                redis_client.setex(
                    f"password_reset:{user['id']}",
                    3600,  # 1 hour expiry
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
    """Reset user password using reset token."""
    try:
        config.refresh_cache()
        if config.maintenance_mode:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Service is under maintenance. Please try again later."
            )

        # Verify reset token
        payload = verify_token(token)
        if not payload or payload.get('type') != 'password_reset':
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid reset token"
            )

        user_id = int(payload['sub'])

        # Check if token exists in Redis
        stored_token = redis_client.get(f"password_reset:{user_id}")
        if not stored_token or stored_token != token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token"
            )

        # Validate new password
        if len(new_password) < 8:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must be at least 8 characters long"
            )

        with db.get_cursor() as cursor:
            # Update password
            new_password_hash = get_password_hash(new_password)
            cursor.execute(
                "UPDATE users SET password_hash = %s WHERE id = %s",
                (new_password_hash, user_id)
            )

            # Store in password history
            cursor.execute(
                "INSERT INTO password_history (user_id, password_hash) VALUES (%s, %s)",
                (user_id, new_password_hash)
            )

            # Clean up reset token
            redis_client.delete(f"password_reset:{user_id}")

            logger.info(f"Password reset successful for user {user_id}")
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
    """Get list of available user roles."""
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
    """Check if current user has specific permission."""
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
    """Debug endpoint to check maintenance mode status."""
    config.refresh_cache()
    return {
        "maintenance_mode": config.maintenance_mode,
        "maintenance_mode_type": str(type(config.maintenance_mode)),
        "maintenance_mode_raw": str(config.maintenance_mode)
    }


@router.get("/debug/settings")
async def debug_settings():
    """Debug endpoint to check configuration settings."""
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
    """Get current session information."""
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
    """Refresh user session activity."""
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