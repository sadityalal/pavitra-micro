from fastapi import APIRouter, HTTPException, Depends, Form, status, BackgroundTasks, UploadFile, File, Request, Header
from typing import List, Optional, Dict, Any
import html
from shared import config, db, sanitize_input, get_logger, redis_client, rabbitmq_client
from shared.security import verify_password, get_password_hash
from shared.auth_middleware import get_current_user, require_roles
from shared.rate_limiter import rate_limiter
from shared.session_service import session_service, SessionType
from shared.session_middleware import get_session, get_session_id
from .models import (
    UserProfileResponse, UserProfileUpdate, AddressResponse,
    AddressCreate, WishlistResponse, CartResponse, HealthResponse
)
from datetime import datetime
import json
import os
import uuid

router = APIRouter()
logger = get_logger(__name__)


def publish_user_event(user_data: dict, event_type: str):
    try:
        message = {
            'event_type': event_type,
            'user_id': user_data['id'],
            'email': user_data.get('email'),
            'first_name': user_data.get('first_name'),
            'timestamp': datetime.utcnow().isoformat(),
            'data': user_data
        }
        rabbitmq_client.publish_message(
            exchange='notification_events',
            routing_key=f'user.{event_type}',
            message=message
        )
        logger.info(f"User {event_type} event published for user {user_data['id']}")
    except Exception as e:
        logger.error(f"Failed to publish user event: {e}")


def cache_user_profile(user_id: int, profile_data: dict, expire: int = 1800):
    try:
        key = f"user_profile:{user_id}"
        redis_client.setex(key, expire, json.dumps(profile_data))
        logger.info(f"Cached user profile for user {user_id}")
    except Exception as e:
        logger.error(f"Failed to cache user profile: {e}")


def get_cached_user_profile(user_id: int) -> Optional[dict]:
    try:
        key = f"user_profile:{user_id}"
        data = redis_client.get(key)
        if data:
            return json.loads(data)
        return None
    except Exception as e:
        logger.error(f"Failed to get cached user profile: {e}")
        return None


def cache_user_addresses(user_id: int, addresses: List[dict], expire: int = 1800):
    try:
        key = f"user_addresses:{user_id}"
        redis_client.setex(key, expire, json.dumps(addresses))
        logger.info(f"Cached addresses for user {user_id}")
    except Exception as e:
        logger.error(f"Failed to cache user addresses: {e}")


def get_cached_user_addresses(user_id: int) -> Optional[List[dict]]:
    try:
        key = f"user_addresses:{user_id}"
        data = redis_client.get(key)
        if data:
            return json.loads(data)
        return None
    except Exception as e:
        logger.error(f"Failed to get cached user addresses: {e}")
        return None


def cache_user_wishlist(user_id: int, wishlist_data: dict, expire: int = 900):
    try:
        key = f"user_wishlist:{user_id}"
        redis_client.setex(key, expire, json.dumps(wishlist_data))
        logger.info(f"Cached wishlist for user {user_id}")
    except Exception as e:
        logger.error(f"Failed to cache user wishlist: {e}")


def get_cached_user_wishlist(user_id: int) -> Optional[dict]:
    try:
        key = f"user_wishlist:{user_id}"
        data = redis_client.get(key)
        if data:
            return json.loads(data)
        return None
    except Exception as e:
        logger.error(f"Failed to get cached user wishlist: {e}")
        return None


def cache_user_cart(user_id: int, cart_data: dict, expire: int = 600):
    try:
        key = f"user_cart:{user_id}"
        redis_client.setex(key, expire, json.dumps(cart_data))
        logger.info(f"Cached cart for user {user_id}")
    except Exception as e:
        logger.error(f"Failed to cache user cart: {e}")


def get_cached_user_cart(user_id: int) -> Optional[dict]:
    try:
        key = f"user_cart:{user_id}"
        data = redis_client.get(key)
        if data:
            return json.loads(data)
        return None
    except Exception as e:
        logger.error(f"Failed to get cached user cart: {e}")
        return None


def invalidate_user_cache(user_id: int):
    try:
        keys = [
            f"user_profile:{user_id}",
            f"user_addresses:{user_id}",
            f"user_wishlist:{user_id}",
            f"user_cart:{user_id}"
        ]
        for key in keys:
            redis_client.delete(key)
        logger.info(f"Invalidated cache for user {user_id}")
    except Exception as e:
        logger.error(f"Failed to invalidate user cache: {e}")


async def get_current_user_or_session(request: Request):
    try:
        # First, try to get authenticated user
        try:
            current_user = await get_current_user(request)
            if current_user and current_user.get('sub'):
                user_id = current_user['sub']
                ip_address = request.client.host if request.client else 'unknown'
                user_agent = request.headers.get("user-agent", "")

                # Get or create user session - ONE SESSION PER USER
                session = session_service.get_or_create_user_session(user_id, ip_address, user_agent)
                if session:
                    return {
                        "user_id": user_id,
                        "is_guest": False,
                        "session": session,
                        "session_id": session.session_id
                    }
        except HTTPException:
            # User not authenticated, continue as guest
            pass

        # Handle guest session - get existing or create new
        guest_id = request.cookies.get("guest_id")
        if not guest_id:
            guest_id = str(uuid.uuid4())

        ip_address = request.client.host if request.client else 'unknown'
        user_agent = request.headers.get("user-agent", "")

        session = session_service.get_or_create_guest_session(guest_id, ip_address, user_agent)
        if session:
            return {
                "user_id": None,
                "is_guest": True,
                "session": session,
                "session_id": session.session_id,
                "guest_id": guest_id
            }

        # Fallback - minimal session data (should rarely happen)
        return {
            "user_id": None,
            "is_guest": True,
            "session": None,
            "session_id": f"minimal_{uuid.uuid4().hex[:8]}",
            "cart_items": {}
        }

    except Exception as e:
        logger.error(f"Critical error in get_current_user_or_session: {e}")
        return {
            "user_id": None,
            "is_guest": True,
            "session": None,
            "session_id": f"error_fallback_{uuid.uuid4().hex[:8]}",
            "cart_items": {}
        }


