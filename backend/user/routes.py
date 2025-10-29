from fastapi import APIRouter, HTTPException, Depends, Form, status, BackgroundTasks, UploadFile, File, Request, Header
from typing import List, Optional, Dict, Any
from shared import config, db, sanitize_input, get_logger, redis_client, rabbitmq_client
from shared.security import verify_password, get_password_hash
from shared.auth_middleware import get_current_user
from shared.rate_limiter import rate_limiter
from shared.redis_client import redis_client
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
        redis_client.redis_client.setex(key, expire, json.dumps(profile_data))
        logger.info(f"Cached user profile for user {user_id}")
    except Exception as e:
        logger.error(f"Failed to cache user profile: {e}")


def get_cached_user_profile(user_id: int) -> Optional[dict]:
    try:
        key = f"user_profile:{user_id}"
        data = redis_client.redis_client.get(key)
        if data:
            return json.loads(data)
        return None
    except Exception as e:
        logger.error(f"Failed to get cached user profile: {e}")
        return None


def cache_user_addresses(user_id: int, addresses: List[dict], expire: int = 1800):
    try:
        key = f"user_addresses:{user_id}"
        redis_client.redis_client.setex(key, expire, json.dumps(addresses))
        logger.info(f"Cached addresses for user {user_id}")
    except Exception as e:
        logger.error(f"Failed to cache user addresses: {e}")


def get_cached_user_addresses(user_id: int) -> Optional[List[dict]]:
    try:
        key = f"user_addresses:{user_id}"
        data = redis_client.redis_client.get(key)
        if data:
            return json.loads(data)
        return None
    except Exception as e:
        logger.error(f"Failed to get cached user addresses: {e}")
        return None


def cache_user_wishlist(user_id: int, wishlist_data: dict, expire: int = 900):
    try:
        key = f"user_wishlist:{user_id}"
        redis_client.redis_client.setex(key, expire, json.dumps(wishlist_data))
        logger.info(f"Cached wishlist for user {user_id}")
    except Exception as e:
        logger.error(f"Failed to cache user wishlist: {e}")


def get_cached_user_wishlist(user_id: int) -> Optional[dict]:
    try:
        key = f"user_wishlist:{user_id}"
        data = redis_client.redis_client.get(key)
        if data:
            return json.loads(data)
        return None
    except Exception as e:
        logger.error(f"Failed to get cached user wishlist: {e}")
        return None


def cache_user_cart(user_id: int, cart_data: dict, expire: int = 600):
    try:
        key = f"user_cart:{user_id}"
        redis_client.redis_client.setex(key, expire, json.dumps(cart_data))
        logger.info(f"Cached cart for user {user_id}")
    except Exception as e:
        logger.error(f"Failed to cache user cart: {e}")


def get_cached_user_cart(user_id: int) -> Optional[dict]:
    try:
        key = f"user_cart:{user_id}"
        data = redis_client.redis_client.get(key)
        if data:
            return json.loads(data)
        return None
    except Exception as e:
        logger.error(f"Failed to get cached user cart: {e}")
        return None


def cache_guest_cart(guest_id: str, cart_data: dict, expire: int = 86400):  # 24 hours for guest carts
    try:
        key = f"guest_cart:{guest_id}"
        redis_client.redis_client.setex(key, expire, json.dumps(cart_data))
        logger.info(f"Cached cart for guest {guest_id}")
    except Exception as e:
        logger.error(f"Failed to cache guest cart: {e}")


def get_cached_guest_cart(guest_id: str) -> Optional[dict]:
    try:
        key = f"guest_cart:{guest_id}"
        data = redis_client.redis_client.get(key)
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
            redis_client.redis_client.delete(key)
        logger.info(f"Invalidated cache for user {user_id}")
    except Exception as e:
        logger.error(f"Failed to invalidate user cache: {e}")


def get_or_create_guest_id(request: Request, x_guest_id: Optional[str] = Header(None)) -> str:
    """Get or create guest ID for anonymous users"""
    if x_guest_id:
        return x_guest_id
    # Check cookies for existing guest ID
    guest_id = request.cookies.get("guest_id")
    if guest_id:
        return guest_id
    # Create new guest ID
    return str(uuid.uuid4())


