from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import HTTPException, status
import secrets
import string
import re
from .config import config
import logging

logger = logging.getLogger(__name__)

# Password hashing - CHANGED: Use Argon2 instead of bcrypt
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        if not plain_password or not hashed_password:
            logger.error("Empty password or hash provided")
            return False

        # Handle cases where hash might be None or empty
        if not hashed_password.startswith('$argon2'):
            logger.error(f"Invalid hash format: {hashed_password[:50]}...")
            return False

        result = pwd_context.verify(plain_password, hashed_password)
        logger.info(f"🔐 Password verification result: {result}")
        return result

    except Exception as e:
        logger.error(f"❌ Password verification failed: {str(e)}")
        return False


def get_password_hash(password: str) -> str:
    try:
        if not password:
            raise ValueError("Password cannot be empty")
        return pwd_context.hash(password)
    except Exception as e:
        logger.error(f"❌ Password hashing failed: {str(e)}")
        raise

# JWT token handling
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=30)

    to_encode.update({"exp": expire})

    try:
        encoded_jwt = jwt.encode(to_encode, config.jwt_secret, algorithm=config.jwt_algorithm)
        return encoded_jwt
    except Exception as e:
        logger.error(f"❌ Token creation failed: {str(e)}")
        raise

def verify_token(token: str) -> Optional[Dict[str, Any]]:
    try:
        payload = jwt.decode(token, config.jwt_secret, algorithms=[config.jwt_algorithm])
        return payload
    except JWTError as e:
        logger.error(f"❌ JWT verification failed: {e}")
        return None

# Input sanitization
def sanitize_input(input_str: str) -> str:
    if not input_str:
        return input_str

    dangerous_chars = ['<', '>', 'script', 'javascript', 'onload', 'onerror']
    sanitized = input_str
    for char in dangerous_chars:
        sanitized = sanitized.replace(char, '')

    return sanitized.strip()

def validate_email(email: str) -> bool:
    if not email:
        return False
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_phone(phone: str) -> bool:
    if not phone:
        return False
    pattern = r'^\+?[1-9]\d{1,14}$'
    return re.match(pattern, phone) is not None