from fastapi import APIRouter, HTTPException, Depends, Query, status, UploadFile, File, Request, BackgroundTasks
from typing import Optional, List
from shared import config, db, sanitize_input, get_logger, require_roles, redis_client, rabbitmq_client
from shared.auth_middleware import get_current_user
from shared.rate_limiter import rate_limiter
from shared.session_middleware import get_session, get_session_id
from shared.session_service import session_service, SessionType
from .models import (
    ProductResponse, ProductListResponse, CategoryResponse,
    BrandResponse, ProductSearch, HealthResponse, ProductCreate, ProductStatus, StockStatus, ProductType
)
from datetime import datetime
import ast
import os
import json
from urllib.parse import urlparse

router = APIRouter()
logger = get_logger(__name__)


def validate_product_for_cart(product_id: int, quantity: int, variation_id: Optional[int] = None) -> dict:
    try:
        with db.get_cursor() as cursor:
            query = """
                SELECT
                    p.id, p.name, p.sku, p.base_price, p.stock_quantity,
                    p.stock_status, p.max_cart_quantity, p.status,
                    p.track_inventory, p.low_stock_threshold
                FROM products p
                WHERE p.id = %s AND p.status = 'active'
            """
            cursor.execute(query, (product_id,))
            product = cursor.fetchone()
            if not product:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Product not found or not available"
                )
            config.refresh_cache()
            max_cart_quantity = getattr(config, 'max_cart_quantity_per_product', 20)

            # Use product-specific limit if available, otherwise use global setting
            product_max_quantity = product['max_cart_quantity']
            if product_max_quantity:
                max_quantity = min(product_max_quantity, max_cart_quantity)
            else:
                max_quantity = max_cart_quantity

            if product['status'] != 'active':
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Product is not available"
                )

            if product['stock_status'] == 'out_of_stock':
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Product is out of stock"
                )

            if product['track_inventory'] and product['stock_status'] != 'on_backorder':
                if quantity > product['stock_quantity'] and product['stock_status'] != 'on_backorder':
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Insufficient stock available"
                    )

            if quantity > max_quantity:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Maximum {max_quantity} items can be added to cart per order"
                )

            if variation_id:
                cursor.execute("""
                    SELECT stock_quantity, stock_status
                    FROM product_variations
                    WHERE id = %s AND product_id = %s
                """, (variation_id, product_id))
                variation = cursor.fetchone()
                if not variation:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Product variation not found"
                    )
                if variation['stock_status'] == 'out_of_stock':
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Product variation is out of stock"
                    )
                if quantity > variation['stock_quantity'] and variation['stock_status'] != 'on_backorder':
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Only {variation['stock_quantity']} items available for this variation"
                    )

            return {
                'id': product['id'],
                'name': product['name'],
                'price': float(product['base_price']),
                'stock_quantity': product['stock_quantity'],
                'stock_status': product['stock_status'],
                'max_cart_quantity': max_quantity,
                'track_inventory': bool(product['track_inventory'])
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Product validation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to validate product for cart"
        )


def get_product_cart_limits(product_id: int, variation_id: Optional[int] = None) -> dict:
    """
    Get cart limits and stock information for a product
    """
    try:
        with db.get_cursor() as cursor:
            query = """
                SELECT 
                    p.id, p.name, p.stock_quantity, p.stock_status, 
                    p.max_cart_quantity, p.track_inventory
                FROM products p
                WHERE p.id = %s AND p.status = 'active'
            """
            cursor.execute(query, (product_id,))
            product = cursor.fetchone()

            if not product:
                return {
                    'available': False,
                    'max_quantity': 0,
                    'stock_quantity': 0,
                    'stock_status': 'out_of_stock'
                }

            max_quantity = product['max_cart_quantity'] or 20

            # For variations, check variation stock
            variation_stock = None
            if variation_id:
                cursor.execute("""
                    SELECT stock_quantity, stock_status
                    FROM product_variations 
                    WHERE id = %s AND product_id = %s
                """, (variation_id, product_id))
                variation = cursor.fetchone()
                if variation:
                    variation_stock = {
                        'stock_quantity': variation['stock_quantity'],
                        'stock_status': variation['stock_status']
                    }

            return {
                'available': True,
                'max_quantity': max_quantity,
                'product_stock': {
                    'stock_quantity': product['stock_quantity'],
                    'stock_status': product['stock_status']
                },
                'variation_stock': variation_stock,
                'track_inventory': bool(product['track_inventory'])
            }

    except Exception as e:
        logger.error(f"Failed to get product cart limits: {e}")
        return {
            'available': False,
            'max_quantity': 0,
            'stock_quantity': 0,
            'stock_status': 'out_of_stock'
        }


@router.get("/{product_id}/cart-validation")
async def validate_product_cart_addition(
        product_id: int,
        quantity: int = Query(1, ge=1),
        variation_id: Optional[int] = Query(None),
        request: Request = None
):
    """
    Validate if a product can be added to cart with specified quantity
    """
    try:
        await rate_limiter.check_rate_limit(request)

        if quantity < 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Quantity must be at least 1"
            )

        # Validate the product
        product_data = validate_product_for_cart(product_id, quantity, variation_id)

        return {
            "valid": True,
            "product_id": product_id,
            "variation_id": variation_id,
            "quantity": quantity,
            "max_quantity": product_data['max_cart_quantity'],
            "price": product_data['price'],
            "stock_status": product_data['stock_status'],
            # REMOVED: "available_stock": product_data['stock_quantity']
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Cart validation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to validate product for cart"
        )


# Add this endpoint to get bulk product info for cart
@router.post("/bulk-cart-info")
async def get_bulk_cart_product_info(
        product_ids: List[int],
        request: Request = None
):
    """
    Get product information for multiple products (useful for cart display)
    """
    try:
        await rate_limiter.check_rate_limit(request)

        if not product_ids:
            return {"products": []}

        with db.get_cursor() as cursor:
            placeholders = ','.join(['%s'] * len(product_ids))
            query = f"""
                SELECT 
                    p.id, p.name, p.slug, p.main_image_url, p.base_price,
                    p.stock_quantity, p.stock_status, p.max_cart_quantity,
                    p.track_inventory, p.status
                FROM products p
                WHERE p.id IN ({placeholders}) AND p.status = 'active'
            """
            cursor.execute(query, product_ids)
            products = cursor.fetchall()

            product_map = {}
            for product in products:
                max_quantity = product['max_cart_quantity'] or 20
                product_map[product['id']] = {
                    'id': product['id'],
                    'name': product['name'],
                    'slug': product['slug'],
                    'image_url': product['main_image_url'],
                    'price': float(product['base_price']),
                    # REMOVED: 'stock_quantity': product['stock_quantity'],
                    'stock_status': product['stock_status'],
                    'max_cart_quantity': max_quantity,
                    'available': True,
                    'track_inventory': bool(product['track_inventory'])
                }

            # Include products that weren't found
            result_products = []
            for pid in product_ids:
                if pid in product_map:
                    result_products.append(product_map[pid])
                else:
                    result_products.append({
                        'id': pid,
                        'available': False,
                        'stock_status': 'out_of_stock'
                    })

            return {"products": result_products}

    except Exception as e:
        logger.error(f"Failed to get bulk cart info: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get product information"
        )


def invalidate_product_cache_comprehensive(product_id: int):
    """Comprehensive cache invalidation for product and related data"""
    try:
        keys_to_delete = [
            f"product:{product_id}",
            "categories:all",
            "products:featured",
            "products:bestsellers",
            "products:new_arrivals"
        ]

        # FIX: Use pipeline for atomic deletion
        pipeline = redis_client.redis_client.pipeline()
        for key in keys_to_delete:
            pipeline.delete(key)
        pipeline.execute()

        # FIX: Also delete pattern-based keys
        pattern_keys = redis_client.redis_client.keys("products:*")
        if pattern_keys:
            redis_client.redis_client.delete(*pattern_keys)

        logger.info(f"Comprehensively invalidated cache for product {product_id}")
    except Exception as e:
        logger.error(f"Failed to comprehensively invalidate product cache: {e}")