def migrate_guest_cart_to_user_database(guest_session, user_id: int, cursor):
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
                logger.info(f"✅ Migrated cart item: product {product_id}, quantity {available_quantity}")
            except Exception as e:
                logger.error(f"❌ Failed to migrate cart item {item_key}: {e}")
                continue
        return migrated_count
    except Exception as e:
        logger.error(f"❌ Cart migration failed: {e}")
        return 0


async def _convert_session_cart_to_response(cart_items: Dict[str, Any]) -> CartResponse:
    try:
        items = []
        subtotal = 0.0
        total_items = 0
        if not cart_items:
            return CartResponse(items=[], subtotal=0.0, total_items=0)
        product_ids = []
        item_map = {}
        for item_key, item_data in cart_items.items():
            try:
                if not isinstance(item_data, dict):
                    continue
                product_id = item_data.get('product_id')
                if not product_id:
                    continue
                product_ids.append(product_id)
                item_map[product_id] = {
                    'data': item_data,
                    'key': item_key
                }
            except (ValueError, KeyError, AttributeError) as e:
                continue
        if not product_ids:
            return CartResponse(items=[], subtotal=0.0, total_items=0)
        with db.get_cursor() as cursor:
            placeholders = ','.join(['%s'] * len(product_ids))
            cursor.execute(f"""
                SELECT id, name, slug, main_image_url, base_price,
                       stock_quantity, stock_status, max_cart_quantity
                FROM products
                WHERE id IN ({placeholders}) AND status = 'active'
            """, product_ids)
            products = {p['id']: p for p in cursor.fetchall()}
        for product_id, product in products.items():
            if product_id in item_map:
                item_data = item_map[product_id]['data']
                quantity = item_data.get('quantity', 1)
                item_total = float(product['base_price']) * quantity
                subtotal += item_total
                total_items += quantity
                items.append({
                    'id': product_id,
                    'product_id': product_id,
                    'variation_id': item_data.get('variation_id'),
                    'product_name': product['name'],
                    'product_slug': product['slug'],
                    'product_image': product['main_image_url'],
                    'product_price': float(product['base_price']),
                    'quantity': quantity,
                    'total_price': item_total,
                    'stock_quantity': product['stock_quantity'],
                    'stock_status': product['stock_status'],
                    'max_cart_quantity': product['max_cart_quantity']
                })
        return CartResponse(
            items=items,
            subtotal=subtotal,
            total_items=total_items
        )
    except Exception as e:
        logger.error(f"Failed to convert session cart: {e}")
        return CartResponse(items=[], subtotal=0.0, total_items=0)


async def _convert_db_cart_to_response(cart_items: List[Dict]) -> CartResponse:
    items = []
    subtotal = 0.0
    total_items = 0
    for item in cart_items:
        item_total = float(item['product_price']) * item['quantity']
        subtotal += item_total
        total_items += item['quantity']
        items.append({
            'id': item['id'],
            'product_id': item['product_id'],
            'variation_id': item['variation_id'],
            'product_name': item['product_name'],
            'product_slug': item['product_slug'],
            'product_image': item['product_image'],
            'product_price': float(item['product_price']),
            'quantity': item['quantity'],
            'total_price': item_total,
            'stock_quantity': item['stock_quantity'],
            'stock_status': item['stock_status'],
            'max_cart_quantity': item['max_cart_quantity']
        })
    return CartResponse(
        items=items,
        subtotal=subtotal,
        total_items=total_items
    )


@router.get("/health", response_model=HealthResponse)
async def health():
    try:
        with db.get_cursor() as cursor:
            cursor.execute("SELECT COUNT(*) as count FROM users")
            users_count = cursor.fetchone()['count']
            return HealthResponse(
                status="healthy",
                service="user",
                users_count=users_count,
                timestamp=datetime.utcnow()
            )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthResponse(
            status="unhealthy",
            service="user",
            users_count=0,
            timestamp=datetime.utcnow()
        )


@router.get("/profile", response_model=UserProfileResponse)
async def get_user_profile(current_user: dict = Depends(get_current_user)):
    try:
        user_id = current_user['sub']
        cached_profile = get_cached_user_profile(user_id)
        if cached_profile:
            return UserProfileResponse(**cached_profile)
        with db.get_cursor() as cursor:
            cursor.execute("""
                SELECT
                    u.*,
                    c.country_name,
                    c.currency_code,
                    c.currency_symbol
                FROM users u
                LEFT JOIN countries c ON u.country_id = c.id
                WHERE u.id = %s
            """, (user_id,))
            user = cursor.fetchone()
            safe_first_name = html.escape(user['first_name']) if user['first_name'] else ""
            safe_last_name = html.escape(user['last_name']) if user['last_name'] else ""
            safe_email = html.escape(user['email']) if user['email'] else ""
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
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
            profile_data = UserProfileResponse(
                id=user['id'],
                uuid=user['uuid'],
                email=safe_email,
                mobile=user['phone'],
                first_name=safe_first_name,
                last_name=safe_last_name,
                phone=user['phone'],
                username=user['username'],
                country_id=user['country_id'],
                email_verified=bool(user['email_verified']),
                phone_verified=bool(user['phone_verified']),
                is_active=bool(user['is_active']),
                roles=list(roles),
                permissions=list(permissions),
                preferred_currency=user.get('preferred_currency', 'INR'),
                preferred_language=user.get('preferred_language', 'en'),
                avatar_url=user['avatar_url'],
                date_of_birth=user['date_of_birth'],
                gender=user['gender'],
                last_login=user['last_login'],
                created_at=user['created_at'],
                updated_at=user['updated_at']
            )
            cache_user_profile(user_id, profile_data.dict())
            return profile_data
    except Exception as e:
        logger.error(f"Failed to fetch user profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch user profile"
        )


