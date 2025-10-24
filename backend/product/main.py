import os
import sys
from fastapi import FastAPI, HTTPException, Query, Depends, Path, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from pydantic import BaseModel
from typing import List, Optional, Dict
import uvicorn
import logging
import mysql.connector
from mysql.connector import Error
import json

sys.path.append('/app')
from shared.utils.config import config
from shared.database.database import db
from shared.utils.logger import get_product_logger
from shared.security.role_checker import (
    allow_admin, allow_manage_products, allow_authenticated,
    RoleChecker
)
from shared.models.user_models import UserResponse

logger = get_product_logger()

app = FastAPI(
    title="Product Service - Pavitra Trading",
    description="Product Catalog and Management Service",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Allow vendors to manage their own products
allow_vendor_products = RoleChecker(allowed_roles=["super_admin", "admin", "vendor"])

class ProductCreate(BaseModel):
    name: str
    short_description: Optional[str] = None
    description: Optional[str] = None
    base_price: float
    category_id: int
    brand_id: Optional[int] = None
    stock_quantity: int = 0
    is_featured: bool = False

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    short_description: Optional[str] = None
    description: Optional[str] = None
    base_price: Optional[float] = None
    stock_quantity: Optional[int] = None
    is_featured: Optional[bool] = None
    status: Optional[str] = None

@app.get("/")
async def root():
    return {"message": "Product Service - Pavitra Trading", "environment": config.app_env}

@app.get("/health")
async def health():
    try:
        connection = db.get_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM products WHERE status = 'active'")
        product_count = cursor.fetchone()[0]
        cursor.close()
        connection.close()
        
        return {
            "status": "healthy",
            "service": "product",
            "environment": config.app_env,
            "active_products": product_count
        }
    except Error as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "service": "product",
            "environment": config.app_env
        }

# Public endpoints - no authentication required
@app.get("/products")
async def get_products(
    category: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    min_price: Optional[float] = Query(None),
    max_price: Optional[float] = Query(None),
    in_stock: Optional[bool] = Query(None),
    featured: Optional[bool] = Query(None),
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0),
    currency: str = Query("INR")
):
    connection = None
    try:
        connection = db.get_connection()
        cursor = connection.cursor(dictionary=True)
        
        query = """
            SELECT 
                p.id, 
                p.name, 
                CASE 
                    WHEN %s = 'INR' THEN p.base_price
                    WHEN p.international_pricing->>'$."%s"' IS NOT NULL 
                    THEN CAST(p.international_pricing->>'$."%s"' AS DECIMAL(12,2))
                    ELSE p.base_price * (
                        SELECT CASE %s 
                            WHEN 'USD' THEN 0.012 
                            WHEN 'EUR' THEN 0.011 
                            WHEN 'GBP' THEN 0.009 
                            WHEN 'AUD' THEN 0.018 
                            ELSE 1 
                        END
                    )
                END as price,
                %s as currency,
                c.name as category,
                p.stock_quantity,
                p.main_image_url as image_url,
                b.name as brand,
                p.short_description,
                p.is_featured,
                p.is_trending
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.id
            LEFT JOIN brands b ON p.brand_id = b.id
            WHERE p.status = 'active'
        """
        params = [currency, currency, currency, currency, currency]
        
        conditions = []
        if category:
            conditions.append("c.slug = %s")
            params.append(category)
        if search:
            conditions.append("(p.name LIKE %s OR p.short_description LIKE %s OR p.description LIKE %s)")
            params.extend([f"%{search}%", f"%{search}%", f"%{search}%"])
        if min_price is not None:
            conditions.append("p.base_price >= %s")
            params.append(min_price)
        if max_price is not None:
            conditions.append("p.base_price <= %s")
            params.append(max_price)
        if in_stock:
            conditions.append("p.stock_quantity > 0")
        if featured:
            conditions.append("p.is_featured = 1")
            
        if conditions:
            query += " AND " + " AND ".join(conditions)
            
        query += " ORDER BY p.is_featured DESC, p.created_at DESC LIMIT %s OFFSET %s"
        params.extend([limit, offset])
        
        cursor.execute(query, params)
        products = cursor.fetchall()
        
        logger.info(f"Products fetched: {len(products)} products")
        return products
    except Error as e:
        logger.error(f"Database error in get_products: {e}")
        raise HTTPException(status_code=500, detail="Database error")
    finally:
        if connection and connection.is_connected():
            connection.close()

# Admin-only endpoints
@app.post("/products", dependencies=[Depends(allow_manage_products)])
async def create_product(
    product: ProductCreate,
    payload: dict = Depends(allow_manage_products)
):
    connection = None
    try:
        connection = db.get_connection()
        cursor = connection.cursor(dictionary=True)
        
        cursor.execute("""
            INSERT INTO products (
                name, short_description, description, base_price, 
                category_id, brand_id, stock_quantity, is_featured, status
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'active')
        """, (
            product.name, product.short_description, product.description,
            product.base_price, product.category_id, product.brand_id,
            product.stock_quantity, product.is_featured
        ))
        
        product_id = cursor.lastrowid
        connection.commit()
        
        logger.info(f"Product created: {product_id} by user {payload.get('sub')}")
        return {"product_id": product_id, "message": "Product created successfully"}
    except Error as e:
        logger.error(f"Database error in create_product: {e}")
        raise HTTPException(status_code=500, detail="Database error")
    finally:
        if connection and connection.is_connected():
            connection.close()