def get_cached_products_with_fallback(cache_key: str, fallback_func: callable, expire: int = 1800):
    """Get cached products with fallback function and proper error handling"""
    try:
        cached_data = redis_client.get(cache_key)
        if cached_data:
            return json.loads(cached_data)
    except Exception as e:
        logger.warning(f"Cache read failed for {cache_key}: {e}")

    # Fallback to database
    try:
        data = fallback_func()
        if data:
            redis_client.setex(cache_key, expire, json.dumps(data))
        return data
    except Exception as e:
        logger.error(f"Fallback function failed for {cache_key}: {e}")
        return None

def publish_product_event(product_data: dict, event_type: str):
    try:
        message = {
            'event_type': event_type,
            'product_id': product_data['id'],
            'product_name': product_data.get('name'),
            'timestamp': datetime.utcnow().isoformat(),
            'data': product_data
        }
        rabbitmq_client.publish_message(
            exchange='product_events',
            routing_key=f'product.{event_type}',
            message=message
        )
        logger.info(f"Product {event_type} event published for product {product_data['id']}")
    except Exception as e:
        logger.error(f"Failed to publish product event: {e}")


def cache_product(product_id: int, product_data: dict, expire: int = 1800):
    try:
        key = f"product:{product_id}"
        redis_client.setex(key, expire, json.dumps(product_data))
        logger.info(f"Cached product {product_id}")
    except Exception as e:
        logger.error(f"Failed to cache product: {e}")


def get_cached_product(product_id: int) -> Optional[dict]:
    try:
        key = f"product:{product_id}"
        data = redis_client.get(key)
        if data:
            return json.loads(data)
        return None
    except Exception as e:
        logger.error(f"Failed to get cached product: {e}")
        return None


def cache_categories(categories_data: List[dict], expire: int = 3600):
    try:
        key = "categories:all"
        redis_client.setex(key, expire, json.dumps(categories_data))
        logger.info("Cached categories")
    except Exception as e:
        logger.error(f"Failed to cache categories: {e}")


def get_cached_categories() -> Optional[List[dict]]:
    try:
        key = "categories:all"
        data = redis_client.get(key)
        if data:
            return json.loads(data)
        return None
    except Exception as e:
        logger.error(f"Failed to get cached categories: {e}")
        return None


def invalidate_product_cache(product_id: int):
    try:
        keys = [
            f"product:{product_id}",
            "categories:all"
        ]
        for key in keys:
            redis_client.delete(key)
        logger.info(f"Invalidated cache for product {product_id}")
    except Exception as e:
        logger.error(f"Failed to invalidate product cache: {e}")


def normalize_image_urls(image_data):
    if not image_data:
        return image_data
    if isinstance(image_data, str):
        if image_data.startswith(('http://', 'https://')):
            parsed = urlparse(image_data)
            return parsed.path
        return image_data
    elif isinstance(image_data, list):
        normalized = []
        for img_url in image_data:
            if img_url and img_url.startswith(('http://', 'https://')):
                parsed = urlparse(img_url)
                normalized.append(parsed.path)
            else:
                normalized.append(img_url)
        return normalized
    return image_data


def update_session_product_views(session, product_id: int, session_id: str):
    """Update session with product view history"""
    try:
        if not session or not session_id:
            return

        # Initialize viewed_products if not exists
        viewed_products = getattr(session, 'viewed_products', [])

        # Add product to viewed products (limit to 50 most recent)
        if product_id not in viewed_products:
            viewed_products.insert(0, product_id)
            viewed_products = viewed_products[:50]  # Keep only 50 most recent

        # Update session data
        session_service.update_session_data(session_id, {
            'viewed_products': viewed_products
        })

    except Exception as e:
        logger.error(f"Failed to update session product views: {e}")


def get_session_wishlist(session):
    """Get wishlist items from session"""
    try:
        if not session:
            return []
        return getattr(session, 'wishlist_items', [])
    except Exception as e:
        logger.error(f"Failed to get session wishlist: {e}")
        return []


def update_session_wishlist(session, session_id: str, product_id: int, action: str):
    """Update wishlist in session"""
    try:
        if not session or not session_id:
            return False

        # Get current wishlist items
        wishlist_items = getattr(session, 'wishlist_items', [])

        if action == 'add':
            if product_id not in wishlist_items:
                wishlist_items.append(product_id)
        elif action == 'remove':
            if product_id in wishlist_items:
                wishlist_items.remove(product_id)

        # Update session data
        return session_service.update_session_data(session_id, {
            'wishlist_items': wishlist_items
        })

    except Exception as e:
        logger.error(f"Failed to update session wishlist: {e}")
        return False


@router.get("/health", response_model=HealthResponse)
async def health():
    try:
        config.refresh_cache()
        if config.maintenance_mode:
            return HealthResponse(
                status="maintenance",
                service="product",
                products_count=0,
                categories_count=0,
                timestamp=datetime.utcnow()
            )
        with db.get_cursor() as cursor:
            cursor.execute("SELECT COUNT(*) as count FROM products WHERE status = 'active'")
            products_count = cursor.fetchone()['count']
            cursor.execute("SELECT COUNT(*) as count FROM categories WHERE is_active = 1")
            categories_count = cursor.fetchone()['count']
            return HealthResponse(
                status="healthy",
                service="product",
                products_count=products_count,
                categories_count=categories_count,
                timestamp=datetime.utcnow()
            )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthResponse(
            status="unhealthy",
            service="product",
            products_count=0,
            categories_count=0,
            timestamp=datetime.utcnow()
        )


@router.get("/site-settings")
async def get_site_settings(current_user: dict = Depends(get_current_user)):
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