@router.put("/profile", response_model=UserProfileResponse)
async def update_user_profile(
        profile_data: UserProfileUpdate,
        current_user: dict = Depends(get_current_user),
        background_tasks: BackgroundTasks = None
):
    try:
        user_id = current_user['sub']

        with db.get_cursor() as cursor:
            if profile_data.username:
                cursor.execute("""
                    SELECT id FROM users WHERE username = %s AND id != %s
                """, (sanitize_input(profile_data.username), user_id))
                if cursor.fetchone():
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Username already taken"
                    )

            update_fields = []
            update_params = []

            if profile_data.first_name is not None:
                update_fields.append("first_name = %s")
                update_params.append(sanitize_input(profile_data.first_name))
            if profile_data.last_name is not None:
                update_fields.append("last_name = %s")
                update_params.append(sanitize_input(profile_data.last_name))
            if profile_data.phone is not None:
                update_fields.append("phone = %s")
                update_params.append(sanitize_input(profile_data.phone))
            if profile_data.username is not None:
                update_fields.append("username = %s")
                update_params.append(sanitize_input(profile_data.username))
            if profile_data.country_id is not None:
                update_fields.append("country_id = %s")
                update_params.append(profile_data.country_id)
            if profile_data.preferred_currency is not None:
                update_fields.append("preferred_currency = %s")
                update_params.append(profile_data.preferred_currency)
            if profile_data.preferred_language is not None:
                update_fields.append("preferred_language = %s")
                update_params.append(profile_data.preferred_language)
            if profile_data.date_of_birth is not None:
                update_fields.append("date_of_birth = %s")
                update_params.append(profile_data.date_of_birth)
            if profile_data.gender is not None:
                update_fields.append("gender = %s")
                update_params.append(profile_data.gender)

            if not update_fields:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No fields to update"
                )

            update_fields.append("updated_at = NOW()")
            update_params.append(user_id)

            update_query = f"""
                UPDATE users
                SET {', '.join(update_fields)}
                WHERE id = %s
            """
            cursor.execute(update_query, update_params)

            cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
            updated_user = cursor.fetchone()

            if background_tasks:
                background_tasks.add_task(
                    publish_user_event,
                    updated_user,
                    'profile_updated'
                )

            invalidate_user_cache(user_id)

            cached_profile = get_cached_user_profile(user_id)
            if cached_profile:
                return UserProfileResponse(**cached_profile)

            return await get_user_profile(current_user)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update user profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user profile"
        )


@router.get("/addresses", response_model=List[AddressResponse])
async def get_user_addresses(current_user: dict = Depends(get_current_user)):
    try:
        user_id = current_user['sub']
        cached_addresses = get_cached_user_addresses(user_id)
        if cached_addresses:
            return [AddressResponse(**addr) for addr in cached_addresses]

        with db.get_cursor() as cursor:
            cursor.execute("""
                SELECT * FROM user_addresses
                WHERE user_id = %s
                ORDER BY is_default DESC, created_at DESC
            """, (user_id,))
            addresses = cursor.fetchall()

            address_list = []
            for addr in addresses:
                import html
                safe_full_name = html.escape(addr['full_name']) if addr['full_name'] else ""
                safe_address_line1 = html.escape(addr['address_line1']) if addr['address_line1'] else ""
                safe_address_line2 = html.escape(addr['address_line2']) if addr['address_line2'] else ""
                safe_landmark = html.escape(addr['landmark']) if addr['landmark'] else ""
                safe_city = html.escape(addr['city']) if addr['city'] else ""
                safe_state = html.escape(addr['state']) if addr['state'] else ""
                safe_country = html.escape(addr['country']) if addr['country'] else ""

                address_list.append(AddressResponse(
                    id=addr['id'],
                    user_id=addr['user_id'],
                    address_type=addr['address_type'],
                    full_name=safe_full_name,
                    phone=addr['phone'],
                    address_line1=safe_address_line1,
                    address_line2=safe_address_line2,
                    landmark=safe_landmark,
                    city=safe_city,
                    state=safe_state,
                    country=safe_country,
                    postal_code=addr['postal_code'],
                    address_type_detail=addr['address_type_detail'],
                    is_default=bool(addr['is_default']),
                    created_at=addr['created_at'],
                    updated_at=addr['updated_at']
                ))

            cache_user_addresses(user_id, [addr.dict() for addr in address_list])
            return address_list
    except Exception as e:
        logger.error(f"Failed to fetch user addresses: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch addresses"
        )


