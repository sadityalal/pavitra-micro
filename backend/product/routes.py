from fastapi import APIRouter, HTTPException, Depends, Query, status, UploadFile, File, Request, BackgroundTasks
from typing import Optional, List
from shared import config, db, sanitize_input, get_logger, require_roles, redis_client, rabbitmq_client
from shared.auth_middleware import get_current_user
from .models import (
    ProductResponse, ProductListResponse, CategoryResponse,
    BrandResponse, ProductSearch, HealthResponse, ProductCreate, ProductStatus, StockStatus, ProductType
)
from datetime import datetime
import ast
import os
import json

router = APIRouter()
logger = get_logger(__name__)

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
        redis_client.redis_client.setex(key, expire, json.dumps(product_data))
        logger.info(f"Cached product {product_id}")
    except Exception as e:
        logger.error(f"Failed to cache product: {e}")

def get_cached_product(product_id: int) -> Optional[dict]:
    try:
        key = f"product:{product_id}"
        data = redis_client.redis_client.get(key)
        if data:
            return json.loads(data)
        return None
    except Exception as e:
        logger.error(f"Failed to get cached product: {e}")
        return None

def cache_categories(categories_data: List[dict], expire: int = 3600):
    try:
        key = "categories:all"
        redis_client.redis_client.setex(key, expire, json.dumps(categories_data))
        logger.info("Cached categories")
    except Exception as e:
        logger.error(f"Failed to cache categories: {e}")

def get_cached_categories() -> Optional[List[dict]]:
    try:
        key = "categories:all"
        data = redis_client.redis_client.get(key)
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
            redis_client.redis_client.delete(key)
        logger.info(f"Invalidated cache for product {product_id}")
    except Exception as e:
        logger.error(f"Failed to invalidate product cache: {e}")

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
async def get_site_settings():
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
            'free_shipping_threshold': getattr(config, 'free_shipping_threshold', 999),
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

@router.get("/", response_model=ProductListResponse)
async def get_products(
    request: Request,
    search: ProductSearch = Depends(),
    category_slug: Optional[str] = Query(None),
    brand_slug: Optional[str] = Query(None),
    featured: Optional[bool] = Query(None),
    trending: Optional[bool] = Query(None),
    bestseller: Optional[bool] = Query(None),
    min_price: Optional[float] = Query(None),
    max_price: Optional[float] = Query(None),
    in_stock: Optional[bool] = Query(None),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc")
):
    try:
        config.refresh_cache()
        if config.maintenance_mode:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Service is under maintenance. Please try again later."
            )

        query_conditions = ["p.status = 'active'"]
        query_params = []
        
        if search.query:
            query_conditions.append("(p.name LIKE %s OR p.short_description LIKE %s OR p.description LIKE %s)")
            search_term = f"%{sanitize_input(search.query)}%"
            query_params.extend([search_term, search_term, search_term])
        
        if search.category_id:
            query_conditions.append("p.category_id = %s")
            query_params.append(search.category_id)
        
        if search.brand_id:
            query_conditions.append("p.brand_id = %s")
            query_params.append(search.brand_id)
        
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

        where_clause = " AND ".join(query_conditions)
        
        valid_sort_columns = ["name", "base_price", "created_at", "view_count", "total_sold", "wishlist_count"]
        valid_sort_orders = ["asc", "desc"]
        
        if sort_by not in valid_sort_columns:
            sort_by = "created_at"
        if sort_order not in valid_sort_orders:
            sort_order = "desc"

        with db.get_cursor() as cursor:
            count_query = f"""
                SELECT COUNT(*) as total
                FROM products p
                LEFT JOIN categories c ON p.category_id = c.id
                LEFT JOIN brands b ON p.brand_id = b.id
                WHERE {where_clause}
            """
            cursor.execute(count_query, query_params)
            total_count = cursor.fetchone()['total']

            products_query = f"""
                SELECT
                    p.*,
                    c.name as category_name,
                    c.slug as category_slug,
                    b.name as brand_name,
                    b.slug as brand_slug
                FROM products p
                LEFT JOIN categories c ON p.category_id = c.id
                LEFT JOIN brands b ON p.brand_id = b.id
                WHERE {where_clause}
                ORDER BY p.{sort_by} {sort_order.upper()}
                LIMIT %s OFFSET %s
            """
            offset = (search.page - 1) * search.page_size
            cursor.execute(products_query, query_params + [search.page_size, offset])
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
                    main_image_url=product['main_image_url'],
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

            total_pages = (total_count + search.page_size - 1) // search.page_size
            
            return ProductListResponse(
                products=product_list,
                total_count=total_count,
                page=search.page,
                page_size=search.page_size,
                total_pages=total_pages
            )
    except Exception as e:
        logger.error(f"Failed to fetch products: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch products"
        )

@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(product_id: int):
    try:
        config.refresh_cache()
        if config.maintenance_mode:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Service is under maintenance. Please try again later."
            )

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
                main_image_url=product['main_image_url'],
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

            cache_product(product_id, product_response.model_dump())
            return product_response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch product: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch product"
        )