@router.get("/", response_model=ProductListResponse)
async def get_products(
        request: Request,
        search: Optional[str] = Query(None),
        category_id: Optional[int] = Query(None),
        brand_id: Optional[int] = Query(None),
        category_slug: Optional[str] = Query(None),
        brand_slug: Optional[str] = Query(None),
        featured: Optional[bool] = Query(None),
        trending: Optional[bool] = Query(None),
        bestseller: Optional[bool] = Query(None),
        min_price: Optional[float] = Query(None),
        max_price: Optional[float] = Query(None),
        in_stock: Optional[bool] = Query(None),
        sort_by: str = Query("created_at"),
        sort_order: str = Query("desc"),
        page: int = Query(1, ge=1),
        page_size: int = Query(20, ge=1, le=100)
):
    try:
        await rate_limiter.check_rate_limit(request)
        config.refresh_cache()
        if config.maintenance_mode:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Service is under maintenance. Please try again later."
            )

        session_id = get_session_id(request)
        if session_id:
            session_service.update_session_activity(session_id)

        logger.info(f"🔍 Fetching products with filters - search: {search}, category_id: {category_id}, page: {page}")

        # FIX: Use parameterized queries to prevent SQL injection and improve performance
        query_conditions = ["p.status = 'active'"]
        query_params = []

        if search:
            # FIX: Use full-text search for better performance
            search_condition = """
                (MATCH(p.name, p.short_description, p.description) AGAINST (%s IN BOOLEAN MODE) 
                OR p.name LIKE %s OR p.short_description LIKE %s OR p.description LIKE %s)
            """
            query_conditions.append(search_condition)
            search_term = f"%{sanitize_input(search)}%"
            query_params.extend([search, search_term, search_term, search_term])

        if category_id:
            query_conditions.append("p.category_id = %s")
            query_params.append(category_id)

        if brand_id:
            query_conditions.append("p.brand_id = %s")
            query_params.append(brand_id)

        if category_slug:
            query_conditions.append("c.slug = %s")
            query_params.append(sanitize_input(category_slug))

        if brand_slug:
            query_conditions.append("b.slug = %s")
            query_params.append(sanitize_input(brand_slug))

        if min_price is not None:
            query_conditions.append("p.base_price >= %s")
            query_params.append(min_price)

        if max_price is not None:
            query_conditions.append("p.base_price <= %s")
            query_params.append(max_price)

        if in_stock:
            query_conditions.append("p.stock_status = 'in_stock'")

        if featured is not None:
            query_conditions.append("p.is_featured = %s")
            query_params.append(featured)

        if trending is not None:
            query_conditions.append("p.is_trending = %s")
            query_params.append(trending)

        if bestseller is not None:
            query_conditions.append("p.is_bestseller = %s")
            query_params.append(bestseller)

        where_clause = " AND ".join(query_conditions) if query_conditions else "1=1"

        # FIX: Validate and sanitize sort parameters to prevent SQL injection
        valid_sort_columns = ["name", "base_price", "created_at", "view_count", "total_sold", "wishlist_count"]
        valid_sort_orders = ["asc", "desc"]

        if sort_by not in valid_sort_columns:
            sort_by = "created_at"
        if sort_order not in valid_sort_orders:
            sort_order = "desc"

        # FIX: Use parameterized queries for all parts
        with db.get_cursor() as cursor:
            # FIX: Use COUNT(*) OVER() for more efficient pagination
            products_query = f"""
                SELECT
                    p.*,
                    c.name as category_name,
                    c.slug as category_slug,
                    b.name as brand_name,
                    b.slug as brand_slug,
                    COUNT(*) OVER() as total_count
                FROM products p
                LEFT JOIN categories c ON p.category_id = c.id
                LEFT JOIN brands b ON p.brand_id = b.id
                WHERE {where_clause}
                ORDER BY p.{sort_by} {sort_order.upper()}
                LIMIT %s OFFSET %s
            """

            offset = (page - 1) * page_size
            final_params = query_params + [page_size, offset]

            logger.info(f"📦 Products query executing with {len(final_params)} parameters")
            cursor.execute(products_query, final_params)
            products = cursor.fetchall()

            # FIX: Get total count from the first row if available
            total_count = 0
            if products:
                total_count = products[0].get('total_count', 0)
            else:
                # Fallback to count query if no products found
                count_query = f"""
                    SELECT COUNT(*) as total
                    FROM products p
                    LEFT JOIN categories c ON p.category_id = c.id
                    LEFT JOIN brands b ON p.brand_id = b.id
                    WHERE {where_clause}
                """
                cursor.execute(count_query, query_params)
                total_count = cursor.fetchone()['total']

            logger.info(f"📦 Products fetched: {len(products)}, total: {total_count}")

            product_list = []
            for product in products:
                specification = None
                image_gallery = None

                if product['specification']:
                    try:
                        if isinstance(product['specification'], str):
                            specification = ast.literal_eval(product['specification'])
                        else:
                            specification = product['specification']
                    except:
                        specification = None

                if product['image_gallery']:
                    try:
                        if isinstance(product['image_gallery'], str):
                            image_gallery = ast.literal_eval(product['image_gallery'])
                        else:
                            image_gallery = product['image_gallery']
                    except:
                        image_gallery = None

                main_image_url = normalize_image_urls(product['main_image_url'])
                image_gallery = normalize_image_urls(image_gallery)

                product_list.append(ProductResponse(
                    id=product['id'],
                    uuid=product['uuid'],
                    name=product['name'],
                    sku=product['sku'],
                    slug=product['slug'],
                    short_description=product['short_description'],
                    description=product['description'],
                    base_price=float(product['base_price']),
                    compare_price=float(product['compare_price']) if product['compare_price'] else None,
                    category_id=product['category_id'],
                    brand_id=product['brand_id'],
                    specification=specification,
                    gst_rate=float(product['gst_rate']),
                    is_gst_inclusive=bool(product['is_gst_inclusive']),
                    track_inventory=bool(product['track_inventory']),
                    stock_quantity=product['stock_quantity'],
                    low_stock_threshold=product['low_stock_threshold'],
                    stock_status=product['stock_status'],
                    product_type=product['product_type'],
                    weight_grams=float(product['weight_grams']) if product['weight_grams'] else None,
                    main_image_url=main_image_url,
                    image_gallery=image_gallery,
                    status=product['status'],
                    is_featured=bool(product['is_featured']),
                    is_trending=bool(product['is_trending']),
                    is_bestseller=bool(product['is_bestseller']),
                    view_count=product['view_count'],
                    wishlist_count=product['wishlist_count'],
                    total_sold=product['total_sold'],
                    created_at=product['created_at'],
                    updated_at=product['updated_at']
                ))

            total_pages = (total_count + page_size - 1) // page_size if page_size > 0 else 1
            logger.info(f"✅ Successfully returning {len(product_list)} products")

            return ProductListResponse(
                products=product_list,
                total_count=total_count,
                page=page,
                page_size=page_size,
                total_pages=total_pages
            )

    except Exception as e:
        logger.error(f"❌ Failed to fetch products: {str(e)}")
        logger.error(f"❌ Error type: {type(e).__name__}")
        import traceback
        logger.error(f"❌ Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch products"
        )


@router.get("/featured", response_model=ProductListResponse)
async def get_featured_products(
        request: Request,
        page: int = Query(1, ge=1),
        page_size: int = Query(20, ge=1, le=100)
):
    try:
        await rate_limiter.check_rate_limit(request)
        config.refresh_cache()
        if config.maintenance_mode:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Service is under maintenance. Please try again later."
            )

        # SESSION: Update session activity
        session_id = get_session_id(request)
        if session_id:
            session_service.update_session_activity(session_id)

        with db.get_cursor() as cursor:
            count_query = "SELECT COUNT(*) as total FROM products WHERE status = 'active' AND is_featured = 1"
            cursor.execute(count_query)
            total_count = cursor.fetchone()['total']
            offset = (page - 1) * page_size
            products_query = """
                SELECT
                    p.*,
                    c.name as category_name,
                    c.slug as category_slug,
                    b.name as brand_name,
                    b.slug as brand_slug
                FROM products p
                LEFT JOIN categories c ON p.category_id = c.id
                LEFT JOIN brands b ON p.brand_id = b.id
                WHERE p.status = 'active' AND p.is_featured = 1
                ORDER BY p.created_at DESC
                LIMIT %s OFFSET %s
            """
            cursor.execute(products_query, [page_size, offset])
            products = cursor.fetchall()
            product_list = []
            for product in products:
                specification = None
                image_gallery = None
                if product['specification']:
                    try:
                        if isinstance(product['specification'], str):
                            specification = ast.literal_eval(product['specification'])
                        else:
                            specification = product['specification']
                    except:
                        specification = None

                if product['image_gallery']:
                    try:
                        if isinstance(product['image_gallery'], str):
                            image_gallery = ast.literal_eval(product['image_gallery'])
                        else:
                            image_gallery = product['image_gallery']
                    except:
                        image_gallery = None

                main_image_url = normalize_image_urls(product['main_image_url'])
                image_gallery = normalize_image_urls(image_gallery)

                product_list.append(ProductResponse(
                    id=product['id'],
                    uuid=product['uuid'],
                    name=product['name'],
                    sku=product['sku'],
                    slug=product['slug'],
                    short_description=product['short_description'],
                    description=product['description'],
                    base_price=float(product['base_price']),
                    compare_price=float(product['compare_price']) if product['compare_price'] else None,
                    category_id=product['category_id'],
                    brand_id=product['brand_id'],
                    specification=specification,
                    gst_rate=float(product['gst_rate']),
                    is_gst_inclusive=bool(product['is_gst_inclusive']),
                    track_inventory=bool(product['track_inventory']),
                    stock_quantity=product['stock_quantity'],
                    low_stock_threshold=product['low_stock_threshold'],
                    stock_status=product['stock_status'],
                    product_type=product['product_type'],
                    weight_grams=float(product['weight_grams']) if product['weight_grams'] else None,
                    main_image_url=main_image_url,
                    image_gallery=image_gallery,
                    status=product['status'],
                    is_featured=bool(product['is_featured']),
                    is_trending=bool(product['is_trending']),
                    is_bestseller=bool(product['is_bestseller']),
                    view_count=product['view_count'],
                    wishlist_count=product['wishlist_count'],
                    total_sold=product['total_sold'],
                    created_at=product['created_at'],
                    updated_at=product['updated_at']
                ))

            total_pages = (total_count + page_size - 1) // page_size
            return ProductListResponse(
                products=product_list,
                total_count=total_count,
                page=page,
                page_size=page_size,
                total_pages=total_pages
            )
    except Exception as e:
        logger.error(f"Failed to fetch featured products: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch featured products"
        )