@router.post("/addresses", response_model=AddressResponse)
async def create_user_address(
        address_data: AddressCreate,
        current_user: dict = Depends(get_current_user),
        background_tasks: BackgroundTasks = None
):
    try:
        user_id = current_user['sub']

        if not address_data.full_name or not address_data.phone or not address_data.address_line1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Full name, phone, and address line 1 are required"
            )

        import re
        phone_pattern = r'^\+?[1-9]\d{1,14}$'
        if not re.match(phone_pattern, address_data.phone):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid phone number format"
            )

        with db.get_cursor() as cursor:
            cursor.execute("""
                SELECT id FROM user_addresses
                WHERE user_id = %s AND address_line1 = %s AND city = %s AND postal_code = %s
            """, (user_id, sanitize_input(address_data.address_line1),
                  sanitize_input(address_data.city), sanitize_input(address_data.postal_code)))

            if cursor.fetchone():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Address already exists"
                )

            if address_data.is_default:
                cursor.execute("""
                    UPDATE user_addresses
                    SET is_default = 0
                    WHERE user_id = %s AND address_type = %s
                """, (user_id, address_data.address_type.value))

            cursor.execute("""
                INSERT INTO user_addresses (
                    user_id, address_type, full_name, phone, address_line1,
                    address_line2, landmark, city, state, country, postal_code,
                    address_type_detail, is_default
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                user_id,
                address_data.address_type.value,
                sanitize_input(address_data.full_name),
                sanitize_input(address_data.phone),
                sanitize_input(address_data.address_line1),
                sanitize_input(address_data.address_line2) if address_data.address_line2 else None,
                sanitize_input(address_data.landmark) if address_data.landmark else None,
                sanitize_input(address_data.city),
                sanitize_input(address_data.state),
                sanitize_input(address_data.country),
                sanitize_input(address_data.postal_code),
                address_data.address_type_detail.value if address_data.address_type_detail else None,
                address_data.is_default
            ))

            address_id = cursor.lastrowid
            cursor.execute("SELECT * FROM user_addresses WHERE id = %s", (address_id,))
            address = cursor.fetchone()

            invalidate_user_cache(user_id)

            return AddressResponse(
                id=address['id'],
                user_id=address['user_id'],
                address_type=address['address_type'],
                full_name=address['full_name'],
                phone=address['phone'],
                address_line1=address['address_line1'],
                address_line2=address['address_line2'],
                landmark=address['landmark'],
                city=address['city'],
                state=address['state'],
                country=address['country'],
                postal_code=address['postal_code'],
                address_type_detail=address['address_type_detail'],
                is_default=bool(address['is_default']),
                created_at=address['created_at'],
                updated_at=address['updated_at']
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create address: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create address"
        )


@router.get("/wishlist", response_model=WishlistResponse)
async def get_user_wishlist(current_user: dict = Depends(get_current_user)):
    try:
        user_id = current_user['sub']
        cached_wishlist = get_cached_user_wishlist(user_id)
        if cached_wishlist:
            return WishlistResponse(**cached_wishlist)

        with db.get_cursor() as cursor:
            cursor.execute("""
                SELECT
                    w.*,
                    p.name as product_name,
                    p.slug as product_slug,
                    p.main_image_url as product_image,
                    p.base_price as product_price,
                    p.stock_status as product_stock_status
                FROM wishlists w
                JOIN products p ON w.product_id = p.id
                WHERE w.user_id = %s AND p.status = 'active'
                ORDER BY w.created_at DESC
            """, (user_id,))
            wishlist_items = cursor.fetchall()

            items = [
                {
                    'id': item['id'],
                    'product_id': item['product_id'],
                    'product_name': item['product_name'],
                    'product_slug': item['product_slug'],
                    'product_image': item['product_image'],
                    'product_price': float(item['product_price']),
                    'product_stock_status': item['product_stock_status'],
                    'added_at': item['created_at']
                }
                for item in wishlist_items
            ]

            wishlist_data = WishlistResponse(
                items=items,
                total_count=len(items)
            )

            cache_user_wishlist(user_id, wishlist_data.dict())
            return wishlist_data
    except Exception as e:
        logger.error(f"Failed to fetch wishlist: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch wishlist"
        )


@router.post("/wishlist/{product_id}")
async def add_to_wishlist(
        product_id: int,
        current_user: dict = Depends(get_current_user)
):
    try:
        user_id = current_user['sub']

        with db.get_cursor() as cursor:
            cursor.execute("SELECT id FROM products WHERE id = %s AND status = 'active'", (product_id,))
            if not cursor.fetchone():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Product not found"
                )

            cursor.execute("SELECT id FROM wishlists WHERE user_id = %s AND product_id = %s", (user_id, product_id))
            if cursor.fetchone():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Product already in wishlist"
                )

            cursor.execute("INSERT INTO wishlists (user_id, product_id) VALUES (%s, %s)", (user_id, product_id))
            cursor.execute("UPDATE products SET wishlist_count = wishlist_count + 1 WHERE id = %s", (product_id,))

            redis_client.delete(f"user_wishlist:{user_id}")
            logger.info(f"Product {product_id} added to wishlist for user {user_id}")

            return {"message": "Product added to wishlist"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to add to wishlist: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add to wishlist"
        )


@router.delete("/wishlist/{product_id}")
async def remove_from_wishlist(
        product_id: int,
        current_user: dict = Depends(get_current_user)
):
    try:
        user_id = current_user['sub']

        with db.get_cursor() as cursor:
            cursor.execute("DELETE FROM wishlists WHERE user_id = %s AND product_id = %s", (user_id, product_id))
            if cursor.rowcount == 0:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Product not found in wishlist"
                )

            cursor.execute("UPDATE products SET wishlist_count = GREATEST(0, wishlist_count - 1) WHERE id = %s",
                           (product_id,))

            redis_client.delete(f"user_wishlist:{user_id}")
            logger.info(f"Product {product_id} removed from wishlist for user {user_id}")

            return {"message": "Product removed from wishlist"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to remove from wishlist: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to remove from wishlist"
        )


@router.get("/cart", response_model=CartResponse)
async def get_cart(
        request: Request,
        current_user_or_session: dict = Depends(get_current_user_or_session)
):
    try:
        await rate_limiter.check_rate_limit(request)

        # Handle case where session creation completely failed
        if not current_user_or_session.get('session') and not current_user_or_session.get('is_guest'):
            logger.warning("No session available, returning empty cart")
            return CartResponse(items=[], subtotal=0.0, total_items=0)

        session = current_user_or_session.get('session')
        session_id = current_user_or_session.get('session_id')

        if session_id:
            try:
                session_service.update_session_activity(session_id)
            except Exception as e:
                logger.warning(f"Failed to update session activity: {e}")

        if not current_user_or_session.get('is_guest'):
            # Authenticated user - get cart from database
            user_id = current_user_or_session['user_id']
            with db.get_cursor() as cursor:
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
                    ORDER BY sc.created_at DESC
                """, (user_id,))
                cart_items = cursor.fetchall()
                cart_data = await _convert_db_cart_to_response(cart_items)
                return cart_data
        else:
            # Guest user - get cart from session or fallback
            if session and session.cart_items:
                cart_items = session.cart_items if session.cart_items is not None else {}
                cart_response = await _convert_session_cart_to_response(cart_items)
                return cart_response
            else:
                # Check if we have fallback cart items
                fallback_cart = current_user_or_session.get('cart_items', {})
                if fallback_cart:
                    cart_response = await _convert_session_cart_to_response(fallback_cart)
                    return cart_response
                else:
                    return CartResponse(items=[], subtotal=0.0, total_items=0)

    except Exception as e:
        logger.error(f"Failed to fetch cart: {e}")
        # Return empty cart instead of error
        return CartResponse(items=[], subtotal=0.0, total_items=0)


