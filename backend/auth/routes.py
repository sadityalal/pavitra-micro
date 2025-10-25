from fastapi import APIRouter, HTTPException, Depends, Form
from fastapi.security import HTTPBearer
from typing import Optional
import mysql.connector
from mysql.connector import Error
import re
from datetime import datetime

from .models import (
    UserCreate, UserLogin, Token, UserResponse, 
    RoleResponse, PermissionCheck, HealthResponse
)
from shared.config import config
from shared.database import db

router = APIRouter()
security = HTTPBearer()

def validate_email(email: str) -> bool:
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_phone(phone: str) -> bool:
    pattern = r'^[6-9]\d{9}$'
    return re.match(pattern, phone) is not None

def validate_username(username: str) -> bool:
    pattern = r'^[a-zA-Z0-9_]{3,30}$'
    return re.match(pattern, username) is not None

@router.get("/health", response_model=HealthResponse)
async def health():
    try:
        connection = db.get_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        cursor.close()
        connection.close()
        
        return HealthResponse(
            status="healthy",
            service="auth",
            environment="production",
            users_count=user_count,
            timestamp=datetime.utcnow()
        )
    except Error as e:
        return HealthResponse(
            status="unhealthy",
            service="auth", 
            environment="production",
            users_count=0,
            timestamp=datetime.utcnow()
        )

@router.post("/register", response_model=Token)
async def register_user(
    email: Optional[str] = Form(None),
    phone: Optional[str] = Form(None),
    username: Optional[str] = Form(None),
    password: str = Form(...),
    first_name: str = Form(...),
    last_name: str = Form(...),
    country_id: int = Form(1)
):
    # Basic validation
    if not email and not phone and not username:
        raise HTTPException(status_code=400, detail="Email, phone, or username is required")
    
    if email and not validate_email(email):
        raise HTTPException(status_code=400, detail="Invalid email format")
    
    # TODO: Add password validation, user creation logic
    # This is simplified for now
    
    return Token(
        access_token="simulated_token",
        token_type="bearer",
        expires_in=1800,
        user_roles=["customer"],
        user_permissions=[]
    )

@router.post("/login", response_model=Token)
async def login_user(login_id: str = Form(...), password: str = Form(...)):
    # TODO: Add actual login logic
    return Token(
        access_token="simulated_token",
        token_type="bearer", 
        expires_in=1800,
        user_roles=["customer"],
        user_permissions=[]
    )

@router.get("/users/me", response_model=UserResponse)
async def get_current_user_profile():
    # TODO: Add JWT authentication
    return UserResponse(
        id=1,
        uuid="simulated-uuid",
        email="test@example.com",
        first_name="Test",
        last_name="User",
        email_verified=True,
        phone_verified=False,
        is_active=True,
        roles=["customer"],
        permissions=[],
        preferred_currency="INR",
        preferred_language="en",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
