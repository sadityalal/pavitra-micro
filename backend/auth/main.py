import os
import sys
import re
from fastapi import FastAPI, HTTPException, Depends, Form, Path, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import mysql.connector
from mysql.connector import Error
import logging
from datetime import datetime
from typing import Optional, List

sys.path.append('/app')
from shared.utils.config import config
from shared.database.database import db
from shared.security.password_utils import PasswordSecurity
from shared.security.jwt_utils import JWTManager
from shared.security.rate_limiter import RateLimiter
from shared.security.role_checker import (
    allow_super_admin, allow_admin, allow_manage_users, 
    allow_authenticated, RoleChecker
)
from shared.utils.logger import get_auth_logger, AuditLogger
from shared.models.user_models import UserResponse, Token, RoleResponse, PermissionCheck

logger = get_auth_logger()
audit_logger = AuditLogger()

app = FastAPI(
    title="Auth Service - Pavitra Trading",
    description="Authentication, Authorization and User Management Service",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

jwt_manager = JWTManager()
security = HTTPBearer()
rate_limiter = RateLimiter()

def validate_email(email: str) -> bool:
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_phone(phone: str) -> bool:
    pattern = r'^[6-9]\d{9}$'
    return re.match(pattern, phone) is not None

def validate_username(username: str) -> bool:
    pattern = r'^[a-zA-Z0-9_]{3,30}$'
    return re.match(pattern, username) is not None

def get_user_by_login(login_id: str) -> Optional[dict]:
    connection = None
    try:
        connection = db.get_connection()
        cursor = connection.cursor(dictionary=True)
        
        if validate_email(login_id):
            cursor.execute("""
                SELECT id, email, password_hash, first_name, last_name, 
                       phone, username, country_id, is_active, email_verified, phone_verified
                FROM users WHERE email = %s
            """, (login_id,))
        elif validate_phone(login_id):
            cursor.execute("""
                SELECT id, email, password_hash, first_name, last_name, 
                       phone, username, country_id, is_active, email_verified, phone_verified
                FROM users WHERE phone = %s
            """, (login_id,))
        elif validate_username(login_id):
            cursor.execute("""
                SELECT id, email, password_hash, first_name, last_name, 
                       phone, username, country_id, is_active, email_verified, phone_verified
                FROM users WHERE username = %s
            """, (login_id,))
        else:
            return None
            
        user = cursor.fetchone()
        return user
    except Error as e:
        logger.error(f"Database error in get_user_by_login: {e}")
        return None
    finally:
        if connection and connection.is_connected():
            connection.close()

def get_user_with_roles(user_id: int) -> Optional[dict]:
    """Get user with their roles and permissions"""
    connection = None
    try:
        connection = db.get_connection()
        cursor = connection.cursor(dictionary=True)
        
        # Get user basic info
        cursor.execute("""
            SELECT id, uuid, email, first_name, last_name, phone, username,
                   country_id, is_active, email_verified, phone_verified,
                   preferred_currency, preferred_language, avatar_url,
                   created_at, updated_at
            FROM users WHERE id = %s
        """, (user_id,))
        user = cursor.fetchone()
        
        if not user:
            return None
        
        # Get user roles
        cursor.execute("""
            SELECT ur.name 
            FROM user_roles ur
            JOIN user_role_assignments ura ON ur.id = ura.role_id
            WHERE ura.user_id = %s
        """, (user_id,))
        user['roles'] = [row['name'] for row in cursor.fetchall()]
        
        # Get user permissions
        cursor.execute("""
            SELECT DISTINCT p.name
            FROM permissions p
            JOIN role_permissions rp ON p.id = rp.permission_id
            JOIN user_roles ur ON rp.role_id = ur.id
            JOIN user_role_assignments ura ON ur.id = ura.role_id
            WHERE ura.user_id = %s
        """, (user_id,))
        user['permissions'] = [row['name'] for row in cursor.fetchall()]
        
        return user
    except Error as e:
        logger.error(f"Database error in get_user_with_roles: {e}")
        return None
    finally:
        if connection and connection.is_connected():
            connection.close()

@app.get("/")
async def root():
    return {"message": "Auth Service - Pavitra Trading", "environment": config.app_env}

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
            "service": "auth",
            "environment": config.app_env,
            "users_count": user_count,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Error as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "service": "auth",
            "environment": config.app_env
        }