@router.post("/cart/{product_id}")
async def add_to_cart(
        request: Request,
        product_id: int,
        quantity: int = 1,
        variation_id: Optional[int] = None,
        current_user_or_session: dict = Depends(get_current_user_or_session)
):
    try:
        if quantity < 1:
            raise HTTPException(status_code=400, detail="Quantity must be at least 1")

        # Validate product exists and is available
        with db.get_cursor() as cursor:
            cursor.execute("""
                SELECT id, name, stock_quantity, stock_status, max_cart_quantity, base_price
                FROM products WHERE id = %s AND status = 'active'
            """, (product_id,))
            product = cursor.fetchone()
            if not product:
                raise HTTPException(status_code=404, detail="Product not found")

            if product['stock_status'] == 'out_of_stock':
                raise HTTPException(status_code=400, detail="Product is out of stock")

            max_cart_quantity = getattr(config, 'max_cart_quantity_per_product', 20)
            product_max_quantity = product['max_cart_quantity']
            if product_max_quantity:
                max_quantity = min(product_max_quantity, max_cart_quantity)
            else:
                max_quantity = max_cart_quantity

            if quantity > product['stock_quantity'] and product['stock_status'] != 'on_backorder':
                raise HTTPException(status_code=400, detail=f"Only {product['stock_quantity']} items available")

            if quantity > max_quantity:
                raise HTTPException(status_code=400, detail=f"Maximum {max_quantity} items can be added")

        session = current_user_or_session.get('session')
        session_id = current_user_or_session.get('session_id')

        if not current_user_or_session.get('is_guest'):
            # LOGGED IN USER - this part works
            user_id = current_user_or_session['user_id']
            with db.get_cursor() as cursor:
                cursor.execute("""
                    SELECT id, quantity FROM shopping_cart
                    WHERE user_id = %s AND product_id = %s
                    AND (variation_id = %s OR (variation_id IS NULL AND %s IS NULL))
                """, (user_id, product_id, variation_id, variation_id))
                existing_item = cursor.fetchone()

                if existing_item:
                    new_quantity = existing_item['quantity'] + quantity
                    if new_quantity > max_quantity:
                        raise HTTPException(status_code=400, detail=f"Maximum {max_quantity} items can be added")
                    cursor.execute("UPDATE shopping_cart SET quantity = %s WHERE id = %s",
                                   (new_quantity, existing_item['id']))
                else:
                    cursor.execute("""
                        INSERT INTO shopping_cart (user_id, product_id, variation_id, quantity)
                        VALUES (%s, %s, %s, %s)
                    """, (user_id, product_id, variation_id, quantity))

                redis_client.delete(f"user_cart:{user_id}")
                return {"message": "Product added to cart", "session_based": False}

        else:
            # GUEST USER - FIXED VERSION
            if not session_id or not session:
                # Create new guest session if none exists
                guest_id = str(uuid.uuid4())
                ip_address = request.client.host if request.client else 'unknown'
                user_agent = request.headers.get("user-agent", "")

                session = session_service.get_or_create_guest_session(guest_id, ip_address, user_agent)
                if session:
                    session_id = session.session_id
                    request.state.session = session
                    request.state.session_id = session_id
                else:
                    raise HTTPException(status_code=500, detail="Failed to create guest session")

            # Get current cart items
            cart_items = {}
            if session and session.cart_items:
                cart_items = session.cart_items.copy()
            elif session_id:
                # Load fresh session data from Redis
                loaded_session = session_service.get_session(session_id)
                if loaded_session and loaded_session.cart_items:
                    cart_items = loaded_session.cart_items.copy()

            # Generate item key
            item_key = f"{product_id}_{variation_id}" if variation_id else str(product_id)

            # Update cart items
            if item_key in cart_items:
                new_quantity = cart_items[item_key]['quantity'] + quantity
                if new_quantity > max_quantity:
                    raise HTTPException(status_code=400, detail=f"Maximum {max_quantity} items can be added")
                cart_items[item_key]['quantity'] = new_quantity
            else:
                cart_items[item_key] = {
                    'product_id': product_id,
                    'variation_id': variation_id,
                    'quantity': quantity
                }

            # CRITICAL FIX: Update session with cart items
            success = session_service.update_session_data(session_id, {"cart_items": cart_items})

            if success:
                # Verify the update worked
                updated_session = session_service.get_session(session_id)
                actual_cart_count = len(
                    updated_session.cart_items) if updated_session and updated_session.cart_items else 0

                logger.info(f"✅ Guest cart updated: session_id={session_id}, items_count={actual_cart_count}")

                return {
                    "message": "Product added to cart",
                    "session_based": True,
                    "session_id": session_id,
                    "cart_items_count": actual_cart_count
                }
            else:
                logger.error(f"❌ Failed to update guest cart in session: {session_id}")
                raise HTTPException(status_code=500, detail="Failed to update cart")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to add to cart: {e}")
        raise HTTPException(status_code=500, detail="Failed to add to cart")


