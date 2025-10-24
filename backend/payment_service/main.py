from fastapi import FastAPI
from pydantic import BaseModel
from enum import Enum
import uvicorn
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Payment Service")

class PaymentMethod(str, Enum):
    UPI = "upi"
    CARD = "card"
    COD = "cash_on_delivery"

class PaymentRequest(BaseModel):
    order_id: str
    amount: float
    method: PaymentMethod

@app.get("/")
async def root():
    return {"message": "Payment Service is running!"}

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "payment"}

@app.post("/pay")
async def process_payment(payment: PaymentRequest):
    logger.info(f"Processing payment for order {payment.order_id}")
    return {
        "payment_id": "pay_123",
        "status": "success",
        "transaction_id": "txn_123456"
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8005)
