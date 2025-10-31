from fastapi import APIRouter, HTTPException, Depends, Form, status, BackgroundTasks, UploadFile, File, Request, Header
from typing import List, Optional, Dict, Any
from shared import config, db, sanitize_input, get_logger, redis_client, rabbitmq_client
from shared.security import verify_password, get_password_hash
from shared.auth_middleware import get_current_user
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


def require_roles(required_roles: List[str]):
    def role_dependency(current_user: dict = Depends(get_current_user)):
        user_roles = current_user.get('roles', [])
        if not any(role in user_roles for role in required_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient role permissions"
            )
        return current_user

    return role_dependency


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


def cache_guest_cart(guest_id: str, cart_data: dict, expire: int = 86400):
    try:
        key = f"guest_cart:{guest_id}"
        redis_client.setex(key, expire, json.dumps(cart_data))
        logger.info(f"Cached cart for guest {guest_id}")
    except Exception as e:
        logger.error(f"Failed to cache guest cart: {e}")


def get_cached_guest_cart(guest_id: str) -> Optional[dict]:
    try:
        key = f"guest_cart:{guest_id}"
        data = redis_client.get(key)
        if data:
            return json.loads(data)
        return None
    except Exception as e:
        logger.error(f"Failed to get cached guest cart: {e}")
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


def get_or_create_guest_id(request: Request, x_guest_id: Optional[str] = Header(None)) -> str:
    if x_guest_id:
        return x_guest_id
    guest_id = request.cookies.get("guest_id")
    if guest_id:
        return guest_id
    return str(uuid.uuid4())


async def get_current_user_or_guest(request: Request, x_guest_id: Optional[str] = Header(None)):
    try:
        # First try to get authenticated user
        current_user = await get_current_user(request)
        return {
            "user_id": current_user['sub'],
            "is_guest": False,
            "session_based": False,
            "session": None
        }
    except HTTPException:
        # Try to get session
        session = get_session(request)
        if session and session.session_type == SessionType.GUEST:
            return {
                "guest_id": session.guest_id,
                "is_guest": True,
                "session_based": True,
                "session": session
            }

        # Fall back to old guest system
        guest_id = get_or_create_guest_id(request, x_guest_id)
        return {
            "guest_id": guest_id,
            "is_guest": True,
            "session_based": False,
            "session": None
        }


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
            logger.info(f"Returning cached profile for user {user_id}")
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
                email=user['email'],
                mobile=user['phone'],
                first_name=user['first_name'],
                last_name=user['last_name'],
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

            # Return updated profile
            cached_profile = get_cached_user_profile(user_id)
            if cached_profile:
                return UserProfileResponse(**cached_profile)

            # Fallback to fetching from database
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
            logger.info(f"Returning cached addresses for user {user_id}")
            return [AddressResponse(**addr) for addr in cached_addresses]

        with db.get_cursor() as cursor:
            cursor.execute("""
                SELECT * FROM user_addresses
                WHERE user_id = %s
                ORDER BY is_default DESC, created_at DESC
            """, (user_id,))
            addresses = cursor.fetchall()
            address_list = [
                AddressResponse(
                    id=addr['id'],
                    user_id=addr['user_id'],
                    address_type=addr['address_type'],
                    full_name=addr['full_name'],
                    phone=addr['phone'],
                    address_line1=addr['address_line1'],
                    address_line2=addr['address_line2'],
                    landmark=addr['landmark'],
                    city=addr['city'],
                    state=addr['state'],
                    country=addr['country'],
                    postal_code=addr['postal_code'],
                    address_type_detail=addr['address_type_detail'],
                    is_default=bool(addr['is_default']),
                    created_at=addr['created_at'],
                    updated_at=addr['updated_at']
                )
                for addr in addresses
            ]
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
        with db.get_cursor() as cursor:
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
            logger.info(f"Returning cached wishlist for user {user_id}")
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
        current_user_or_guest: dict = Depends(get_current_user_or_guest)
):
    try:
        await rate_limiter.check_rate_limit(request)

        # SESSION-BASED CART: Try to get cart from session first
        session = current_user_or_guest.get('session')
        if session and current_user_or_guest.get('session_based'):
            logger.info(f"Getting cart from session for guest {session.guest_id}")
            return await _convert_session_cart_to_response(session.cart_items)

        # FALLBACK: Use existing database/redis cart system
        if current_user_or_guest.get('is_guest'):
            guest_id = current_user_or_guest['guest_id']
            cached_cart = get_cached_guest_cart(guest_id)
            if cached_cart:
                logger.info(f"Returning cached cart for guest {guest_id}")
                return CartResponse(**cached_cart)
            return CartResponse(items=[], subtotal=0.0, total_items=0)
        else:
            user_id = current_user_or_guest['user_id']
            cached_cart = get_cached_user_cart(user_id)
            if cached_cart:
                logger.info(f"Returning cached cart for user {user_id}")
                return CartResponse(**cached_cart)

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
                cache_user_cart(user_id, cart_data.dict())
                return cart_data

    except Exception as e:
        logger.error(f"Failed to fetch cart: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch cart"
        )