@router.put("/cart/{cart_item_id}")
async def update_cart_item(
        request: Request,
        cart_item_id: int,
        quantity: int,
        current_user_or_session: dict = Depends(get_current_user_or_session)
):
    try:
        await rate_limiter.check_rate_limit(request)

        if quantity < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Quantity cannot be negative"
            )

        session = current_user_or_session.get('session')
        session_id = current_user_or_session.get('session_id')

        if not current_user_or_session.get('is_guest'):
            user_id = current_user_or_session['user_id']
            with db.get_cursor() as cursor:
                cursor.execute("""
                    SELECT sc.*, p.stock_quantity, p.stock_status, p.max_cart_quantity
                    FROM shopping_cart sc
                    JOIN products p ON sc.product_id = p.id
                    WHERE sc.id = %s AND sc.user_id = %s
                """, (cart_item_id, user_id))

                cart_item = cursor.fetchone()
                if not cart_item:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Cart item not found"
                    )

                if quantity == 0:
                    cursor.execute("DELETE FROM shopping_cart WHERE id = %s", (cart_item_id,))
                    redis_client.delete(f"user_cart:{user_id}")
                    return {"message": "Item removed from cart", "session_based": False}

                max_quantity = min(cart_item['max_cart_quantity'] or 20, cart_item['stock_quantity'])
                if quantity > max_quantity and cart_item['stock_status'] != 'on_backorder':
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Maximum {max_quantity} items available"
                    )

                cursor.execute("""
                    UPDATE shopping_cart
                    SET quantity = %s, updated_at = NOW()
                    WHERE id = %s
                """, (quantity, cart_item_id))

                redis_client.delete(f"user_cart:{user_id}")
                return {"message": "Cart updated successfully", "session_based": False}
        else:
            if session and session_id and session.cart_items:
                try:
                    product_id = cart_item_id
                    cart_items = session.cart_items.copy()
                    item_key = None

                    for key, item in cart_items.items():
                        if item['product_id'] == product_id:
                            item_key = key
                            break

                    if item_key:
                        if quantity == 0:
                            del cart_items[item_key]
                        else:
                            with db.get_cursor() as cursor:
                                cursor.execute("""
                                    SELECT stock_quantity, max_cart_quantity
                                    FROM products WHERE id = %s
                                """, (product_id,))
                                product = cursor.fetchone()
                                if product:
                                    max_quantity = min(product['max_cart_quantity'] or 20, product['stock_quantity'])
                                    if quantity > max_quantity:
                                        raise HTTPException(
                                            status_code=status.HTTP_400_BAD_REQUEST,
                                            detail=f"Maximum {max_quantity} items available"
                                        )
                            cart_items[item_key]['quantity'] = quantity

                        success = session_service.update_session_data(session_id, {"cart_items": cart_items})
                        if success:
                            return {"message": "Cart updated successfully", "session_based": True}
                        else:
                            raise HTTPException(
                                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail="Failed to update cart"
                            )
                    else:
                        raise HTTPException(
                            status_code=status.HTTP_404_NOT_FOUND,
                            detail="Cart item not found"
                        )

                except HTTPException:
                    raise
                except Exception as e:
                    logger.error(f"Session cart update failed: {e}")
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Failed to update cart"
                    )
            else:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Cart item not found"
                )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update cart: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update cart"
        )