@router.get("/bestsellers", response_model=ProductListResponse)
async def get_bestseller_products(
        request: Request,
        page: int = Query(1, ge=1),
        page_size: int = Query(20, ge=1, le=100)
):
    try:
        await rate_limiter.check_rate_limit(request)
        config.refresh_cache()
        if config.maintenance_mode:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Service is under maintenance. Please try again later."
            )

        # SESSION: Update session activity
        session_id = get_session_id(request)
        if session_id:
            session_service.update_session_activity(session_id)

        with db.get_cursor() as cursor:
            count_query = "SELECT COUNT(*) as total FROM products WHERE status = 'active' AND is_bestseller = 1"
            cursor.execute(count_query)
            total_count = cursor.fetchone()['total']
            offset = (page - 1) * page_size
            products_query = """
                SELECT
                    p.*,
                    c.name as category_name,
                    c.slug as category_slug,
                    b.name as brand_name,
                    b.slug as brand_slug
                FROM products p
                LEFT JOIN categories c ON p.category_id = c.id
                LEFT JOIN brands b ON p.brand_id = b.id
                WHERE p.status = 'active' AND p.is_bestseller = 1
                ORDER BY p.total_sold DESC, p.created_at DESC
                LIMIT %s OFFSET %s
            """
            cursor.execute(products_query, [page_size, offset])
            products = cursor.fetchall()
            product_list = []
            for product in products:
                specification = None
                image_gallery = None
                if product['specification']:
                    try:
                        if isinstance(product['specification'], str):
                            specification = ast.literal_eval(product['specification'])
                        else:
                            specification = product['specification']
                    except:
                        specification = None

                if product['image_gallery']:
                    try:
                        if isinstance(product['image_gallery'], str):
                            image_gallery = ast.literal_eval(product['image_gallery'])
                        else:
                            image_gallery = product['image_gallery']
                    except:
                        image_gallery = None

                main_image_url = normalize_image_urls(product['main_image_url'])
                image_gallery = normalize_image_urls(image_gallery)

                product_list.append(ProductResponse(
                    id=product['id'],
                    uuid=product['uuid'],
                    name=product['name'],
                    sku=product['sku'],
                    slug=product['slug'],
                    short_description=product['short_description'],
                    description=product['description'],
                    base_price=float(product['base_price']),
                    compare_price=float(product['compare_price']) if product['compare_price'] else None,
                    category_id=product['category_id'],
                    brand_id=product['brand_id'],
                    specification=specification,
                    gst_rate=float(product['gst_rate']),
                    is_gst_inclusive=bool(product['is_gst_inclusive']),
                    track_inventory=bool(product['track_inventory']),
                    stock_quantity=product['stock_quantity'],
                    low_stock_threshold=product['low_stock_threshold'],
                    stock_status=product['stock_status'],
                    product_type=product['product_type'],
                    weight_grams=float(product['weight_grams']) if product['weight_grams'] else None,
                    main_image_url=main_image_url,
                    image_gallery=image_gallery,
                    status=product['status'],
                    is_featured=bool(product['is_featured']),
                    is_trending=bool(product['is_trending']),
                    is_bestseller=bool(product['is_bestseller']),
                    view_count=product['view_count'],
                    wishlist_count=product['wishlist_count'],
                    total_sold=product['total_sold'],
                    created_at=product['created_at'],
                    updated_at=product['updated_at']
                ))

            total_pages = (total_count + page_size - 1) // page_size
            return ProductListResponse(
                products=product_list,
                total_count=total_count,
                page=page,
                page_size=page_size,
                total_pages=total_pages
            )
    except Exception as e:
        logger.error(f"Failed to fetch bestseller products: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch bestseller products"
        )


@router.get("/new-arrivals", response_model=ProductListResponse)
async def get_new_arrivals(
        request: Request,
        page: int = Query(1, ge=1),
        page_size: int = Query(20, ge=1, le=100)
):
    try:
        await rate_limiter.check_rate_limit(request)
        config.refresh_cache()
        if config.maintenance_mode:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Service is under maintenance. Please try again later."
            )

        # SESSION: Update session activity
        session_id = get_session_id(request)
        if session_id:
            session_service.update_session_activity(session_id)

        with db.get_cursor() as cursor:
            count_query = "SELECT COUNT(*) as total FROM products WHERE status = 'active' AND created_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)"
            cursor.execute(count_query)
            total_count = cursor.fetchone()['total']
            offset = (page - 1) * page_size
            products_query = """
                SELECT
                    p.*,
                    c.name as category_name,
                    c.slug as category_slug,
                    b.name as brand_name,
                    b.slug as brand_slug
                FROM products p
                LEFT JOIN categories c ON p.category_id = c.id
                LEFT JOIN brands b ON p.brand_id = b.id
                WHERE p.status = 'active' AND p.created_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)
                ORDER BY p.created_at DESC
                LIMIT %s OFFSET %s
            """
            cursor.execute(products_query, [page_size, offset])
            products = cursor.fetchall()
            product_list = []
            for product in products:
                specification = None
                image_gallery = None
                if product['specification']:
                    try:
                        if isinstance(product['specification'], str):
                            specification = ast.literal_eval(product['specification'])
                        else:
                            specification = product['specification']
                    except:
                        specification = None

                if product['image_gallery']:
                    try:
                        if isinstance(product['image_gallery'], str):
                            image_gallery = ast.literal_eval(product['image_gallery'])
                        else:
                            image_gallery = product['image_gallery']
                    except:
                        image_gallery = None

                main_image_url = normalize_image_urls(product['main_image_url'])
                image_gallery = normalize_image_urls(image_gallery)

                product_list.append(ProductResponse(
                    id=product['id'],
                    uuid=product['uuid'],
                    name=product['name'],
                    sku=product['sku'],
                    slug=product['slug'],
                    short_description=product['short_description'],
                    description=product['description'],
                    base_price=float(product['base_price']),
                    compare_price=float(product['compare_price']) if product['compare_price'] else None,
                    category_id=product['category_id'],
                    brand_id=product['brand_id'],
                    specification=specification,
                    gst_rate=float(product['gst_rate']),
                    is_gst_inclusive=bool(product['is_gst_inclusive']),
                    track_inventory=bool(product['track_inventory']),
                    stock_quantity=product['stock_quantity'],
                    low_stock_threshold=product['low_stock_threshold'],
                    stock_status=product['stock_status'],
                    product_type=product['product_type'],
                    weight_grams=float(product['weight_grams']) if product['weight_grams'] else None,
                    main_image_url=main_image_url,
                    image_gallery=image_gallery,
                    status=product['status'],
                    is_featured=bool(product['is_featured']),
                    is_trending=bool(product['is_trending']),
                    is_bestseller=bool(product['is_bestseller']),
                    view_count=product['view_count'],
                    wishlist_count=product['wishlist_count'],
                    total_sold=product['total_sold'],
                    created_at=product['created_at'],
                    updated_at=product['updated_at']
                ))

            total_pages = (total_count + page_size - 1) // page_size
            return ProductListResponse(
                products=product_list,
                total_count=total_count,
                page=page,
                page_size=page_size,
                total_pages=total_pages
            )
    except Exception as e:
        logger.error(f"Failed to fetch new arrivals: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch new arrivals"
        )


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(product_id: int, request: Request):
    try:
        await rate_limiter.check_rate_limit(request)
        config.refresh_cache()
        if config.maintenance_mode:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Service is under maintenance. Please try again later."
            )

        session = get_session(request)
        session_id = get_session_id(request)
        if session_id:
            session_service.update_session_activity(session_id)
            update_session_product_views(session, product_id, session_id)

        cached_product = get_cached_product(product_id)
        if cached_product:
            logger.info(f"Returning cached product {product_id}")
            return ProductResponse(**cached_product)

        with db.get_cursor() as cursor:
            cursor.execute("""
                SELECT
                    p.*,
                    c.name as category_name,
                    c.slug as category_slug,
                    b.name as brand_name,
                    b.slug as brand_slug
                FROM products p
                LEFT JOIN categories c ON p.category_id = c.id
                LEFT JOIN brands b ON p.brand_id = b.id
                WHERE p.id = %s AND p.status = 'active'
            """, (product_id,))
            product = cursor.fetchone()
            if not product:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Product not found"
                )

            cursor.execute("""
                UPDATE products SET view_count = view_count + 1 WHERE id = %s
            """, (product_id,))

            specification = None
            image_gallery = None
            if product['specification']:
                try:
                    if isinstance(product['specification'], str):
                        specification = ast.literal_eval(product['specification'])
                    else:
                        specification = product['specification']
                except:
                    specification = None

            if product['image_gallery']:
                try:
                    if isinstance(product['image_gallery'], str):
                        image_gallery = ast.literal_eval(product['image_gallery'])
                    else:
                        image_gallery = product['image_gallery']
                except:
                    image_gallery = None

            main_image_url = normalize_image_urls(product['main_image_url'])
            image_gallery = normalize_image_urls(image_gallery)

            # Get max cart quantity with default fallback
            max_cart_quantity = product['max_cart_quantity'] or 20

            product_response = ProductResponse(
                id=product['id'],
                uuid=product['uuid'],
                name=product['name'],
                sku=product['sku'],
                slug=product['slug'],
                short_description=product['short_description'],
                description=product['description'],
                base_price=float(product['base_price']),
                compare_price=float(product['compare_price']) if product['compare_price'] else None,
                category_id=product['category_id'],
                brand_id=product['brand_id'],
                specification=specification,
                gst_rate=float(product['gst_rate']),
                is_gst_inclusive=bool(product['is_gst_inclusive']),
                track_inventory=bool(product['track_inventory']),
                stock_quantity=product['stock_quantity'],
                low_stock_threshold=product['low_stock_threshold'],
                stock_status=product['stock_status'],
                product_type=product['product_type'],
                weight_grams=float(product['weight_grams']) if product['weight_grams'] else None,
                main_image_url=main_image_url,
                image_gallery=image_gallery,
                status=product['status'],
                is_featured=bool(product['is_featured']),
                is_trending=bool(product['is_trending']),
                is_bestseller=bool(product['is_bestseller']),
                view_count=product['view_count'] + 1,
                wishlist_count=product['wishlist_count'],
                total_sold=product['total_sold'],
                created_at=product['created_at'],
                updated_at=product['updated_at']
            )

            cache_product(product_id, product_response.dict())
            return product_response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch product: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch product"
        )