async def get_current_user_or_guest(request: Request, x_guest_id: Optional[str] = Header(None)):
    """Get current user or guest ID for cart operations"""
    try:
        # Try to get authenticated user first
        return await get_current_user(request)
    except HTTPException:
        # If not authenticated, use guest ID
        guest_id = get_or_create_guest_id(request, x_guest_id)
        return {"guest_id": guest_id, "is_guest": True}


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
            cache_user_profile(user_id, profile_data.model_dump())
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
            if profile_data.first_name:
                update_fields.append("first_name = %s")
                update_params.append(sanitize_input(profile_data.first_name))
            if profile_data.last_name:
                update_fields.append("last_name = %s")
                update_params.append(sanitize_input(profile_data.last_name))
            if profile_data.phone:
                update_fields.append("phone = %s")
                update_params.append(sanitize_input(profile_data.phone))
            if profile_data.username:
                update_fields.append("username = %s")
                update_params.append(sanitize_input(profile_data.username))
            if profile_data.country_id:
                update_fields.append("country_id = %s")
                update_params.append(profile_data.country_id)
            if profile_data.preferred_currency:
                update_fields.append("preferred_currency = %s")
                update_params.append(profile_data.preferred_currency)
            if profile_data.preferred_language:
                update_fields.append("preferred_language = %s")
                update_params.append(profile_data.preferred_language)
            if profile_data.date_of_birth:
                update_fields.append("date_of_birth = %s")
                update_params.append(profile_data.date_of_birth)
            if profile_data.gender:
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
            return await get_user_profile(current_user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update user profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user profile"
        )


# ... (address endpoints remain the same - they require authentication)

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
            cache_user_addresses(user_id, [addr.model_dump() for addr in address_list])
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
                address_data.address_type_detail.value,
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


# ... (other address endpoints remain the same)

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
            cache_user_wishlist(user_id, wishlist_data.model_dump())
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
            redis_client.redis_client.delete(f"user_wishlist:{user_id}")
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
            redis_client.redis_client.delete(f"user_wishlist:{user_id}")
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
        # Apply rate limiting for cart access
        await rate_limiter.check_rate_limit(request)

        if current_user_or_guest.get('is_guest'):
            # Handle guest cart
            guest_id = current_user_or_guest['guest_id']
            cached_cart = get_cached_guest_cart(guest_id)
            if cached_cart:
                logger.info(f"Returning cached cart for guest {guest_id}")
                return CartResponse(**cached_cart)

            # Return empty cart for guest if not cached
            return CartResponse(items=[], subtotal=0.0, total_items=0)
        else:
            # Handle authenticated user cart
            user_id = current_user_or_guest['sub']
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
                items = []
                subtotal = 0
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
                cart_data = CartResponse(
                    items=items,
                    subtotal=subtotal,
                    total_items=total_items
                )
                cache_user_cart(user_id, cart_data.model_dump())
                return cart_data
    except Exception as e:
        logger.error(f"Failed to fetch cart: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch cart"
        )