async def _convert_session_cart_to_response(cart_items: Dict[str, Any]) -> CartResponse:
    """Convert session cart items to CartResponse"""
    try:
        items = []
        subtotal = 0.0
        total_items = 0

        if not cart_items:
            return CartResponse(items=[], subtotal=0.0, total_items=0)

        for product_id_str, item_data in cart_items.items():
            try:
                product_id = int(product_id_str)

                # Get product details from database
                with db.get_cursor() as cursor:
                    cursor.execute("""
                        SELECT id, name, slug, main_image_url, base_price, 
                               stock_quantity, stock_status, max_cart_quantity
                        FROM products WHERE id = %s AND status = 'active'
                    """, (product_id,))
                    product = cursor.fetchone()

                    if product:
                        item_total = float(product['base_price']) * item_data['quantity']
                        subtotal += item_total
                        total_items += item_data['quantity']

                        items.append({
                            'id': product_id,  # Using product_id as temporary ID
                            'product_id': product_id,
                            'variation_id': item_data.get('variation_id'),
                            'product_name': product['name'],
                            'product_slug': product['slug'],
                            'product_image': product['main_image_url'],
                            'product_price': float(product['base_price']),
                            'quantity': item_data['quantity'],
                            'total_price': item_total,
                            'stock_quantity': product['stock_quantity'],
                            'stock_status': product['stock_status'],
                            'max_cart_quantity': product['max_cart_quantity']
                        })
            except (ValueError, KeyError) as e:
                logger.warning(f"Skipping invalid cart item {product_id_str}: {e}")
                continue

        return CartResponse(
            items=items,
            subtotal=subtotal,
            total_items=total_items
        )
    except Exception as e:
        logger.error(f"Failed to convert session cart: {e}")
        return CartResponse(items=[], subtotal=0.0, total_items=0)


async def _convert_db_cart_to_response(cart_items: List[Dict]) -> CartResponse:
    """Convert database cart items to CartResponse"""
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


@router.post("/cart/{product_id}")
async def add_to_cart(
        request: Request,
        product_id: int,
        quantity: int = 1,
        variation_id: Optional[int] = None,
        current_user_or_guest: dict = Depends(get_current_user_or_guest)
):
    try:
        await rate_limiter.check_rate_limit(request)

        if quantity < 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Quantity must be at least 1"
            )

        with db.get_cursor() as cursor:
            cursor.execute("""
                SELECT id, name, stock_quantity, stock_status, max_cart_quantity, base_price
                FROM products
                WHERE id = %s AND status = 'active'
            """, (product_id,))
            product = cursor.fetchone()

            if not product:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Product not found"
                )

            if product['stock_status'] == 'out_of_stock':
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Product is out of stock"
                )

            if quantity > product['stock_quantity'] and product['stock_status'] != 'on_backorder':
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Only {product['stock_quantity']} items available in stock"
                )

            max_quantity = min(product['max_cart_quantity'], product['stock_quantity'])
            if quantity > max_quantity:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Maximum {max_quantity} items can be added to cart"
                )

        # SESSION-BASED CART: Add to session cart
        session = current_user_or_guest.get('session')
        session_id = get_session_id(request)

        if session and current_user_or_guest.get('session_based') and session_id:
            try:
                # Get current cart items from session
                cart_items = session.cart_items.copy() if session.cart_items else {}

                # Generate unique key for this cart item (product + variation)
                item_key = f"{product_id}_{variation_id}" if variation_id else str(product_id)

                # Update quantity
                if item_key in cart_items:
                    new_quantity = cart_items[item_key]['quantity'] + quantity
                    if new_quantity > max_quantity:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Maximum {max_quantity} items can be added to cart"
                        )
                    cart_items[item_key]['quantity'] = new_quantity
                else:
                    cart_items[item_key] = {
                        'product_id': product_id,
                        'variation_id': variation_id,
                        'quantity': quantity
                    }

                # Update session with new cart items
                success = session_service.update_session_data(session_id, {"cart_items": cart_items})
                if success:
                    logger.info(f"Product {product_id} added to session cart for guest {session.guest_id}")
                    return {"message": "Product added to cart", "session_based": True}
                else:
                    logger.warning("Failed to update session cart, falling back to database")

            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Session cart update failed: {e}, falling back to database")

        # FALLBACK: Use existing database cart system
        if current_user_or_guest.get('is_guest'):
            guest_id = current_user_or_guest['guest_id']
            # For guest users without session, use the old guest cart system
            guest_cart = get_cached_guest_cart(guest_id) or {"items": [], "subtotal": 0.0, "total_items": 0}
            cache_guest_cart(guest_id, guest_cart)
            return {"message": "Product added to cart", "guest_id": guest_id, "session_based": False}
        else:
            user_id = current_user_or_guest['user_id']
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
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Maximum {max_quantity} items can be added to cart"
                        )
                    cursor.execute("""
                        UPDATE shopping_cart
                        SET quantity = %s, updated_at = NOW()
                        WHERE id = %s
                    """, (new_quantity, existing_item['id']))
                else:
                    cursor.execute("""
                        INSERT INTO shopping_cart (user_id, product_id, variation_id, quantity)
                        VALUES (%s, %s, %s, %s)
                    """, (user_id, product_id, variation_id, quantity))

                redis_client.delete(f"user_cart:{user_id}")
                logger.info(f"Product {product_id} added to database cart for user {user_id}")
                return {"message": "Product added to cart", "session_based": False}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to add to cart: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add to cart"
        )


