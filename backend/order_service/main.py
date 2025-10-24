from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
import logging
from shared.utils.config import config
from shared.database.database import db
import mysql.connector
from mysql.connector import Error

logging.basicConfig(level=getattr(logging, config.log_level))
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Order Service",
    debug=config.app_debug
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class OrderItem(BaseModel):
    product_id: int
    quantity: int


class CreateOrder(BaseModel):
    items: List[OrderItem]
    shipping_address: str


@app.get("/")
async def root():
    return {"message": "Order Service is running!", "environment": config.app_env}


@app.get("/health")
async def health():
    try:
        connection = db.get_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM orders")
        order_count = cursor.fetchone()[0]
        cursor.close()
        connection.close()

        return {
            "status": "healthy",
            "service": "order",
            "environment": config.app_env,
            "orders_count": order_count
        }
    except Error as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "service": "order",
            "environment": config.app_env
        }


@app.post("/orders")
async def create_order(order: CreateOrder):
    connection = None
    try:
        connection = db.get_connection()
        cursor = connection.cursor(dictionary=True)

        # Create order in database
        cursor.execute("""
            INSERT INTO orders (order_number, user_id, subtotal, total_amount, shipping_address)
            VALUES (%s, %s, %s, %s, %s)
        """, (f"ORD-{int(__import__('time').time())}", 1, 99.99, 99.99, order.shipping_address))

        order_id = cursor.lastrowid
        connection.commit()

        logger.info(f"Created order {order_id} with {len(order.items)} items")
        return {
            "order_id": order_id,
            "status": "pending",
            "items": order.items,
            "environment": config.app_env
        }

    except Error as e:
        logger.error(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Database error")
    finally:
        if connection and connection.is_connected():
            connection.close()


@app.get("/orders")
async def get_orders():
    connection = None
    try:
        connection = db.get_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute("""
            SELECT id, order_number, status, total_amount, created_at
            FROM orders 
            ORDER BY created_at DESC 
            LIMIT 10
        """)

        orders = cursor.fetchall()
        return orders

    except Error as e:
        logger.error(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Database error")
    finally:
        if connection and connection.is_connected():
            connection.close()


if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.getenv('PORT', config.get_service_port('ORDER')))
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level=config.log_level.lower(),
        workers=2
    )