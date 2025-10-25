from fastapi import HTTPException, Request, status
from typing import Optional, Dict, Any
from .security import verify_token
from .redis_client import redis_client
import logging

logger = logging.getLogger(__name__)

async def get_current_user(request: Request) -> Dict[str, Any]:
    """Extract and verify JWT token from request"""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )
    
    token = auth_header[7:]
    
    # Try to get user from cache first
    cached_user = redis_client.get_cached_session(f"token:{token}")
    if cached_user:
        logger.info("User authenticated from cache")
        return cached_user
    
    # Verify token
    payload = verify_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    
    # Cache the user session
    redis_client.cache_user_session(
        user_id=int(payload['sub']),
        session_data=payload,
        expire=3600  # 1 hour
    )
    
    return payload

async def require_roles(required_roles: list, request: Request):
    """Middleware to require specific roles"""
    user = await get_current_user(request)
    
    user_roles = user.get('roles', [])
    if not any(role in user_roles for role in required_roles):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    
    return user

async def require_permissions(required_permissions: list, request: Request):
    """Middleware to require specific permissions"""
    user = await get_current_user(request)
    
    user_permissions = user.get('permissions', [])
    if not any(perm in user_permissions for perm in required_permissions):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    
    return user