@router.post("/cart/{product_id}")
async def add_to_cart(
        request: Request,
        product_id: int,
        quantity: int = 1,
        current_user_or_guest: dict = Depends(get_current_user_or_guest)
):
    try:
        # Apply rate limiting for cart operations
        await rate_limiter.check_rate_limit(request)

        if quantity < 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Quantity must be at least 1"
            )

        with db.get_cursor() as cursor:
            cursor.execute("""
                SELECT id, stock_quantity, stock_status, max_cart_quantity
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

            if current_user_or_guest.get('is_guest'):
                # Handle guest cart in Redis
                guest_id = current_user_or_guest['guest_id']
                guest_cart = get_cached_guest_cart(guest_id) or {"items": [], "subtotal": 0.0, "total_items": 0}

                # Check if product already in cart
                existing_item = None
                for item in guest_cart['items']:
                    if item['product_id'] == product_id and item.get('variation_id') is None:
                        existing_item = item
                        break

                if existing_item:
                    new_quantity = existing_item['quantity'] + quantity
                    if new_quantity > max_quantity:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Maximum {max_quantity} items can be added to cart"
                        )
                    existing_item['quantity'] = new_quantity
                    existing_item['total_price'] = float(product['base_price']) * new_quantity
                else:
                    guest_cart['items'].append({
                        'id': len(guest_cart['items']) + 1,  # Temporary ID for guest
                        'product_id': product_id,
                        'variation_id': None,
                        'product_name': product['name'],
                        'product_slug': f"product-{product_id}",
                        'product_image': None,
                        'product_price': float(product['base_price']),
                        'quantity': quantity,
                        'total_price': float(product['base_price']) * quantity,
                        'stock_quantity': product['stock_quantity'],
                        'stock_status': product['stock_status'],
                        'max_cart_quantity': product['max_cart_quantity']
                    })

                # Recalculate totals
                guest_cart['subtotal'] = sum(item['total_price'] for item in guest_cart['items'])
                guest_cart['total_items'] = sum(item['quantity'] for item in guest_cart['items'])

                cache_guest_cart(guest_id, guest_cart)
                logger.info(f"Product {product_id} added to guest cart {guest_id}")
                return {"message": "Product added to cart", "guest_id": guest_id}
            else:
                # Handle authenticated user cart in database
                user_id = current_user_or_guest['sub']
                cursor.execute("""
                    SELECT id, quantity FROM shopping_cart
                    WHERE user_id = %s AND product_id = %s AND variation_id IS NULL
                """, (user_id, product_id))
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
                        INSERT INTO shopping_cart (user_id, product_id, quantity)
                        VALUES (%s, %s, %s)
                    """, (user_id, product_id, quantity))
                redis_client.redis_client.delete(f"user_cart:{user_id}")
                logger.info(f"Product {product_id} added to cart for user {user_id}")
                return {"message": "Product added to cart"}
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
        # Apply rate limiting
        await rate_limiter.check_rate_limit(request)

        if quantity < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Quantity cannot be negative"
            )

        if current_user_or_guest.get('is_guest'):
            # Handle guest cart update
            guest_id = current_user_or_guest['guest_id']
            guest_cart = get_cached_guest_cart(guest_id)
            if not guest_cart:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Cart item not found"
                )

            # Find item in guest cart
            item_found = False
            for item in guest_cart['items']:
                if item['id'] == cart_item_id:
                    item_found = True
                    if quantity == 0:
                        guest_cart['items'].remove(item)
                    else:
                        # Validate quantity against stock
                        with db.get_cursor() as cursor:
                            cursor.execute("""
                                SELECT stock_quantity, max_cart_quantity, base_price
                                FROM products WHERE id = %s
                            """, (item['product_id'],))
                            product = cursor.fetchone()
                            if product and quantity > min(product['max_cart_quantity'], product['stock_quantity']):
                                raise HTTPException(
                                    status_code=status.HTTP_400_BAD_REQUEST,
                                    detail=f"Maximum {min(product['max_cart_quantity'], product['stock_quantity'])} items available"
                                )
                            item['quantity'] = quantity
                            item['total_price'] = float(product['base_price']) * quantity
                    break

            if not item_found:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Cart item not found"
                )

            # Recalculate totals
            guest_cart['subtotal'] = sum(item['total_price'] for item in guest_cart['items'])
            guest_cart['total_items'] = sum(item['quantity'] for item in guest_cart['items'])

            cache_guest_cart(guest_id, guest_cart)
            return {"message": "Cart updated successfully"}
        else:
            # Handle authenticated user cart update
            user_id = current_user_or_guest['sub']
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
                    redis_client.redis_client.delete(f"user_cart:{user_id}")
                    return {"message": "Item removed from cart"}
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
                redis_client.redis_client.delete(f"user_cart:{user_id}")
                return {"message": "Cart updated successfully"}
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
        # Apply rate limiting
        await rate_limiter.check_rate_limit(request)

        if current_user_or_guest.get('is_guest'):
            # Handle guest cart removal
            guest_id = current_user_or_guest['guest_id']
            guest_cart = get_cached_guest_cart(guest_id)
            if guest_cart:
                initial_count = len(guest_cart['items'])
                guest_cart['items'] = [item for item in guest_cart['items'] if item['id'] != cart_item_id]
                if len(guest_cart['items']) == initial_count:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Cart item not found"
                    )
                # Recalculate totals
                guest_cart['subtotal'] = sum(item['total_price'] for item in guest_cart['items'])
                guest_cart['total_items'] = sum(item['quantity'] for item in guest_cart['items'])
                cache_guest_cart(guest_id, guest_cart)
                return {"message": "Item removed from cart"}
            else:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Cart item not found"
                )
        else:
            # Handle authenticated user cart removal
            user_id = current_user_or_guest['sub']
            with db.get_cursor() as cursor:
                cursor.execute("DELETE FROM shopping_cart WHERE id = %s AND user_id = %s", (cart_item_id, user_id))
                if cursor.rowcount == 0:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Cart item not found"
                    )
                redis_client.redis_client.delete(f"user_cart:{user_id}")
                return {"message": "Item removed from cart"}
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
        # Apply rate limiting
        await rate_limiter.check_rate_limit(request)

        if current_user_or_guest.get('is_guest'):
            # Clear guest cart
            guest_id = current_user_or_guest['guest_id']
            cache_guest_cart(guest_id, {"items": [], "subtotal": 0.0, "total_items": 0})
            return {"message": "Cart cleared successfully"}
        else:
            # Clear authenticated user cart
            user_id = current_user_or_guest['sub']
            with db.get_cursor() as cursor:
                cursor.execute("DELETE FROM shopping_cart WHERE user_id = %s", (user_id,))
                redis_client.redis_client.delete(f"user_cart:{user_id}")
                return {"message": "Cart cleared successfully"}
    except Exception as e:
        logger.error(f"Failed to clear cart: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to clear cart"
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
        from shared import config, db, get_logger
        logger = get_logger(__name__)
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
            redis_status = "connected" if redis_client._ensure_connection() else "disconnected"
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