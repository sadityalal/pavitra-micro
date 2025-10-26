from fastapi import HTTPException, Request, status
from typing import Optional, Dict, Any, List
from .security import verify_token
from .redis_client import redis_client
from .database import db
import logging

logger = logging.getLogger(__name__)


async def get_current_user(request: Request) -> Dict[str, Any]:
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )

    token = auth_header[7:]

    # Check cache first
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

    # Get user data from database
    try:
        with db.get_cursor() as cursor:
            cursor.execute("""
                SELECT 
                    u.id, u.uuid, u.email, u.first_name, u.last_name, u.phone,
                    u.email_verified, u.phone_verified, u.is_active,
                    u.country_id, u.preferred_currency, u.preferred_language,
                    u.avatar_url
                FROM users u
                WHERE u.id = %s AND u.is_active = 1
            """, (int(payload['sub']),))

            user_data = cursor.fetchone()
            if not user_data:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found or inactive"
                )

            # Get user roles and permissions
            cursor.execute("""
                SELECT 
                    ur.name as role_name,
                    p.name as permission_name
                FROM user_role_assignments ura
                JOIN user_roles ur ON ura.role_id = ur.id
                LEFT JOIN role_permissions rp ON ur.id = rp.role_id
                LEFT JOIN permissions p ON rp.permission_id = p.id
                WHERE ura.user_id = %s
            """, (user_data['id'],))

            roles = set()
            permissions = set()
            for row in cursor.fetchall():
                if row['role_name']:
                    roles.add(row['role_name'])
                if row['permission_name']:
                    permissions.add(row['permission_name'])

            # Build user payload
            user_payload = {
                'sub': user_data['id'],
                'uuid': user_data['uuid'],
                'email': user_data['email'],
                'first_name': user_data['first_name'],
                'last_name': user_data['last_name'],
                'phone': user_data['phone'],
                'email_verified': bool(user_data['email_verified']),
                'phone_verified': bool(user_data['phone_verified']),
                'is_active': bool(user_data['is_active']),
                'country_id': user_data['country_id'],
                'preferred_currency': user_data['preferred_currency'],
                'preferred_language': user_data['preferred_language'],
                'avatar_url': user_data['avatar_url'],
                'roles': list(roles),
                'permissions': list(permissions)
            }

            # Cache user session
            redis_client.cache_user_session(
                user_id=user_data['id'],
                session_data=user_payload,
                expire=3600
            )

            return user_payload

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get user data: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to authenticate user"
        )


async def require_roles(required_roles: List[str], request: Request):
    user = await get_current_user(request)
    user_roles = user.get('roles', [])

    if not any(role in user_roles for role in required_roles):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient role permissions"
        )

    return user


async def require_permissions(required_permissions: List[str], request: Request):
    user = await get_current_user(request)
    user_permissions = user.get('permissions', [])

    if not any(perm in user_permissions for perm in required_permissions):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )

    return user


async def require_any_role(required_roles: List[str], request: Request):
    user = await get_current_user(request)
    user_roles = user.get('roles', [])

    if not any(role in user_roles for role in required_roles):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient role permissions"
        )

    return user


async def require_all_roles(required_roles: List[str], request: Request):
    user = await get_current_user(request)
    user_roles = user.get('roles', [])

    if not all(role in user_roles for role in required_roles):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Missing required roles"
        )

    return user