@router.delete("/cart/{cart_item_id}")
async def remove_from_cart(
        request: Request,
        cart_item_id: int,
        current_user_or_session: dict = Depends(get_current_user_or_session)
):
    try:
        await rate_limiter.check_rate_limit(request)

        session = current_user_or_session.get('session')
        session_id = current_user_or_session.get('session_id')

        if not current_user_or_session.get('is_guest'):
            # Authenticated user - remove from database cart
            user_id = current_user_or_session['user_id']

            with db.get_cursor() as cursor:
                cursor.execute("DELETE FROM shopping_cart WHERE id = %s AND user_id = %s", (cart_item_id, user_id))
                if cursor.rowcount == 0:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Cart item not found"
                    )

                redis_client.delete(f"user_cart:{user_id}")
                return {"message": "Item removed from cart", "session_based": False}
        else:
            # Guest user - remove from session cart
            if session and session_id and session.cart_items:
                try:
                    product_id = cart_item_id
                    cart_items = session.cart_items.copy()
                    item_key = None

                    for key, item in cart_items.items():
                        if item['product_id'] == product_id:
                            item_key = key
                            break

                    if item_key:
                        del cart_items[item_key]
                        success = session_service.update_session_data(session_id, {"cart_items": cart_items})

                        if success:
                            return {"message": "Item removed from cart", "session_based": True}
                        else:
                            raise HTTPException(
                                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail="Failed to remove from cart"
                            )
                    else:
                        raise HTTPException(
                            status_code=status.HTTP_404_NOT_FOUND,
                            detail="Cart item not found"
                        )

                except HTTPException:
                    raise
                except Exception as e:
                    logger.error(f"Session cart removal failed: {e}")
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Failed to remove from cart"
                    )
            else:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Cart item not found"
                )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to remove from cart: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to remove from cart"
        )


@router.delete("/cart")
async def clear_cart(
        request: Request,
        current_user_or_session: dict = Depends(get_current_user_or_session)
):
    try:
        await rate_limiter.check_rate_limit(request)

        session_id = current_user_or_session.get('session_id')

        if not current_user_or_session.get('is_guest'):
            # Authenticated user - clear database cart
            user_id = current_user_or_session['user_id']

            with db.get_cursor() as cursor:
                cursor.execute("DELETE FROM shopping_cart WHERE user_id = %s", (user_id,))
                redis_client.delete(f"user_cart:{user_id}")
                return {"message": "Cart cleared successfully", "session_based": False}
        else:
            # Guest user - clear session cart
            if session_id:
                success = session_service.update_session_data(session_id, {"cart_items": {}})
                if success:
                    return {"message": "Cart cleared successfully", "session_based": True}
                else:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Failed to clear cart"
                    )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Session not available"
                )

    except Exception as e:
        logger.error(f"Failed to clear cart: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to clear cart"
        )


@router.get("/session/info")
async def get_session_info(request: Request, current_user: dict = Depends(get_current_user)):
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
            "cart_items_count": len(session.cart_items) if session.cart_items else 0,
            "ip_address": session.ip_address
        }
    except Exception as e:
        logger.error(f"Failed to get session info: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get session information"
        )


@router.post("/session/cart/migrate-to-user")
async def migrate_session_cart_to_user(request: Request, current_user: dict = Depends(get_current_user)):
    try:
        user_id = current_user['sub']

        # Get the user session (should already exist due to auth)
        user_session = session_service.get_session_by_user_id(user_id)
        if not user_session:
            logger.error(f"No user session found for user {user_id}")
            raise HTTPException(status_code=404, detail="User session not found")

        # Get current guest session if any
        current_session = get_session(request)
        migrated_count = 0

        with db.get_cursor() as cursor:
            if current_session and current_session.session_type == SessionType.GUEST:
                migrated_count = migrate_guest_cart_to_user_database(current_session, user_id, cursor)
                logger.info(f"🔄 Migrated {migrated_count} cart items from guest session to user {user_id}")

                # Update user session cart if items were migrated
                if migrated_count > 0:
                    # The migration function should handle the database update
                    # We just need to ensure the session reflects the changes
                    session_service.update_session_activity(user_session.session_id)

        redis_client.delete(f"user_cart:{user_id}")
        logger.info(f"Cart migration completed for user {user_id}, {migrated_count} items migrated")

        return {
            "message": "Cart migrated successfully",
            "items_migrated": migrated_count,
            "session_id": user_session.session_id
        }

    except Exception as e:
        logger.error(f"Failed to migrate cart: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to migrate cart"
        )


@router.post("/profile/avatar")
async def upload_avatar(
        file: UploadFile = File(...),
        current_user: dict = Depends(get_current_user)
):
    try:
        user_id = current_user['sub']
        allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']

        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid file type. Only JPEG, PNG, GIF, and WebP are allowed."
            )

        max_size = 5 * 1024 * 1024
        file.file.seek(0, 2)
        file_size = file.file.tell()
        file.file.seek(0)

        if file_size > max_size:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File too large. Maximum size is 5MB."
            )

        file_extension = file.filename.split('.')[-1]
        unique_filename = f"avatar_{user_id}_{int(datetime.now().timestamp())}.{file_extension}"
        file_path = f"/app/uploads/avatars/{unique_filename}"

        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)

        with db.get_cursor() as cursor:
            cursor.execute(
                "UPDATE users SET avatar_url = %s WHERE id = %s",
                (f"/uploads/avatars/{unique_filename}", user_id)
            )

        invalidate_user_cache(user_id)

        return {
            "message": "Avatar uploaded successfully",
            "avatar_url": f"/uploads/avatars/{unique_filename}"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to upload avatar: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload avatar"
        )