@router.get("/stock-status/bulk")
async def get_bulk_stock_status(
        product_ids: List[int] = Query(...),
        request: Request = None
):
    """
    Get stock status for multiple products at once
    """
    try:
        await rate_limiter.check_rate_limit(request)

        if not product_ids or len(product_ids) > 50:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Maximum 50 products allowed per request"
            )

        with db.get_cursor() as cursor:
            placeholders = ','.join(['%s'] * len(product_ids))
            query = f"""
                SELECT 
                    id, name, stock_quantity, stock_status, 
                    max_cart_quantity, status
                FROM products 
                WHERE id IN ({placeholders})
            """
            cursor.execute(query, product_ids)
            products = cursor.fetchall()

            status_map = {}
            for product in products:
                max_quantity = product['max_cart_quantity'] or 20
                status_map[product['id']] = {
                    'product_id': product['id'],
                    'name': product['name'],
                    # REMOVED: 'stock_quantity': product['stock_quantity'],
                    'stock_status': product['stock_status'],
                    'max_cart_quantity': max_quantity,
                    'available': product['status'] == 'active'
                }

            # Include products that weren't found
            result = []
            for pid in product_ids:
                if pid in status_map:
                    result.append(status_map[pid])
                else:
                    result.append({
                        'product_id': pid,
                        'available': False,
                        'stock_status': 'out_of_stock',
                        'max_cart_quantity': 0
                    })

            return {"products": result}

    except Exception as e:
        logger.error(f"Failed to get bulk stock status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get stock status"
        )

@router.get("/slug/{product_slug}", response_model=ProductResponse)
async def get_product_by_slug(product_slug: str, request: Request):
    try:
        await rate_limiter.check_rate_limit(request)
        config.refresh_cache()
        if config.maintenance_mode:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Service is under maintenance. Please try again later."
            )

        # SESSION: Update session activity
        session = get_session(request)
        session_id = get_session_id(request)
        if session_id:
            session_service.update_session_activity(session_id)

        with db.get_cursor() as cursor:
            cursor.execute("""
                SELECT
                    p.*,
                    c.name as category_name,
                    c.slug as category_slug,
                    b.name as brand_name,
                    b.slug as brand_slug
                FROM products p
                LEFT JOIN categories c ON p.category_id = c.id
                LEFT JOIN brands b ON p.brand_id = b.id
                WHERE p.slug = %s AND p.status = 'active'
            """, (sanitize_input(product_slug),))
            product = cursor.fetchone()
            if not product:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Product not found"
                )

            cursor.execute("""
                UPDATE products SET view_count = view_count + 1 WHERE id = %s
            """, (product['id'],))

            # SESSION: Update product views
            if session_id:
                update_session_product_views(session, product['id'], session_id)

            specification = None
            image_gallery = None
            if product['specification']:
                try:
                    if isinstance(product['specification'], str):
                        specification = ast.literal_eval(product['specification'])
                    else:
                        specification = product['specification']
                except:
                    specification = None

            if product['image_gallery']:
                try:
                    if isinstance(product['image_gallery'], str):
                        image_gallery = ast.literal_eval(product['image_gallery'])
                    else:
                        image_gallery = product['image_gallery']
                except:
                    image_gallery = None

            main_image_url = normalize_image_urls(product['main_image_url'])
            image_gallery = normalize_image_urls(image_gallery)

            return ProductResponse(
                id=product['id'],
                uuid=product['uuid'],
                name=product['name'],
                sku=product['sku'],
                slug=product['slug'],
                short_description=product['short_description'],
                description=product['description'],
                base_price=float(product['base_price']),
                compare_price=float(product['compare_price']) if product['compare_price'] else None,
                category_id=product['category_id'],
                brand_id=product['brand_id'],
                specification=specification,
                gst_rate=float(product['gst_rate']),
                is_gst_inclusive=bool(product['is_gst_inclusive']),
                track_inventory=bool(product['track_inventory']),
                stock_quantity=product['stock_quantity'],
                low_stock_threshold=product['low_stock_threshold'],
                stock_status=product['stock_status'],
                product_type=product['product_type'],
                weight_grams=float(product['weight_grams']) if product['weight_grams'] else None,
                main_image_url=main_image_url,
                image_gallery=image_gallery,
                status=product['status'],
                is_featured=bool(product['is_featured']),
                is_trending=bool(product['is_trending']),
                is_bestseller=bool(product['is_bestseller']),
                view_count=product['view_count'] + 1,
                wishlist_count=product['wishlist_count'],
                total_sold=product['total_sold'],
                created_at=product['created_at'],
                updated_at=product['updated_at']
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch product by slug: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch product"
        )


@router.get("/categories/all", response_model=List[CategoryResponse])
async def get_categories(
        request: Request,
        parent_id: Optional[int] = Query(None),
        featured: Optional[bool] = Query(None)
):
    try:
        await rate_limiter.check_rate_limit(request)
        config.refresh_cache()
        if config.maintenance_mode:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Service is under maintenance. Please try again later."
            )

        # SESSION: Update session activity
        session_id = get_session_id(request)
        if session_id:
            session_service.update_session_activity(session_id)

        cached_categories = get_cached_categories()
        if cached_categories and parent_id is None and featured is None:
            logger.info("Returning cached categories")
            return [CategoryResponse(**cat) for cat in cached_categories]

        with db.get_cursor() as cursor:
            query_conditions = ["is_active = 1"]
            query_params = []

            if parent_id is not None:
                query_conditions.append("parent_id = %s")
                query_params.append(parent_id)
            else:
                query_conditions.append("parent_id IS NULL")

            if featured is not None:
                query_conditions.append("is_featured = %s")
                query_params.append(featured)

            where_clause = " AND ".join(query_conditions)
            cursor.execute(f"""
                SELECT * FROM categories
                WHERE {where_clause}
                ORDER BY sort_order, name
            """, query_params)
            categories = cursor.fetchall()
            category_list = [
                CategoryResponse(
                    id=cat['id'],
                    uuid=cat['uuid'],
                    name=cat['name'],
                    slug=cat['slug'],
                    description=cat['description'],
                    parent_id=cat['parent_id'],
                    image_url=normalize_image_urls(cat['image_url']),
                    is_active=bool(cat['is_active']),
                    sort_order=cat['sort_order']
                )
                for cat in categories
            ]
            if parent_id is None and featured is None:
                cache_categories([cat.dict() for cat in category_list])
            return category_list
    except Exception as e:
        logger.error(f"Failed to fetch categories: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch categories"
        )


