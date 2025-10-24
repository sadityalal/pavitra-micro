import os
import sys
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import mysql.connector
from mysql.connector import Error
import logging

# Add the backend directory to Python path for Docker
sys.path.append('/app')

from shared.utils.config import config
from shared.database.database import db
from shared.security.password_utils import PasswordSecurity
from shared.security.jwt_utils import JWTManager

logging.basicConfig(level=getattr(logging, config.log_level))
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Auth Service",
    debug=config.app_debug
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

jwt_manager = JWTManager(config.jwt_secret, config.jwt_algorithm)


@app.get("/")
async def root():
    return {"message": "Auth Service is running!", "environment": config.app_env}


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
            "database": "connected",
            "service": "auth",
            "environment": config.app_env,
            "users_count": user_count
        }
    except Error as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "service": "auth",
            "environment": config.app_env
        }


@app.post("/register")
async def register_user(email: str, password: str, first_name: str, last_name: str):
    connection = None
    try:
        # Validate password
        is_valid, message = PasswordSecurity.validate_password_strength(password)
        if not is_valid:
            raise HTTPException(status_code=400, detail=message)

        connection = db.get_connection()
        cursor = connection.cursor(dictionary=True)

        # Check if email exists
        cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="Email already exists")

        # Hash password and create user
        hashed_password = PasswordSecurity.hash_password(password)
        cursor.execute(
            "INSERT INTO users (email, password_hash, first_name, last_name) VALUES (%s, %s, %s, %s)",
            (email, hashed_password, first_name, last_name)
        )
        user_id = cursor.lastrowid
        connection.commit()

        # Generate token
        token_data = {"sub": str(user_id), "email": email}
        access_token = jwt_manager.create_access_token(token_data)

        return {
            "message": "User created successfully",
            "user_id": user_id,
            "email": email,
            "access_token": access_token,
            "token_type": "bearer"
        }

    except HTTPException:
        raise
    except Error as e:
        logger.error(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Database error")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
    finally:
        if connection and connection.is_connected():
            connection.close()


@app.post("/login")
async def login_user(email: str, password: str):
    connection = None
    try:
        connection = db.get_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            "SELECT id, email, password_hash FROM users WHERE email = %s",
            (email,)
        )
        user = cursor.fetchone()

        if not user:
            raise HTTPException(status_code=401, detail="Invalid credentials")

        if not PasswordSecurity.verify_password(password, user['password_hash']):
            raise HTTPException(status_code=401, detail="Invalid credentials")

        # Generate token
        token_data = {"sub": str(user['id']), "email": user['email']}
        access_token = jwt_manager.create_access_token(token_data)

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user_id": user['id'],
            "email": user['email']
        }
    except HTTPException:
        raise
    except Error as e:
        logger.error(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Database error")
    finally:
        if connection and connection.is_connected():
            connection.close()


@app.get("/users")
async def get_users():
    connection = None
    try:
        connection = db.get_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT id, email, first_name, last_name, created_at FROM users")
        users = cursor.fetchall()
        return {"users": users}
    except Error as e:
        logger.error(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Database error")
    finally:
        if connection and connection.is_connected():
            connection.close()


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv('PORT', config.get_service_port('AUTH')))
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level=config.log_level.lower(),
        workers=2
    )