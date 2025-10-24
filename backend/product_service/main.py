from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
import uvicorn
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Product Service")

class Product(BaseModel):
    id: int
    name: str
    price: float
    category: str

@app.get("/")
async def root():
    return {"message": "Product Service is running!"}

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "product"}

@app.get("/products")
async def get_products():
    products = [
        {"id": 1, "name": "Test Product 1", "price": 99.99, "category": "electronics"},
        {"id": 2, "name": "Test Product 2", "price": 49.99, "category": "clothing"}
    ]
    logger.info(f"Returning {len(products)} products")
    return products

@app.get("/categories")
async def get_categories():
    return ["electronics", "clothing", "home", "books"]

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002)