@router.get("/categories/{category_id}", response_model=CategoryResponse)
async def get_category(category_id: int, request: Request):
    try:
        await rate_limiter.check_rate_limit(request)
        config.refresh_cache()
        if config.maintenance_mode:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Service is under maintenance. Please try again later."
            )

        # SESSION: Update session activity
        session_id = get_session_id(request)
        if session_id:
            session_service.update_session_activity(session_id)

        with db.get_cursor() as cursor:
            cursor.execute("""
                SELECT * FROM categories
                WHERE id = %s AND is_active = 1
            """, (category_id,))
            category = cursor.fetchone()
            if not category:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Category not found"
                )
            return CategoryResponse(
                id=category['id'],
                uuid=category['uuid'],
                name=category['name'],
                slug=category['slug'],
                description=category['description'],
                parent_id=category['parent_id'],
                image_url=normalize_image_urls(category['image_url']),
                is_active=bool(category['is_active']),
                sort_order=category['sort_order']
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch category: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch category"
        )


@router.get("/categories/slug/{category_slug}", response_model=CategoryResponse)
async def get_category_by_slug(category_slug: str, request: Request):
    try:
        await rate_limiter.check_rate_limit(request)
        config.refresh_cache()
        if config.maintenance_mode:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Service is under maintenance. Please try again later."
            )

        # SESSION: Update session activity
        session_id = get_session_id(request)
        if session_id:
            session_service.update_session_activity(session_id)

        with db.get_cursor() as cursor:
            cursor.execute("""
                SELECT * FROM categories
                WHERE slug = %s AND is_active = 1
            """, (sanitize_input(category_slug),))
            category = cursor.fetchone()
            if not category:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Category not found"
                )
            return CategoryResponse(
                id=category['id'],
                uuid=category['uuid'],
                name=category['name'],
                slug=category['slug'],
                description=category['description'],
                parent_id=category['parent_id'],
                image_url=normalize_image_urls(category['image_url']),
                is_active=bool(category['is_active']),
                sort_order=category['sort_order']
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch category by slug: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch category"
        )


@router.get("/brands/all", response_model=List[BrandResponse])
async def get_brands(request: Request, featured: Optional[bool] = Query(None)):
    try:
        await rate_limiter.check_rate_limit(request)
        config.refresh_cache()
        if config.maintenance_mode:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Service is under maintenance. Please try again later."
            )

        # SESSION: Update session activity
        session_id = get_session_id(request)
        if session_id:
            session_service.update_session_activity(session_id)

        with db.get_cursor() as cursor:
            query = "SELECT * FROM brands WHERE is_active = 1"
            params = []
            if featured is not None:
                query += " AND is_featured = %s"
                params.append(featured)
            query += " ORDER BY name"
            cursor.execute(query, params)
            brands = cursor.fetchall()
            return [
                BrandResponse(
                    id=brand['id'],
                    uuid=brand['uuid'],
                    name=brand['name'],
                    slug=brand['slug'],
                    description=brand['description'],
                    logo_url=normalize_image_urls(brand['logo_url']),
                    is_active=bool(brand['is_active'])
                )
                for brand in brands
            ]
    except Exception as e:
        logger.error(f"Failed to fetch brands: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch brands"
        )


@router.get("/brands/{brand_id}", response_model=BrandResponse)
async def get_brand(brand_id: int, request: Request):
    try:
        await rate_limiter.check_rate_limit(request)
        config.refresh_cache()
        if config.maintenance_mode:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Service is under maintenance. Please try again later."
            )

        # SESSION: Update session activity
        session_id = get_session_id(request)
        if session_id:
            session_service.update_session_activity(session_id)

        with db.get_cursor() as cursor:
            cursor.execute("""
                SELECT * FROM brands
                WHERE id = %s AND is_active = 1
            """, (brand_id,))
            brand = cursor.fetchone()
            if not brand:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Brand not found"
                )
            return BrandResponse(
                id=brand['id'],
                uuid=brand['uuid'],
                name=brand['name'],
                slug=brand['slug'],
                description=brand['description'],
                logo_url=normalize_image_urls(brand['logo_url']),
                is_active=bool(brand['is_active'])
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch brand: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch brand"
        )


# Wishlist endpoints with session support
@router.get("/wishlist")
async def get_wishlist(request: Request, current_user: dict = Depends(get_current_user)):
    """Get combined wishlist from session and database"""
    try:
        # SESSION: Update session activity
        session = get_session(request)
        session_id = get_session_id(request)
        if session_id:
            session_service.update_session_activity(session_id)

        user_id = current_user['sub']
        session_wishlist = get_session_wishlist(session) if session else []

        with db.get_cursor() as cursor:
            # Get database wishlist
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
            db_wishlist = cursor.fetchall()

            # Combine session and database wishlists (remove duplicates)
            db_product_ids = {item['product_id'] for item in db_wishlist}
            combined_product_ids = set(session_wishlist) | db_product_ids

            # Get combined product details
            if combined_product_ids:
                placeholders = ','.join(['%s'] * len(combined_product_ids))
                cursor.execute(f"""
                    SELECT
                        id, name, slug, main_image_url, base_price, stock_status
                    FROM products
                    WHERE id IN ({placeholders}) AND status = 'active'
                """, list(combined_product_ids))
                products = {p['id']: p for p in cursor.fetchall()}

                wishlist_items = []
                for product_id in combined_product_ids:
                    if product_id in products:
                        product = products[product_id]
                        wishlist_items.append({
                            'product_id': product_id,
                            'product_name': product['name'],
                            'product_slug': product['slug'],
                            'product_image': product['main_image_url'],
                            'product_price': float(product['base_price']),
                            'product_stock_status': product['stock_status'],
                            'in_session': product_id in session_wishlist,
                            'in_database': product_id in db_product_ids
                        })

                return {
                    "items": wishlist_items,
                    "total_count": len(wishlist_items),
                    "session_items_count": len(session_wishlist),
                    "database_items_count": len(db_wishlist)
                }
            else:
                return {
                    "items": [],
                    "total_count": 0,
                    "session_items_count": 0,
                    "database_items_count": 0
                }

    except Exception as e:
        logger.error(f"Failed to fetch wishlist: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch wishlist"
        )


@router.post("/wishlist/{product_id}")
async def add_to_wishlist(
        product_id: int,
        request: Request,
        current_user: dict = Depends(get_current_user)
):
    """Add product to wishlist (both session and database)"""
    try:
        user_id = current_user['sub']
        session = get_session(request)
        session_id = get_session_id(request)

        # SESSION: Update session activity
        if session_id:
            session_service.update_session_activity(session_id)

        with db.get_cursor() as cursor:
            # Verify product exists
            cursor.execute("SELECT id FROM products WHERE id = %s AND status = 'active'", (product_id,))
            if not cursor.fetchone():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Product not found"
                )

            # Add to database wishlist
            cursor.execute("""
                INSERT IGNORE INTO wishlists (user_id, product_id) 
                VALUES (%s, %s)
            """, (user_id, product_id))

            # Update product wishlist count
            cursor.execute("UPDATE products SET wishlist_count = wishlist_count + 1 WHERE id = %s", (product_id,))

            # SESSION: Also add to session wishlist
            if session and session_id:
                update_session_wishlist(session, session_id, product_id, 'add')

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
        request: Request,
        current_user: dict = Depends(get_current_user)
):
    """Remove product from wishlist (both session and database)"""
    try:
        user_id = current_user['sub']
        session = get_session(request)
        session_id = get_session_id(request)

        # SESSION: Update session activity
        if session_id:
            session_service.update_session_activity(session_id)

        with db.get_cursor() as cursor:
            # Remove from database wishlist
            cursor.execute("DELETE FROM wishlists WHERE user_id = %s AND product_id = %s", (user_id, product_id))

            if cursor.rowcount > 0:
                # Update product wishlist count
                cursor.execute("UPDATE products SET wishlist_count = GREATEST(0, wishlist_count - 1) WHERE id = %s",
                               (product_id,))

            # SESSION: Also remove from session wishlist
            if session and session_id:
                update_session_wishlist(session, session_id, product_id, 'remove')

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


