from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional
import uvicorn
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="User Service")

class UserProfile(BaseModel):
    first_name: str
    last_name: str
    email: str

@app.get("/")
async def root():
    return {"message": "User Service is running!"}

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "user"}

@app.get("/profile")
async def get_profile():
    return {
        "user_id": "user_123",
        "first_name": "John",
        "last_name": "Doe",
        "email": "john@example.com"
    }

@app.put("/profile")
async def update_profile(profile: UserProfile):
    logger.info(f"Updating profile for user")
    return {"message": "Profile updated successfully"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8004)