@router.put("/cart/{cart_item_id}")
async def update_cart_item(
        request: Request,
        cart_item_id: int,
        quantity: int,
        current_user_or_guest: dict = Depends(get_current_user_or_guest)
):
    try:
        await rate_limiter.check_rate_limit(request)

        if quantity < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Quantity cannot be negative"
            )

        # SESSION-BASED CART: Update session cart
        session = current_user_or_guest.get('session')
        session_id = get_session_id(request)

        if session and current_user_or_guest.get('session_based') and session_id and session.cart_items:
            try:
                # For session carts, we use product_id as cart_item_id
                product_id = cart_item_id
                cart_items = session.cart_items.copy()

                # Find the item in session cart
                item_key = None
                for key, item in cart_items.items():
                    if item['product_id'] == product_id:
                        item_key = key
                        break

                if item_key:
                    if quantity == 0:
                        del cart_items[item_key]
                    else:
                        # Validate quantity against stock
                        with db.get_cursor() as cursor:
                            cursor.execute("""
                                SELECT stock_quantity, max_cart_quantity 
                                FROM products WHERE id = %s
                            """, (product_id,))
                            product = cursor.fetchone()
                            if product:
                                max_quantity = min(product['max_cart_quantity'], product['stock_quantity'])
                                if quantity > max_quantity:
                                    raise HTTPException(
                                        status_code=status.HTTP_400_BAD_REQUEST,
                                        detail=f"Maximum {max_quantity} items available"
                                    )
                        cart_items[item_key]['quantity'] = quantity

                    # Update session
                    success = session_service.update_session_data(session_id, {"cart_items": cart_items})
                    if success:
                        logger.info(f"Session cart updated for guest {session.guest_id}")
                        return {"message": "Cart updated successfully", "session_based": True}

            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Session cart update failed: {e}")

        # FALLBACK: Use existing database cart system
        if current_user_or_guest.get('is_guest'):
            # For guest users without session, return simple response
            return {"message": "Cart updated successfully", "session_based": False}
        else:
            user_id = current_user_or_guest['user_id']
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

                max_quantity = min(cart_item['max_cart_quantity'], cart_item['stock_quantity'])
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
        current_user_or_guest: dict = Depends(get_current_user_or_guest)
):
    try:
        await rate_limiter.check_rate_limit(request)

        # SESSION-BASED CART: Remove from session cart
        session = current_user_or_guest.get('session')
        session_id = get_session_id(request)

        if session and current_user_or_guest.get('session_based') and session_id and session.cart_items:
            try:
                # For session carts, we use product_id as cart_item_id
                product_id = cart_item_id
                cart_items = session.cart_items.copy()

                # Find and remove the item
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

            except Exception as e:
                logger.error(f"Session cart removal failed: {e}")

        # FALLBACK: Use existing database cart system
        if current_user_or_guest.get('is_guest'):
            return {"message": "Item removed from cart", "session_based": False}
        else:
            user_id = current_user_or_guest['user_id']
            with db.get_cursor() as cursor:
                cursor.execute("DELETE FROM shopping_cart WHERE id = %s AND user_id = %s", (cart_item_id, user_id))
                if cursor.rowcount == 0:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Cart item not found"
                    )
                redis_client.delete(f"user_cart:{user_id}")
                return {"message": "Item removed from cart", "session_based": False}

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
        current_user_or_guest: dict = Depends(get_current_user_or_guest)
):
    try:
        await rate_limiter.check_rate_limit(request)

        # SESSION-BASED CART: Clear session cart
        session_id = get_session_id(request)
        if session_id:
            success = session_service.update_session_data(session_id, {"cart_items": {}})
            if success:
                return {"message": "Cart cleared successfully", "session_based": True}

        # FALLBACK: Use existing database cart system
        if current_user_or_guest.get('is_guest'):
            guest_id = current_user_or_guest['guest_id']
            cache_guest_cart(guest_id, {"items": [], "subtotal": 0.0, "total_items": 0})
            return {"message": "Cart cleared successfully", "session_based": False}
        else:
            user_id = current_user_or_guest['user_id']
            with db.get_cursor() as cursor:
                cursor.execute("DELETE FROM shopping_cart WHERE user_id = %s", (user_id,))
                redis_client.delete(f"user_cart:{user_id}")
                return {"message": "Cart cleared successfully", "session_based": False}

    except Exception as e:
        logger.error(f"Failed to clear cart: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to clear cart"
        )


