from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import uvicorn
import logging
from shared.utils.config import config
from shared.database.database import db
import mysql.connector
from mysql.connector import Error

logging.basicConfig(level=getattr(logging, config.log_level))
logger = logging.getLogger(__name__)

app = FastAPI(
    title="User Service",
    debug=config.app_debug
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class UserProfile(BaseModel):
    first_name: str
    last_name: str
    email: str
    phone: Optional[str] = None


@app.get("/")
async def root():
    return {"message": "User Service is running!", "environment": config.app_env}


@app.get("/health")
async def health():
    try:
        connection = db.get_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        cursor.close()
        connection.close()

        return {
            "status": "healthy",
            "service": "user",
            "environment": config.app_env,
            "users_count": user_count
        }
    except Error as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "service": "user",
            "environment": config.app_env
        }


@app.get("/profile/{user_id}")
async def get_profile(user_id: int):
    connection = None
    try:
        connection = db.get_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute("""
            SELECT id, email, first_name, last_name, phone, created_at
            FROM users 
            WHERE id = %s
        """, (user_id,))

        user = cursor.fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        return user

    except Error as e:
        logger.error(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Database error")
    finally:
        if connection and connection.is_connected():
            connection.close()


@app.put("/profile/{user_id}")
async def update_profile(user_id: int, profile: UserProfile):
    connection = None
    try:
        connection = db.get_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute("""
            UPDATE users 
            SET first_name = %s, last_name = %s, email = %s, phone = %s
            WHERE id = %s
        """, (profile.first_name, profile.last_name, profile.email, profile.phone, user_id))

        connection.commit()
        logger.info(f"Updated profile for user {user_id}")

        return {"message": "Profile updated successfully"}

    except Error as e:
        logger.error(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Database error")
    finally:
        if connection and connection.is_connected():
            connection.close()


if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.getenv('PORT', config.get_service_port('USER')))
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level=config.log_level.lower(),
        workers=2
    )