@router.get("/session/recommendations")
async def get_personalized_recommendations(
        request: Request,
        limit: int = Query(10, ge=1, le=50)
):
    """Get personalized product recommendations based on session data"""
    try:
        session = get_session(request)
        session_id = get_session_id(request)

        # SESSION: Update session activity
        if session_id:
            session_service.update_session_activity(session_id)

        if not session:
            # Return featured products if no session data
            with db.get_cursor() as cursor:
                cursor.execute("""
                    SELECT * FROM products 
                    WHERE status = 'active' AND is_featured = 1
                    ORDER BY created_at DESC 
                    LIMIT %s
                """, (limit,))
                products = cursor.fetchall()
                return {"recommendations": products, "source": "featured"}

        # Get recommendations based on viewed products
        viewed_products = getattr(session, 'viewed_products', [])
        wishlist_items = getattr(session, 'wishlist_items', [])

        with db.get_cursor() as cursor:
            if viewed_products:
                # Recommend similar products based on viewed items
                placeholders = ','.join(['%s'] * len(viewed_products))
                cursor.execute(f"""
                    SELECT DISTINCT p.*
                    FROM products p
                    WHERE p.status = 'active' 
                    AND p.id NOT IN ({placeholders})
                    AND (p.category_id IN (
                        SELECT DISTINCT category_id FROM products WHERE id IN ({placeholders})
                    ) OR p.brand_id IN (
                        SELECT DISTINCT brand_id FROM products WHERE id IN ({placeholders})
                    ))
                    ORDER BY p.view_count DESC, p.created_at DESC
                    LIMIT %s
                """, viewed_products + viewed_products + viewed_products + [limit])
                recommendations = cursor.fetchall()
                return {"recommendations": recommendations, "source": "viewed_products"}
            else:
                # Fallback to trending products
                cursor.execute("""
                    SELECT * FROM products 
                    WHERE status = 'active' AND is_trending = 1
                    ORDER BY view_count DESC, created_at DESC 
                    LIMIT %s
                """, (limit,))
                recommendations = cursor.fetchall()
                return {"recommendations": recommendations, "source": "trending"}

    except Exception as e:
        logger.error(f"Failed to get recommendations: {e}")
        # Fallback to featured products
        with db.get_cursor() as cursor:
            cursor.execute("""
                SELECT * FROM products 
                WHERE status = 'active' AND is_featured = 1
                ORDER BY created_at DESC 
                LIMIT %s
            """, (limit,))
            products = cursor.fetchall()
            return {"recommendations": products, "source": "featured_fallback"}