@router.get("/session/info")
async def get_session_info(request: Request, current_user: dict = Depends(get_current_user)):
    """Get current session information for authenticated users"""
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


@router.post("/session/cart/migrate")
async def migrate_cart_to_session(
        request: Request,
        current_user: dict = Depends(get_current_user)
):
    """Migrate database cart to session cart for authenticated users"""
    try:
        user_id = current_user['sub']
        session_id = get_session_id(request)

        if not session_id:
            raise HTTPException(status_code=404, detail="Session not found")

        # Get cart from database
        with db.get_cursor() as cursor:
            cursor.execute("""
                SELECT product_id, variation_id, quantity
                FROM shopping_cart
                WHERE user_id = %s
            """, (user_id,))
            db_cart_items = cursor.fetchall()

        # Convert to session cart format
        session_cart = {}
        for item in db_cart_items:
            item_key = f"{item['product_id']}_{item['variation_id']}" if item['variation_id'] else str(
                item['product_id'])
            session_cart[item_key] = {
                'product_id': item['product_id'],
                'variation_id': item['variation_id'],
                'quantity': item['quantity']
            }

        # Update session
        success = session_service.update_session_data(session_id, {"cart_items": session_cart})
        if not success:
            raise HTTPException(status_code=500, detail="Failed to migrate cart")

        # Clear database cart
        with db.get_cursor() as cursor:
            cursor.execute("DELETE FROM shopping_cart WHERE user_id = %s", (user_id,))
        redis_client.delete(f"user_cart:{user_id}")

        logger.info(f"Cart migrated to session for user {user_id}")
        return {"message": "Cart migrated to session successfully", "items_migrated": len(session_cart)}

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


@router.post("/change-password")
async def change_password(
        current_password: str = Form(...),
        new_password: str = Form(...),
        current_user: dict = Depends(get_current_user)
):
    try:
        user_id = current_user['sub']
        if len(new_password) < 8:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must be at least 8 characters long"
            )

        with db.get_cursor() as cursor:
            cursor.execute("SELECT password_hash FROM users WHERE id = %s", (user_id,))
            user = cursor.fetchone()
            if not user or not verify_password(current_password, user['password_hash']):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Current password is incorrect"
                )

            new_password_hash = get_password_hash(new_password)
            cursor.execute(
                "UPDATE users SET password_hash = %s WHERE id = %s",
                (new_password_hash, user_id)
            )
            cursor.execute(
                "INSERT INTO password_history (user_id, password_hash) VALUES (%s, %s)",
                (user_id, new_password_hash)
            )

            logger.info(f"Password changed for user {user_id}")
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
        current_user: dict = Depends(require_roles(["admin", "super_admin"]))
):
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
        current_user: dict = Depends(require_roles(["admin", "super_admin"]))
):
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


@router.get("/debug/test")
async def debug_test():
    import traceback
    try:
        maintenance_mode = config.maintenance_mode
        debug_mode = config.debug_mode
        db_status = "unknown"
        user_count = 0
        try:
            with db.get_cursor() as cursor:
                cursor.execute("SELECT 1 as test")
                db_status = "connected"
                cursor.execute("SELECT COUNT(*) as count FROM users")
                user_count = cursor.fetchone()['count']
        except Exception as db_error:
            db_status = f"error: {str(db_error)}"
            logger.error(f"Database error: {db_error}")
        redis_status = "unknown"
        try:
            redis_status = "connected" if redis_client.ping() else "disconnected"
        except Exception as redis_error:
            redis_status = f"error: {str(redis_error)}"
        return {
            "status": "ok",
            "maintenance_mode": maintenance_mode,
            "debug_mode": debug_mode,
            "database": db_status,
            "user_count": user_count,
            "redis": redis_status,
            "service": "user"
        }
    except Exception as e:
        error_traceback = traceback.format_exc()
        return {
            "status": "error",
            "error_type": type(e).__name__,
            "error_message": str(e),
            "traceback": error_traceback,
            "service": "user"
        }