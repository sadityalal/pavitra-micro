from fastapi import APIRouter, HTTPException, Depends, Query, status
from typing import Optional, List
from shared import config, db, sanitize_input, get_logger
from .models import (
    ProductResponse, ProductListResponse, CategoryResponse,
    BrandResponse, ProductSearch, HealthResponse
)
from datetime import datetime

router = APIRouter()
logger = get_logger(__name__)

@router.get("/health", response_model=HealthResponse)
async def health():
    try:
        with db.get_cursor() as cursor:
            # Get products count
            cursor.execute("SELECT COUNT(*) as count FROM products WHERE status = 'active'")
            products_count = cursor.fetchone()['count']
            
            # Get categories count
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

@router.get("/products", response_model=ProductListResponse)
async def get_products(
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
        query_conditions = ["p.status = 'active'"]
        query_params = []
        
        # Search query
        if search.query:
            query_conditions.append("(p.name LIKE %s OR p.short_description LIKE %s OR p.description LIKE %s)")
            search_term = f"%{sanitize_input(search.query)}%"
            query_params.extend([search_term, search_term, search_term])
        
        # Category filter
        if search.category_id:
            query_conditions.append("p.category_id = %s")
            query_params.append(search.category_id)
        
        # Brand filter
        if search.brand_id:
            query_conditions.append("p.brand_id = %s")
            query_params.append(search.brand_id)
        
        # Category slug filter
        if category_slug:
            query_conditions.append("c.slug = %s")
            query_params.append(sanitize_input(category_slug))
        
        # Brand slug filter
        if brand_slug:
            query_conditions.append("b.slug = %s")
            query_params.append(sanitize_input(brand_slug))
        
        # Price range filter
        if min_price is not None:
            query_conditions.append("p.base_price >= %s")
            query_params.append(min_price)
        
        if max_price is not None:
            query_conditions.append("p.base_price <= %s")
            query_params.append(max_price)
        
        # Stock status filter
        if in_stock:
            query_conditions.append("p.stock_status = 'in_stock'")
        
        # Featured products filter
        if featured is not None:
            query_conditions.append("p.is_featured = %s")
            query_params.append(featured)
        
        # Trending products filter
        if trending is not None:
            query_conditions.append("p.is_trending = %s")
            query_params.append(trending)
        
        # Bestseller products filter
        if bestseller is not None:
            query_conditions.append("p.is_bestseller = %s")
            query_params.append(bestseller)
        
        where_clause = " AND ".join(query_conditions)
        
        # Validate sort parameters
        valid_sort_columns = ["name", "base_price", "created_at", "view_count", "total_sold", "wishlist_count"]
        valid_sort_orders = ["asc", "desc"]
        
        if sort_by not in valid_sort_columns:
            sort_by = "created_at"
        if sort_order not in valid_sort_orders:
            sort_order = "desc"
        
        # Count query
        count_query = f"""
            SELECT COUNT(*) as total
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.id
            LEFT JOIN brands b ON p.brand_id = b.id
            WHERE {where_clause}
        """
        
        with db.get_cursor() as cursor:
            cursor.execute(count_query, query_params)
            total_count = cursor.fetchone()['total']
            
            # Products query with sorting
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
                # Parse JSON fields
                specification = None
                image_gallery = None
                
                if product['specification']:
                    try:
                        specification = eval(product['specification']) if product['specification'] else None
                    except:
                        specification = None
                
                if product['image_gallery']:
                    try:
                        image_gallery = eval(product['image_gallery']) if product['image_gallery'] else None
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

@router.get("/products/{product_id}", response_model=ProductResponse)
async def get_product(product_id: int):
    try:
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
            
            # Increment view count
            cursor.execute("""
                UPDATE products SET view_count = view_count + 1 WHERE id = %s
            """, (product_id,))
            
            # Parse JSON fields
            specification = None
            image_gallery = None
            
            if product['specification']:
                try:
                    specification = eval(product['specification']) if product['specification'] else None
                except:
                    specification = None
            
            if product['image_gallery']:
                try:
                    image_gallery = eval(product['image_gallery']) if product['image_gallery'] else None
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
                view_count=product['view_count'] + 1,  # Include the increment
                wishlist_count=product['wishlist_count'],
                total_sold=product['total_sold'],
                created_at=product['created_at'],
                updated_at=product['updated_at']
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch product: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch product"
        )

@router.get("/products/slug/{product_slug}", response_model=ProductResponse)
async def get_product_by_slug(product_slug: str):
    try:
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
            
            # Increment view count
            cursor.execute("""
                UPDATE products SET view_count = view_count + 1 WHERE id = %s
            """, (product['id'],))
            
            # Parse JSON fields
            specification = None
            image_gallery = None
            
            if product['specification']:
                try:
                    specification = eval(product['specification']) if product['specification'] else None
                except:
                    specification = None
            
            if product['image_gallery']:
                try:
                    image_gallery = eval(product['image_gallery']) if product['image_gallery'] else None
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

@router.get("/categories", response_model=List[CategoryResponse])
async def get_categories(
    parent_id: Optional[int] = Query(None),
    featured: Optional[bool] = Query(None)
):
    try:
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
            
            return [
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
            
    except Exception as e:
        logger.error(f"Failed to fetch categories: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch categories"
        )

@router.get("/categories/{category_id}", response_model=CategoryResponse)
async def get_category(category_id: int):
    try:
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

@router.get("/brands", response_model=List[BrandResponse])
async def get_brands(featured: Optional[bool] = Query(None)):
    try:
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

@router.get("/featured-products", response_model=ProductListResponse)
async def get_featured_products(
    page: int = Query(1, ge=1),
    page_size: int = Query(12, ge=1, le=50)
):
    """Get featured products"""
    search = ProductSearch(
        page=page,
        page_size=page_size
    )
    return await get_products(search=search, featured=True)

@router.get("/trending-products", response_model=ProductListResponse)
async def get_trending_products(
    page: int = Query(1, ge=1),
    page_size: int = Query(12, ge=1, le=50)
):
    """Get trending products"""
    search = ProductSearch(
        page=page,
        page_size=page_size
    )
    return await get_products(search=search, trending=True, sort_by="view_count", sort_order="desc")

@router.get("/bestseller-products", response_model=ProductListResponse)
async def get_bestseller_products(
    page: int = Query(1, ge=1),
    page_size: int = Query(12, ge=1, le=50)
):
    """Get bestseller products"""
    search = ProductSearch(
        page=page,
        page_size=page_size
    )
    return await get_products(search=search, bestseller=True, sort_by="total_sold", sort_order="desc")

@router.get("/new-arrivals", response_model=ProductListResponse)
async def get_new_arrivals(
    page: int = Query(1, ge=1),
    page_size: int = Query(12, ge=1, le=50)
):
    """Get newly added products"""
    search = ProductSearch(
        page=page,
        page_size=page_size
    )
    return await get_products(search=search, sort_by="created_at", sort_order="desc")