@router.post("/security/invalidate-all-sessions")
async def invalidate_all_sessions(
        current_user: dict = Depends(get_current_user)
):
    try:
        user_id = current_user['sub']
        success = session_service.invalidate_all_user_sessions(user_id)

        if success:
            logger.info(f"All sessions invalidated for user {user_id}")
            return {"message": "All other sessions have been invalidated"}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to invalidate sessions"
            )
    except Exception as e:
        logger.error(f"Failed to invalidate sessions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to invalidate sessions"
        )


@router.post("/change-password")
async def change_password(
        current_password: str = Form(...),
        new_password: str = Form(...),
        confirm_password: str = Form(...),
        current_user: dict = Depends(get_current_user)
):
    try:
        user_id = current_user['sub']

        if not current_password or not new_password or not confirm_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="All password fields are required"
            )

        if new_password != confirm_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="New password and confirmation do not match"
            )

        if current_password == new_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="New password must be different from current password"
            )

        if len(new_password) < 8:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must be at least 8 characters long"
            )

        if not any(char.isdigit() for char in new_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must contain at least one number"
            )

        if not any(char.isupper() for char in new_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must contain at least one uppercase letter"
            )

        if not any(char.islower() for char in new_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must contain at least one lowercase letter"
            )

        with db.get_cursor() as cursor:
            cursor.execute("""
                SELECT u.password_hash,
                       GROUP_CONCAT(ph.password_hash) as previous_hashes
                FROM users u
                LEFT JOIN password_history ph ON u.id = ph.user_id
                WHERE u.id = %s
                GROUP BY u.id
            """, (user_id,))

            user_data = cursor.fetchone()
            if not user_data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )

            if not verify_password(current_password, user_data['password_hash']):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Current password is incorrect"
                )

            if user_data['previous_hashes']:
                previous_hashes = user_data['previous_hashes'].split(',')
                for old_hash in previous_hashes[-5:]:
                    if verify_password(new_password, old_hash):
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail="New password cannot be the same as any of your previous 5 passwords"
                        )

            new_password_hash = get_password_hash(new_password)

            cursor.execute("START TRANSACTION")
            try:
                cursor.execute(
                    "UPDATE users SET password_hash = %s WHERE id = %s",
                    (new_password_hash, user_id)
                )
                cursor.execute(
                    "INSERT INTO password_history (user_id, password_hash) VALUES (%s, %s)",
                    (user_id, new_password_hash)
                )
                cursor.execute("""
                    DELETE FROM password_history
                    WHERE user_id = %s
                    AND id NOT IN (
                        SELECT id FROM (
                            SELECT id FROM password_history
                            WHERE user_id = %s
                            ORDER BY created_at DESC
                            LIMIT 10
                        ) AS recent_passwords
                    )
                """, (user_id, user_id))
                cursor.execute("COMMIT")
            except Exception as e:
                cursor.execute("ROLLBACK")
                raise e

            try:
                user_sessions = redis_client.keys(f"user_session:{user_id}:*")
                if user_sessions:
                    redis_client.delete(*user_sessions)
                invalidate_user_cache(user_id)

                cursor.execute("""
                    INSERT INTO security_logs (user_id, action, ip_address, user_agent)
                    VALUES (%s, 'password_change', %s, %s)
                """, (user_id, 'unknown', 'unknown'))
            except Exception as e:
                logger.error(f"Failed to cleanup sessions after password change: {e}")

            logger.info(f"Password changed successfully for user {user_id}")
            return {"message": "Password changed successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to change password: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to change password"
        )


@router.get("/admin/users")
async def get_all_users(
        skip: int = 0,
        limit: int = 100,
        current_user: dict = Depends(get_current_user)  # ✅ Simple and working
):
    # Manual role check
    user_roles = current_user.get('roles', [])
    if not any(role in ['admin', 'super_admin'] for role in user_roles):
        raise HTTPException(status_code=403, detail="Admin access required")
    try:
        with db.get_cursor() as cursor:
            cursor.execute("""
                SELECT
                    u.id, u.uuid, u.email, u.first_name, u.last_name, u.phone,
                    u.email_verified, u.phone_verified, u.is_active, u.last_login,
                    u.created_at, u.updated_at,
                    GROUP_CONCAT(DISTINCT ur.name) as roles
                FROM users u
                LEFT JOIN user_role_assignments ura ON u.id = ura.user_id
                LEFT JOIN user_roles ur ON ura.role_id = ur.id
                GROUP BY u.id
                ORDER BY u.created_at DESC
                LIMIT %s OFFSET %s
            """, (limit, skip))
            users = cursor.fetchall()

            cursor.execute("SELECT COUNT(*) as total FROM users")
            total = cursor.fetchone()['total']

            return {
                "users": users,
                "total": total,
                "skip": skip,
                "limit": limit
            }
    except Exception as e:
        logger.error(f"Failed to fetch users: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch users"
        )


@router.put("/admin/users/{user_id}/status")
async def update_user_status(
        user_id: int,
        is_active: bool,
        current_user: dict = Depends(get_current_user)  # ✅ Fixed
):
    # Manual role check add karo
    user_roles = current_user.get('roles', [])
    if not any(role in ['admin', 'super_admin'] for role in user_roles):
        raise HTTPException(status_code=403, detail="Admin access required")
    try:
        with db.get_cursor() as cursor:
            cursor.execute(
                "UPDATE users SET is_active = %s, updated_at = NOW() WHERE id = %s",
                (is_active, user_id)
            )

            if cursor.rowcount == 0:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )

            action = "activated" if is_active else "deactivated"
            logger.info(f"User {user_id} {action} by admin {current_user['sub']}")

            return {"message": f"User {action} successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update user status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user status"
        )