@app.post("/register", response_model=Token)
async def register_user(
    email: Optional[str] = Form(None),
    phone: Optional[str] = Form(None),
    username: Optional[str] = Form(None),
    password: str = Form(...),
    first_name: str = Form(...),
    last_name: str = Form(...),
    country_id: int = Form(1)
):
    identifier = email or phone or username
    rate_limiter.check_rate_limit(f"register:{identifier}")
    
    connection = None
    try:
        if not email and not phone and not username:
            raise HTTPException(status_code=400, detail="Email, phone, or username is required")
        
        if email and not validate_email(email):
            raise HTTPException(status_code=400, detail="Invalid email format")
        if phone and not validate_phone(phone):
            raise HTTPException(status_code=400, detail="Invalid phone format")
        if username and not validate_username(username):
            raise HTTPException(status_code=400, detail="Invalid username format")
        
        is_valid, message = PasswordSecurity.validate_password_strength(password)
        if not is_valid:
            raise HTTPException(status_code=400, detail=message)

        connection = db.get_connection()
        cursor = connection.cursor(dictionary=True)
        
        if email:
            cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
            if cursor.fetchone():
                raise HTTPException(status_code=400, detail="Email already exists")
        
        if phone:
            cursor.execute("SELECT id FROM users WHERE phone = %s", (phone,))
            if cursor.fetchone():
                raise HTTPException(status_code=400, detail="Phone already exists")
                
        if username:
            cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
            if cursor.fetchone():
                raise HTTPException(status_code=400, detail="Username already exists")

        hashed_password = PasswordSecurity.hash_password(password)
        
        cursor.execute("""
            INSERT INTO users (email, phone, username, password_hash, first_name, last_name, country_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (email, phone, username, hashed_password, first_name, last_name, country_id))
        
        user_id = cursor.lastrowid
        
        # Assign default customer role
        cursor.execute("""
            INSERT INTO user_role_assignments (user_id, role_id, assigned_by)
            SELECT %s, id, %s FROM user_roles WHERE name = 'customer'
        """, (user_id, user_id))
        
        connection.commit()

        token_data = {"sub": str(user_id), "email": email, "phone": phone, "username": username}
        access_token = jwt_manager.create_access_token(token_data)
        
        logger.info(f"User registered successfully: {user_id}")
        audit_logger.log_security_event("USER_REGISTERED", str(user_id), "0.0.0.0", "New user registration")
        
        user_roles = jwt_manager.get_user_roles_and_permissions(str(user_id))
        
        return Token(
            access_token=access_token,
            token_type="bearer",
            expires_in=1800,
            user_roles=user_roles["roles"],
            user_permissions=user_roles["permissions"]
        )
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

@app.post("/login", response_model=Token)
async def login_user(login_id: str = Form(...), password: str = Form(...)):
    rate_limiter.check_rate_limit(f"login:{login_id}")
    
    connection = None
    try:
        user = get_user_by_login(login_id)
        if not user:
            audit_logger.log_login_attempt(login_id, False, "0.0.0.0", "Unknown user")
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        if not user['is_active']:
            audit_logger.log_login_attempt(str(user['id']), False, "0.0.0.0", "Account deactivated")
            raise HTTPException(status_code=401, detail="Account is deactivated")
            
        if not PasswordSecurity.verify_password(password, user['password_hash']):
            audit_logger.log_login_attempt(str(user['id']), False, "0.0.0.0", "Wrong password")
            raise HTTPException(status_code=401, detail="Invalid credentials")

        connection = db.get_connection()
        cursor = connection.cursor()
        cursor.execute("UPDATE users SET last_login = %s WHERE id = %s", (datetime.utcnow(), user['id']))
        connection.commit()

        token_data = {
            "sub": str(user['id']), 
            "email": user['email'],
            "phone": user['phone'],
            "username": user['username']
        }
        access_token = jwt_manager.create_access_token(token_data)
        
        audit_logger.log_login_attempt(str(user['id']), True, "0.0.0.0", "Successful login")
        logger.info(f"User logged in successfully: {user['id']}")
        
        user_roles = jwt_manager.get_user_roles_and_permissions(str(user['id']))
        
        return Token(
            access_token=access_token,
            token_type="bearer",
            expires_in=1800,
            user_roles=user_roles["roles"],
            user_permissions=user_roles["permissions"]
        )
    except HTTPException:
        raise
    except Error as e:
        logger.error(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Database error")
    finally:
        if connection and connection.is_connected():
            connection.close()

@app.get("/users/me", response_model=UserResponse)
async def get_current_user_profile(payload: dict = Depends(allow_authenticated)):
    user_id = payload.get("sub")
    user = get_user_with_roles(int(user_id))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

# ... rest of the file remains the same ...
