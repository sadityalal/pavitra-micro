import os
import sys
sys.path.append('/app')
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from enum import Enum
import uvicorn
import logging
from shared.utils.config import config
from shared.database.database import db
import mysql.connector
from mysql.connector import Error

sys.path.append('/app')

logging.basicConfig(level=getattr(logging, config.log_level))
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Payment Service",
    debug=config.app_debug
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class PaymentMethod(str, Enum):
    UPI = "upi"
    CARD = "card"
    COD = "cash_on_delivery"


class PaymentRequest(BaseModel):
    order_id: str
    amount: float
    method: PaymentMethod
    upi_id: Optional[str] = None


@app.get("/")
async def root():
    return {"message": "Payment Service is running!", "environment": config.app_env}


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


@app.post("/pay")
async def process_payment(payment: PaymentRequest):
    connection = None
    try:
        connection = db.get_connection()
        cursor = connection.cursor(dictionary=True)

        # Create payment transaction
        cursor.execute("""
            INSERT INTO payment_transactions (order_id, amount, payment_method, status)
            VALUES (%s, %s, %s, %s)
        """, (payment.order_id, payment.amount, payment.method.value, 'completed'))

        transaction_id = cursor.lastrowid
        connection.commit()

        logger.info(f"Processed payment for order {payment.order_id}")
        return {
            "payment_id": f"pay_{transaction_id}",
            "status": "success",
            "transaction_id": f"txn_{transaction_id}",
            "environment": config.app_env
        }

    except Error as e:
        logger.error(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Database error")
    finally:
        if connection and connection.is_connected():
            connection.close()


if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.getenv('PORT', config.get_service_port('PAYMENT')))
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level=config.log_level.lower(),
        workers=2
    )