@app.put("/products/{product_id}", dependencies=[Depends(allow_manage_products)])
async def update_product(
    product_id: int = Path(..., gt=0),
    product_update: ProductUpdate = Body(...),
    payload: dict = Depends(allow_manage_products)
):
    connection = None
    try:
        connection = db.get_connection()
        cursor = connection.cursor(dictionary=True)
        
        # Build dynamic update query
        update_fields = []
        params = []
        
        if product_update.name is not None:
            update_fields.append("name = %s")
            params.append(product_update.name)
        if product_update.short_description is not None:
            update_fields.append("short_description = %s")
            params.append(product_update.short_description)
        if product_update.description is not None:
            update_fields.append("description = %s")
            params.append(product_update.description)
        if product_update.base_price is not None:
            update_fields.append("base_price = %s")
            params.append(product_update.base_price)
        if product_update.stock_quantity is not None:
            update_fields.append("stock_quantity = %s")
            params.append(product_update.stock_quantity)
        if product_update.is_featured is not None:
            update_fields.append("is_featured = %s")
            params.append(product_update.is_featured)
        if product_update.status is not None:
            update_fields.append("status = %s")
            params.append(product_update.status)
        
        if not update_fields:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        params.append(product_id)
        query = f"UPDATE products SET {', '.join(update_fields)} WHERE id = %s"
        
        cursor.execute(query, params)
        connection.commit()
        
        logger.info(f"Product updated: {product_id} by user {payload.get('sub')}")
        return {"message": "Product updated successfully"}
    except Error as e:
        logger.error(f"Database error in update_product: {e}")
        raise HTTPException(status_code=500, detail="Database error")
    finally:
        if connection and connection.is_connected():
            connection.close()

@app.get("/admin/products", dependencies=[Depends(allow_manage_products)])
async def get_admin_products(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, le=100),
    status: Optional[str] = Query(None),
    payload: dict = Depends(allow_manage_products)
):
    connection = None
    try:
        connection = db.get_connection()
        cursor = connection.cursor(dictionary=True)
        
        query = """
            SELECT p.*, c.name as category_name, b.name as brand_name
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.id
            LEFT JOIN brands b ON p.brand_id = b.id
        """
        params = []
        
        if status:
            query += " WHERE p.status = %s"
            params.append(status)
        
        query += " ORDER BY p.created_at DESC LIMIT %s OFFSET %s"
        params.extend([limit, skip])
        
        cursor.execute(query, params)
        products = cursor.fetchall()
        
        logger.info(f"Admin products fetched: {len(products)} products by user {payload.get('sub')}")
        return products
    except Error as e:
        logger.error(f"Database error in get_admin_products: {e}")
        raise HTTPException(status_code=500, detail="Database error")
    finally:
        if connection and connection.is_connected():
            connection.close()

# Continue with other endpoints (categories, featured products, etc.)
@app.get("/categories")
async def get_categories():
    connection = None
    try:
        connection = db.get_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT c.id, c.name, c.slug, c.image_url,
                   COUNT(p.id) as product_count
            FROM categories c
            LEFT JOIN products p ON c.id = p.category_id AND p.status = 'active'
            WHERE c.is_active = 1
            GROUP BY c.id, c.name, c.slug, c.image_url
            ORDER BY c.sort_order, c.name
        """)
        categories = cursor.fetchall()
        
        logger.info(f"Categories fetched: {len(categories)} categories")
        return categories
    except Error as e:
        logger.error(f"Database error in get_categories: {e}")
        raise HTTPException(status_code=500, detail="Database error")
    finally:
        if connection and connection.is_connected():
            connection.close()

@app.get("/featured-products")
async def get_featured_products(limit: int = Query(10, le=20), currency: str = Query("INR")):
    connection = None
    try:
        connection = db.get_connection()
        cursor = connection.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT 
                p.id, p.name, 
                CASE 
                    WHEN %s = 'INR' THEN p.base_price
                    WHEN p.international_pricing->>'$."%s"' IS NOT NULL 
                    THEN CAST(p.international_pricing->>'$."%s"' AS DECIMAL(12,2))
                    ELSE p.base_price * 0.012
                END as price,
                %s as currency,
                p.main_image_url as image_url,
                p.short_description,
                c.name as category
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.id
            WHERE p.status = 'active' AND p.is_featured = 1
            ORDER BY p.created_at DESC
            LIMIT %s
        """, (currency, currency, currency, currency, limit))
        
        products = cursor.fetchall()
        
        logger.info(f"Featured products fetched: {len(products)} products")
        return products
    except Error as e:
        logger.error(f"Database error in get_featured_products: {e}")
        raise HTTPException(status_code=500, detail="Database error")
    finally:
        if connection and connection.is_connected():
            connection.close()

if __name__ == "__main__":
    import uvicorn
    port = config.get_service_port('PRODUCT')
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level=config.log_level.lower()
    )
