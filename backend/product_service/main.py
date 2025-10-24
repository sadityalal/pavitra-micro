import os
import sys
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
import logging
import mysql.connector
from mysql.connector import Error

# Add the backend directory to Python path for Docker
sys.path.append('/app')

from shared.utils.config import config
from shared.database.database import db

logging.basicConfig(level=getattr(logging, config.log_level))
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Product Service",
    debug=config.app_debug
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Product(BaseModel):
    id: int
    name: str
    price: float
    category: str
    stock_quantity: int
    image_url: Optional[str] = None


@app.get("/")
async def root():
    return {"message": "Product Service is running!", "environment": config.app_env}


@app.get("/health")
async def health():
    try:
        connection = db.get_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM products")
        product_count = cursor.fetchone()[0]
        cursor.close()
        connection.close()

        return {
            "status": "healthy",
            "service": "product",
            "environment": config.app_env,
            "products_count": product_count
        }
    except Error as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "service": "product",
            "environment": config.app_env
        }


@app.get("/products")
async def get_products(category: Optional[str] = None, limit: int = 50):
    connection = None
    try:
        connection = db.get_connection()
        cursor = connection.cursor(dictionary=True)

        if category:
            cursor.execute("""
                SELECT id, name, base_price as price, 
                       (SELECT name FROM categories WHERE id = category_id) as category,
                       stock_quantity, main_image_url as image_url
                FROM products 
                WHERE status = 'active' AND category_id IN (
                    SELECT id FROM categories WHERE name = %s
                )
                LIMIT %s
            """, (category, limit))
        else:
            cursor.execute("""
                SELECT id, name, base_price as price, 
                       (SELECT name FROM categories WHERE id = category_id) as category,
                       stock_quantity, main_image_url as image_url
                FROM products 
                WHERE status = 'active'
                LIMIT %s
            """, (limit,))

        products = cursor.fetchall()
        return products

    except Error as e:
        logger.error(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Database error")
    finally:
        if connection and connection.is_connected():
            connection.close()


@app.get("/products/{product_id}")
async def get_product(product_id: int):
    connection = None
    try:
        connection = db.get_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute("""
            SELECT p.id, p.name, p.base_price as price, p.short_description,
                   p.description, p.stock_quantity, p.main_image_url as image_url,
                   c.name as category, b.name as brand
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.id
            LEFT JOIN brands b ON p.brand_id = b.id
            WHERE p.id = %s AND p.status = 'active'
        """, (product_id,))

        product = cursor.fetchone()
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")

        return product

    except Error as e:
        logger.error(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Database error")
    finally:
        if connection and connection.is_connected():
            connection.close()


@app.get("/categories")
async def get_categories():
    connection = None
    try:
        connection = db.get_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute("""
            SELECT id, name, slug, image_url 
            FROM categories 
            WHERE is_active = 1
            ORDER BY sort_order, name
        """)

        categories = cursor.fetchall()
        return categories

    except Error as e:
        logger.error(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Database error")
    finally:
        if connection and connection.is_connected():
            connection.close()


if __name__ == "__main__":
    port = int(os.getenv('PORT', config.get_service_port('PRODUCT')))
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level=config.log_level.lower(),
        workers=2
    )