# Admin endpoints (remain mostly unchanged, but with session activity updates)
@router.post("/admin/products", response_model=ProductResponse)
async def create_product(
        product_data: ProductCreate,
        request: Request,
        background_tasks: BackgroundTasks
):
    try:
        config.refresh_cache()
        if config.maintenance_mode:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Service is under maintenance. Please try again later."
            )

        session_id = get_session_id(request)
        if session_id:
            session_service.update_session_activity(session_id)

        current_user = await require_roles(['admin', 'vendor'], request)
        user_id = int(current_user.get('sub'))

        with db.get_cursor() as cursor:
            cursor.execute("SELECT id FROM products WHERE sku = %s", (product_data.sku,))
            if cursor.fetchone():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="SKU already exists"
                )

            cursor.execute("SELECT id FROM products WHERE slug = %s", (product_data.slug,))
            if cursor.fetchone():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Slug already exists"
                )

            cursor.execute("SELECT id FROM categories WHERE id = %s AND is_active = 1", (product_data.category_id,))
            if not cursor.fetchone():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Category not found"
                )

            if product_data.brand_id:
                cursor.execute("SELECT id FROM brands WHERE id = %s AND is_active = 1", (product_data.brand_id,))
                if not cursor.fetchone():
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Brand not found"
                    )

            # Set default max_cart_quantity if not provided
            max_cart_quantity = 20  # Default value

            cursor.execute("""
                INSERT INTO products (
                    sku, name, slug, short_description, description, specification,
                    base_price, compare_price, category_id, brand_id, gst_rate,
                    track_inventory, stock_quantity, product_type, is_featured,
                    status, stock_status, low_stock_threshold, max_cart_quantity
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                product_data.sku,
                sanitize_input(product_data.name),
                sanitize_input(product_data.slug),
                sanitize_input(product_data.short_description) if product_data.short_description else None,
                sanitize_input(product_data.description) if product_data.description else None,
                str(product_data.specification) if product_data.specification else None,
                product_data.base_price,
                product_data.compare_price,
                product_data.category_id,
                product_data.brand_id,
                product_data.gst_rate,
                product_data.track_inventory,
                product_data.stock_quantity,
                product_data.product_type.value,
                product_data.is_featured,
                'active',
                'in_stock' if product_data.stock_quantity > 0 else 'out_of_stock',
                5,
                max_cart_quantity  # Set default max cart quantity
            ))

            product_id = cursor.lastrowid
            cursor.execute("SELECT * FROM products WHERE id = %s", (product_id,))
            product = cursor.fetchone()

            specification = None
            if product['specification']:
                try:
                    if isinstance(product['specification'], str):
                        specification = ast.literal_eval(product['specification'])
                    else:
                        specification = product['specification']
                except:
                    specification = None

            main_image_url = normalize_image_urls(product['main_image_url'])
            image_gallery = normalize_image_urls(product['image_gallery'])

            product_response = ProductResponse(
                id=product['id'],
                uuid=product['uuid'],
                name=product['name'],
                sku=product['sku'],
                slug=product['slug'],
                short_description=product['short_description'],
                description=product['description'],
                base_price=float(product['base_price']),
                compare_price=float(product['compare_price']) if product['compare_price'] else None,
                category_id=product['category_id'],
                brand_id=product['brand_id'],
                specification=specification,
                gst_rate=float(product['gst_rate']),
                is_gst_inclusive=bool(product['is_gst_inclusive']),
                track_inventory=bool(product['track_inventory']),
                stock_quantity=product['stock_quantity'],
                low_stock_threshold=product['low_stock_threshold'],
                stock_status=product['stock_status'],
                product_type=product['product_type'],
                weight_grams=float(product['weight_grams']) if product['weight_grams'] else None,
                main_image_url=main_image_url,
                image_gallery=image_gallery,
                status=product['status'],
                is_featured=bool(product['is_featured']),
                is_trending=bool(product['is_trending']),
                is_bestseller=bool(product['is_bestseller']),
                view_count=product['view_count'],
                wishlist_count=product['wishlist_count'],
                total_sold=product['total_sold'],
                created_at=product['created_at'],
                updated_at=product['updated_at']
            )

            if background_tasks:
                background_tasks.add_task(
                    publish_product_event,
                    product,
                    'created'
                )

            logger.info(f"Product created successfully: {product_data.name}")
            return product_response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create product: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create product"
        )


@router.put("/admin/products/{product_id}", response_model=ProductResponse)
async def update_product(
        product_id: int,
        product_data: ProductCreate,
        request: Request,
        background_tasks: BackgroundTasks
):
    try:
        config.refresh_cache()
        if config.maintenance_mode:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Service is under maintenance. Please try again later."
            )

        session_id = get_session_id(request)
        if session_id:
            session_service.update_session_activity(session_id)

        current_user = await require_roles(['admin', 'vendor'], request)

        with db.get_cursor() as cursor:
            cursor.execute("SELECT id FROM products WHERE id = %s", (product_id,))
            if not cursor.fetchone():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Product not found"
                )

            cursor.execute("SELECT id FROM products WHERE sku = %s AND id != %s", (product_data.sku, product_id))
            if cursor.fetchone():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="SKU already exists"
                )

            # FIX: Also check slug uniqueness
            cursor.execute("SELECT id FROM products WHERE slug = %s AND id != %s", (product_data.slug, product_id))
            if cursor.fetchone():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Slug already exists"
                )

            cursor.execute("""
                UPDATE products SET
                    sku = %s, name = %s, slug = %s, short_description = %s,
                    description = %s, specification = %s, base_price = %s,
                    compare_price = %s, category_id = %s, brand_id = %s,
                    gst_rate = %s, track_inventory = %s, stock_quantity = %s,
                    product_type = %s, is_featured = %s, updated_at = NOW()
                WHERE id = %s
            """, (
                product_data.sku,
                sanitize_input(product_data.name),
                sanitize_input(product_data.slug),
                sanitize_input(product_data.short_description) if product_data.short_description else None,
                sanitize_input(product_data.description) if product_data.description else None,
                str(product_data.specification) if product_data.specification else None,
                product_data.base_price,
                product_data.compare_price,
                product_data.category_id,
                product_data.brand_id,
                product_data.gst_rate,
                product_data.track_inventory,
                product_data.stock_quantity,
                product_data.product_type.value,
                product_data.is_featured,
                product_id
            ))

            cursor.execute("SELECT * FROM products WHERE id = %s", (product_id,))
            product = cursor.fetchone()

            if background_tasks:
                background_tasks.add_task(
                    publish_product_event,
                    product,
                    'updated'
                )

            # FIX: Use comprehensive cache invalidation
            background_tasks.add_task(invalidate_product_cache_comprehensive, product_id)

            # Rest of the function remains the same...
            specification = None
            if product['specification']:
                try:
                    if isinstance(product['specification'], str):
                        specification = ast.literal_eval(product['specification'])
                    else:
                        specification = product['specification']
                except:
                    specification = None

            main_image_url = normalize_image_urls(product['main_image_url'])
            image_gallery = normalize_image_urls(product['image_gallery'])

            return ProductResponse(
                id=product['id'],
                uuid=product['uuid'],
                name=product['name'],
                sku=product['sku'],
                slug=product['slug'],
                short_description=product['short_description'],
                description=product['description'],
                base_price=float(product['base_price']),
                compare_price=float(product['compare_price']) if product['compare_price'] else None,
                category_id=product['category_id'],
                brand_id=product['brand_id'],
                specification=specification,
                gst_rate=float(product['gst_rate']),
                is_gst_inclusive=bool(product['is_gst_inclusive']),
                track_inventory=bool(product['track_inventory']),
                stock_quantity=product['stock_quantity'],
                low_stock_threshold=product['low_stock_threshold'],
                stock_status=product['stock_status'],
                product_type=product['product_type'],
                weight_grams=float(product['weight_grams']) if product['weight_grams'] else None,
                main_image_url=main_image_url,
                image_gallery=image_gallery,
                status=product['status'],
                is_featured=bool(product['is_featured']),
                is_trending=bool(product['is_trending']),
                is_bestseller=bool(product['is_bestseller']),
                view_count=product['view_count'],
                wishlist_count=product['wishlist_count'],
                total_sold=product['total_sold'],
                created_at=product['created_at'],
                updated_at=product['updated_at']
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update product: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update product"
        )


@router.post("/admin/products/{product_id}/images")
async def upload_product_images(
        request: Request,
        product_id: int,
        files: List[UploadFile] = File(...),
        background_tasks: BackgroundTasks = None
):
    await require_roles(['admin', 'vendor'], request)
    try:
        config.refresh_cache()
        if config.maintenance_mode:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Service is under maintenance. Please try again later."
            )

        session_id = get_session_id(request)
        if session_id:
            session_service.update_session_activity(session_id)

        with db.get_cursor() as cursor:
            cursor.execute("SELECT id, image_gallery FROM products WHERE id = %s", (product_id,))
            product = cursor.fetchone()
            if not product:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Product not found"
                )

            allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
            max_size = 5 * 1024 * 1024  # 5MB
            uploaded_urls = []
            existing_gallery = []

            if product['image_gallery']:
                try:
                    if isinstance(product['image_gallery'], str):
                        existing_gallery = ast.literal_eval(product['image_gallery'])
                    else:
                        existing_gallery = product['image_gallery']
                except:
                    existing_gallery = []

            for file in files:
                # FIX: Validate file type more securely
                if file.content_type not in allowed_types:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Invalid file type for {file.filename}. Only JPEG, PNG, GIF, and WebP are allowed."
                    )

                # FIX: Validate file extension
                file_extension = file.filename.split('.')[-1].lower()
                if file_extension not in ['jpg', 'jpeg', 'png', 'gif', 'webp']:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Invalid file extension for {file.filename}. Only .jpg, .jpeg, .png, .gif, .webp are allowed."
                    )

                file.file.seek(0, 2)
                file_size = file.file.tell()
                file.file.seek(0)

                if file_size > max_size:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"File {file.filename} too large. Maximum size is 5MB."
                    )

                # FIX: Sanitize filename to prevent path traversal
                safe_filename = "".join(c for c in file.filename if c.isalnum() or c in ('-', '_', '.')).rstrip()
                unique_filename = f"product_{product_id}_{int(datetime.now().timestamp())}_{len(uploaded_urls)}_{safe_filename}"

                # FIX: Ensure upload directory exists and is secure
                upload_dir = "/app/uploads/products"
                os.makedirs(upload_dir, exist_ok=True, mode=0o755)

                file_path = os.path.join(upload_dir, unique_filename)

                # FIX: Prevent path traversal
                if not file_path.startswith("/app/uploads/"):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Invalid file path"
                    )

                # Read and write file in chunks to prevent memory issues
                with open(file_path, "wb") as buffer:
                    while True:
                        chunk = await file.read(8192)  # 8KB chunks
                        if not chunk:
                            break
                        buffer.write(chunk)

                image_url = f"/uploads/products/{unique_filename}"
                uploaded_urls.append(image_url)

            updated_gallery = existing_gallery + uploaded_urls

            # FIX: Limit the number of images in gallery
            if len(updated_gallery) > 20:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Maximum 20 images allowed per product"
                )

            if not product['main_image_url'] and uploaded_urls:
                cursor.execute(
                    "UPDATE products SET main_image_url = %s WHERE id = %s",
                    (uploaded_urls[0], product_id)
                )

            cursor.execute(
                "UPDATE products SET image_gallery = %s WHERE id = %s",
                (str(updated_gallery), product_id)
            )

            if background_tasks:
                cursor.execute("SELECT * FROM products WHERE id = %s", (product_id,))
                updated_product = cursor.fetchone()
                background_tasks.add_task(
                    publish_product_event,
                    updated_product,
                    'images_updated'
                )

            invalidate_product_cache(product_id)

            return {
                "message": f"Successfully uploaded {len(uploaded_urls)} images",
                "uploaded_urls": uploaded_urls,
                "total_images": len(updated_gallery)
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to upload product images: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload product images"
        )


@router.delete("/admin/products/{product_id}")
async def delete_product(
        product_id: int,
        request: Request,
        background_tasks: BackgroundTasks = None
):
    try:
        config.refresh_cache()
        if config.maintenance_mode:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Service is under maintenance. Please try again later."
            )

        # SESSION: Update session activity
        session_id = get_session_id(request)
        if session_id:
            session_service.update_session_activity(session_id)

        current_user = await require_roles(['admin'], request)
        with db.get_cursor() as cursor:
            cursor.execute("SELECT id, name FROM products WHERE id = %s", (product_id,))
            product = cursor.fetchone()
            if not product:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Product not found"
                )
            cursor.execute("UPDATE products SET status = 'archived' WHERE id = %s", (product_id,))
            if background_tasks:
                background_tasks.add_task(
                    publish_product_event,
                    product,
                    'deleted'
                )
            invalidate_product_cache(product_id)
            logger.info(f"Product {product_id} archived by user {current_user.get('sub')}")
            return {"message": "Product archived successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete product: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete product"
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