@router.get("/slug/{product_slug}", response_model=ProductResponse)
async def get_product_by_slug(product_slug: str):
    try:
        config.refresh_cache()
        if config.maintenance_mode:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Service is under maintenance. Please try again later."
            )

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
                main_image_url=product['main_image_url'],
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
    parent_id: Optional[int] = Query(None),
    featured: Optional[bool] = Query(None)
):
    try:
        config.refresh_cache()
        if config.maintenance_mode:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Service is under maintenance. Please try again later."
            )

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
                    image_url=cat['image_url'],
                    is_active=bool(cat['is_active']),
                    sort_order=cat['sort_order']
                )
                for cat in categories
            ]

            if parent_id is None and featured is None:
                cache_categories([cat.model_dump() for cat in category_list])
            
            return category_list
    except Exception as e:
        logger.error(f"Failed to fetch categories: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch categories"
        )

@router.get("/categories/{category_id}", response_model=CategoryResponse)
async def get_category(category_id: int):
    try:
        config.refresh_cache()
        if config.maintenance_mode:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Service is under maintenance. Please try again later."
            )

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
                image_url=category['image_url'],
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
async def get_category_by_slug(category_slug: str):
    try:
        config.refresh_cache()
        if config.maintenance_mode:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Service is under maintenance. Please try again later."
            )

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
                image_url=category['image_url'],
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
async def get_brands(featured: Optional[bool] = Query(None)):
    try:
        config.refresh_cache()
        if config.maintenance_mode:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Service is under maintenance. Please try again later."
            )

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
                    logo_url=brand['logo_url'],
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
async def get_brand(brand_id: int):
    try:
        config.refresh_cache()
        if config.maintenance_mode:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Service is under maintenance. Please try again later."
            )

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
                logo_url=brand['logo_url'],
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


# @router.get("/featured/products", response_model=ProductListResponse)
# async def get_featured_products(
#         request: Request,
#         page: int = Query(1, ge=1),
#         page_size: int = Query(12, ge=1, le=50)
# ):
#     # Create search object manually
#     class ManualSearch:
#         def __init__(self, page, page_size):
#             self.page = page
#             self.page_size = page_size
#             self.query = None
#             self.category_id = None
#             self.brand_id = None
#
#     search = ManualSearch(page=page, page_size=page_size)
#     return await get_products(request, search, featured=True)
#
#
# @router.get("/trending/products", response_model=ProductListResponse)
# async def get_trending_products(
#         request: Request,
#         page: int = Query(1, ge=1),
#         page_size: int = Query(12, ge=1, le=50)
# ):
#     class ManualSearch:
#         def __init__(self, page, page_size):
#             self.page = page
#             self.page_size = page_size
#             self.query = None
#             self.category_id = None
#             self.brand_id = None
#
#     search = ManualSearch(page=page, page_size=page_size)
#     return await get_products(request, search, trending=True, sort_by="view_count", sort_order="desc")
#
#
# @router.get("/bestseller/products", response_model=ProductListResponse)
# async def get_bestseller_products(
#         request: Request,
#         page: int = Query(1, ge=1),
#         page_size: int = Query(12, ge=1, le=50)
# ):
#     class ManualSearch:
#         def __init__(self, page, page_size):
#             self.page = page
#             self.page_size = page_size
#             self.query = None
#             self.category_id = None
#             self.brand_id = None
#
#     search = ManualSearch(page=page, page_size=page_size)
#     return await get_products(request, search, bestseller=True, sort_by="total_sold", sort_order="desc")
#
#
# @router.get("/new-arrivals/products", response_model=ProductListResponse)
# async def get_new_arrivals(
#         request: Request,
#         page: int = Query(1, ge=1),
#         page_size: int = Query(12, ge=1, le=50)
# ):
#     class ManualSearch:
#         def __init__(self, page, page_size):
#             self.page = page
#             self.page_size = page_size
#             self.query = None
#             self.category_id = None
#             self.brand_id = None
#
#     search = ManualSearch(page=page, page_size=page_size)
#     return await get_products(request, search, sort_by="created_at", sort_order="desc")

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

            cursor.execute("""
                INSERT INTO products (
                    sku, name, slug, short_description, description, specification,
                    base_price, compare_price, category_id, brand_id, gst_rate,
                    track_inventory, stock_quantity, product_type, is_featured,
                    status, stock_status, low_stock_threshold
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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
                5
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
                main_image_url=product['main_image_url'],
                image_gallery=None,
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

            invalidate_product_cache(product_id)
            
            specification = None
            if product['specification']:
                try:
                    if isinstance(product['specification'], str):
                        specification = ast.literal_eval(product['specification'])
                    else:
                        specification = product['specification']
                except:
                    specification = None

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
                main_image_url=product['main_image_url'],
                image_gallery=None,
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

        with db.get_cursor() as cursor:
            cursor.execute("SELECT id, image_gallery FROM products WHERE id = %s", (product_id,))
            product = cursor.fetchone()
            
            if not product:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Product not found"
                )

            allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
            max_size = 5 * 1024 * 1024
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
                if file.content_type not in allowed_types:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Invalid file type for {file.filename}. Only JPEG, PNG, GIF, and WebP are allowed."
                    )

                file.file.seek(0, 2)
                file_size = file.file.tell()
                file.file.seek(0)
                
                if file_size > max_size:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"File {file.filename} too large. Maximum size is 5MB."
                    )

                file_extension = file.filename.split('.')[-1]
                unique_filename = f"product_{product_id}_{int(datetime.now().timestamp())}_{len(uploaded_urls)}.{file_extension}"
                file_path = f"/app/uploads/products/{unique_filename}"
                
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                
                with open(file_path, "wb") as buffer:
                    content = await file.read()
                    buffer.write(content)

                image_url = f"/uploads/products/{unique_filename}"
                uploaded_urls.append(image_url)

            updated_gallery = existing_gallery + uploaded_urls
            
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
