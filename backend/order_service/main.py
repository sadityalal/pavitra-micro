from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Order Service")

class OrderItem(BaseModel):
    product_id: int
    quantity: int

class CreateOrder(BaseModel):
    items: List[OrderItem]
    shipping_address: str

@app.get("/")
async def root():
    return {"message": "Order Service is running!"}

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "order"}

@app.post("/orders")
async def create_order(order: CreateOrder):
    logger.info(f"Creating order with {len(order.items)} items")
    return {
        "order_id": "order_123",
        "status": "pending",
        "items": order.items
    }

@app.get("/orders")
async def get_orders():
    return [{"id": 1, "status": "completed", "total": 99.99}]

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8003)
