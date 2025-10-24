import os
import sys
from fastapi import FastAPI, HTTPException, Depends, Body, Path, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from pydantic import BaseModel
from typing import List, Optional, Dict
import uvicorn
import logging
import mysql.connector
from mysql.connector import Error
from datetime import datetime

sys.path.append('/app')
from shared.utils.config import config
from shared.database.database import db
from shared.utils.logger import get_order_logger, AuditLogger
from shared.security.role_checker import (
    allow_admin, allow_manage_orders, allow_authenticated,
    RoleChecker
)

logger = get_order_logger()
audit_logger = AuditLogger()

app = FastAPI(
    title="Order Service - Pavitra Trading",
    description="Order Management Service",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Allow customers to manage their own orders
allow_customer_orders = RoleChecker(allowed_roles=["super_admin", "admin", "customer"])

class OrderItem(BaseModel):
    product_id: int
    quantity: int
    variation_id: Optional[int] = None

class CreateOrder(BaseModel):
    items: List[OrderItem]
    shipping_address: Dict
    payment_method: str

class OrderStatusUpdate(BaseModel):
    status: str
    admin_note: Optional[str] = None

@app.get("/")
async def root():
    return {"message": "Order Service - Pavitra Trading", "environment": config.app_env}

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

@app.post("/orders", dependencies=[Depends(allow_customer_orders)])
async def create_order(
    order: CreateOrder,
    payload: dict = Depends(allow_customer_orders)
):
    connection = None
    try:
        user_id = int(payload.get("sub"))
        connection = db.get_connection()
        cursor = connection.cursor(dictionary=True)
        
        # Calculate order total
        total_amount = 0
        for item in order.items:
            cursor.execute("SELECT base_price FROM products WHERE id = %s", (item.product_id,))
            product = cursor.fetchone()
            if not product:
                raise HTTPException(status_code=400, detail=f"Product {item.product_id} not found")
            total_amount += product['base_price'] * item.quantity
        
        # Create order
        order_number = f"ORD-{int(datetime.utcnow().timestamp())}"
        cursor.execute("""
            INSERT INTO orders (order_number, user_id, subtotal, total_amount, 
                              shipping_address, payment_method, status)
            VALUES (%s, %s, %s, %s, %s, %s, 'pending')
        """, (order_number, user_id, total_amount, total_amount, 
              json.dumps(order.shipping_address), order.payment_method))
        
        order_id = cursor.lastrowid
        
        # Add order items
        for item in order.items:
            cursor.execute("SELECT name, base_price FROM products WHERE id = %s", (item.product_id,))
            product = cursor.fetchone()
            
            cursor.execute("""
                INSERT INTO order_items (order_id, product_id, product_name, 
                                       unit_price, quantity, total_price)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (order_id, item.product_id, product['name'], 
                  product['base_price'], item.quantity, product['base_price'] * item.quantity))
        
        connection.commit()
        
        logger.info(f"Order created: {order_id} by user {user_id}")
        audit_logger.log_order_event("CREATED", order_number, str(user_id), f"Amount: {total_amount}")
        
        return {
            "order_id": order_id,
            "order_number": order_number,
            "status": "pending",
            "total_amount": total_amount
        }
    except Error as e:
        logger.error(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Database error")
    finally:
        if connection and connection.is_connected():
            connection.close()

@app.get("/orders", dependencies=[Depends(allow_customer_orders)])
async def get_user_orders(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, le=100),
    payload: dict = Depends(allow_customer_orders)
):
    connection = None
    try:
        user_id = int(payload.get("sub"))
        connection = db.get_connection()
        cursor = connection.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT id, order_number, status, total_amount, created_at
            FROM orders
            WHERE user_id = %s
            ORDER BY created_at DESC
            LIMIT %s OFFSET %s
        """, (user_id, limit, skip))
        
        orders = cursor.fetchall()
        
        logger.info(f"User orders fetched: {len(orders)} orders for user {user_id}")
        return orders
    except Error as e:
        logger.error(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Database error")
    finally:
        if connection and connection.is_connected():
            connection.close()

@app.get("/admin/orders", dependencies=[Depends(allow_manage_orders)])
async def get_all_orders(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, le=100),
    status: Optional[str] = Query(None),
    payload: dict = Depends(allow_manage_orders)
):
    connection = None
    try:
        connection = db.get_connection()
        cursor = connection.cursor(dictionary=True)
        
        query = """
            SELECT o.*, u.email, u.first_name, u.last_name
            FROM orders o
            JOIN users u ON o.user_id = u.id
        """
        params = []
        
        if status:
            query += " WHERE o.status = %s"
            params.append(status)
        
        query += " ORDER BY o.created_at DESC LIMIT %s OFFSET %s"
        params.extend([limit, skip])
        
        cursor.execute(query, params)
        orders = cursor.fetchall()
        
        logger.info(f"Admin orders fetched: {len(orders)} orders by user {payload.get('sub')}")
        return orders
    except Error as e:
        logger.error(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Database error")
    finally:
        if connection and connection.is_connected():
            connection.close()

@app.put("/admin/orders/{order_id}/status", dependencies=[Depends(allow_manage_orders)])
async def update_order_status(
    order_id: int = Path(..., gt=0),
    status_update: OrderStatusUpdate = Body(...),
    payload: dict = Depends(allow_manage_orders)
):
    connection = None
    try:
        admin_id = payload.get("sub")
        connection = db.get_connection()
        cursor = connection.cursor(dictionary=True)
        
        cursor.execute("""
            UPDATE orders 
            SET status = %s, admin_note = %s, updated_at = %s
            WHERE id = %s
        """, (status_update.status, status_update.admin_note, datetime.utcnow(), order_id))
        
        connection.commit()
        
        logger.info(f"Order status updated: {order_id} to {status_update.status} by admin {admin_id}")
        audit_logger.log_order_event("STATUS_UPDATED", str(order_id), admin_id, f"New status: {status_update.status}")
        
        return {"message": "Order status updated successfully"}
    except Error as e:
        logger.error(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Database error")
    finally:
        if connection and connection.is_connected():
            connection.close()

if __name__ == "__main__":
    import uvicorn
    port = config.get_service_port('ORDER')
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level=config.log_level.lower()
    )
