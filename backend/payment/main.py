import os
import sys
from fastapi import FastAPI, HTTPException, Depends, Body, Path, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from pydantic import BaseModel
from typing import Optional, List, Dict
import uvicorn
import logging
import mysql.connector
from mysql.connector import Error
from datetime import datetime
import uuid

sys.path.append('/app')
from shared.utils.config import config
from shared.database.database import db
from shared.utils.logger import get_payment_logger, AuditLogger
from shared.security.role_checker import (
    allow_admin, allow_authenticated, RoleChecker
)

logger = get_payment_logger()
audit_logger = AuditLogger()

app = FastAPI(
    title="Payment Service - Pavitra Trading",
    description="Payment Processing Service",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class PaymentRequest(BaseModel):
    order_id: str
    amount: float
    currency: str = "INR"
    payment_method: str
    upi_id: Optional[str] = None
    card_token: Optional[str] = None
    bank_code: Optional[str] = None

class PaymentResponse(BaseModel):
    payment_id: str
    status: str
    transaction_id: Optional[str] = None
    gateway_response: Optional[Dict] = None

@app.get("/")
async def root():
    return {"message": "Payment Service - Pavitra Trading", "environment": config.app_env}

@app.get("/health")
async def health():
    try:
        connection = db.get_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM payment_transactions")
        payment_count = cursor.fetchone()[0]
        cursor.close()
        connection.close()
        
        return {
            "status": "healthy",
            "service": "payment",
            "environment": config.app_env,
            "payments_count": payment_count
        }
    except Error as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "service": "payment",
            "environment": config.app_env
        }

@app.get("/payment-methods")
async def get_payment_methods(country_code: str = "IN"):
    connection = None
    try:
        connection = db.get_connection()
        cursor = connection.cursor(dictionary=True)
        
        # Get available payment gateways for the country
        cursor.execute("""
            SELECT gateway_name, gateway_code, supported_currencies
            FROM payment_gateways 
            WHERE is_active = 1 AND JSON_CONTAINS(supported_countries, %s)
        """, (f'"{country_code}"',))
        
        gateways = cursor.fetchall()
        
        # Get banks for netbanking
        cursor.execute("""
            SELECT bank_name, bank_code, logo_url
            FROM banks 
            WHERE is_active = 1
        """)
        
        banks = cursor.fetchall()
        
        payment_methods = {
            "gateways": gateways,
            "banks": banks,
            "methods": ["upi", "card", "netbanking", "wallet", "cash_on_delivery"]
        }
        
        return payment_methods
    except Error as e:
        logger.error(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Database error")
    finally:
        if connection and connection.is_connected():
            connection.close()

@app.post("/process-payment", response_model=PaymentResponse)
async def process_payment(
    payment_request: PaymentRequest,
    payload: dict = Depends(allow_authenticated)
):
    connection = None
    try:
        user_id = int(payload.get("sub"))
        connection = db.get_connection()
        cursor = connection.cursor(dictionary=True)
        
        # Generate payment ID
        payment_id = f"pay_{uuid.uuid4().hex[:16]}"
        transaction_id = f"txn_{uuid.uuid4().hex[:16]}"
        
        # Simulate payment processing
        # In production, integrate with actual payment gateways like Razorpay, Stripe
        payment_status = "completed"  # Simulate successful payment
        
        # Record payment transaction
        cursor.execute("""
            INSERT INTO payment_transactions (
                order_id, user_id, amount, currency, payment_method,
                gateway_name, gateway_transaction_id, status, payment_status
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            payment_request.order_id, user_id, payment_request.amount,
            payment_request.currency, payment_request.payment_method,
            "simulated_gateway", transaction_id, payment_status, "captured"
        ))
        
        # Update order payment status
        cursor.execute("""
            UPDATE orders 
            SET payment_status = 'paid', payment_method = %s,
                transaction_id = %s, paid_at = %s
            WHERE order_number = %s
        """, (
            payment_request.payment_method, transaction_id,
            datetime.utcnow(), payment_request.order_id
        ))
        
        connection.commit()
        
        logger.info(f"Payment processed: {payment_id} for order: {payment_request.order_id}")
        audit_logger.log_payment_event("PROCESSED", payment_request.order_id, payment_request.amount, payment_status)
        
        return PaymentResponse(
            payment_id=payment_id,
            status=payment_status,
            transaction_id=transaction_id,
            gateway_response={"simulated": True, "message": "Payment processed successfully"}
        )
    except Error as e:
        logger.error(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Database error")
    finally:
        if connection and connection.is_connected():
            connection.close()

@app.get("/payment-history")
async def get_payment_history(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, le=100),
    payload: dict = Depends(allow_authenticated)
):
    connection = None
    try:
        user_id = int(payload.get("sub"))
        connection = db.get_connection()
        cursor = connection.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT pt.*, o.order_number
            FROM payment_transactions pt
            JOIN orders o ON pt.order_id = o.id
            WHERE pt.user_id = %s
            ORDER BY pt.created_at DESC
            LIMIT %s OFFSET %s
        """, (user_id, limit, skip))
        
        payments = cursor.fetchall()
        
        logger.info(f"Payment history fetched for user: {user_id}")
        return payments
    except Error as e:
        logger.error(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Database error")
    finally:
        if connection and connection.is_connected():
            connection.close()

@app.get("/admin/payments", dependencies=[Depends(allow_admin)])
async def get_all_payments(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, le=100),
    status: Optional[str] = Query(None),
    payload: dict = Depends(allow_admin)
):
    connection = None
    try:
        connection = db.get_connection()
        cursor = connection.cursor(dictionary=True)
        
        query = """
            SELECT pt.*, u.email, u.first_name, u.last_name, o.order_number
            FROM payment_transactions pt
            JOIN users u ON pt.user_id = u.id
            JOIN orders o ON pt.order_id = o.id
        """
        params = []
        
        if status:
            query += " WHERE pt.status = %s"
            params.append(status)
        
        query += " ORDER BY pt.created_at DESC LIMIT %s OFFSET %s"
        params.extend([limit, skip])
        
        cursor.execute(query, params)
        payments = cursor.fetchall()
        
        logger.info(f"Admin payments fetched: {len(payments)} payments")
        return payments
    except Error as e:
        logger.error(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Database error")
    finally:
        if connection and connection.is_connected():
            connection.close()

@app.post("/refund/{payment_id}", dependencies=[Depends(allow_admin)])
async def process_refund(
    payment_id: str = Path(...),
    refund_amount: float = Body(..., embed=True),
    payload: dict = Depends(allow_admin)
):
    connection = None
    try:
        admin_id = payload.get("sub")
        connection = db.get_connection()
        cursor = connection.cursor(dictionary=True)
        
        # Update payment status to refunded
        cursor.execute("""
            UPDATE payment_transactions 
            SET status = 'refunded', refund_amount = %s, refunded_at = %s
            WHERE gateway_transaction_id = %s
        """, (refund_amount, datetime.utcnow(), payment_id))
        
        connection.commit()
        
        logger.info(f"Refund processed for payment: {payment_id} by admin: {admin_id}")
        audit_logger.log_payment_event("REFUNDED", payment_id, refund_amount, "refunded")
        
        return {"message": "Refund processed successfully"}
    except Error as e:
        logger.error(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Database error")
    finally:
        if connection and connection.is_connected():
            connection.close()

if __name__ == "__main__":
    import uvicorn
    port = config.get_service_port('PAYMENT')
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level=config.log_level.lower()
    )
