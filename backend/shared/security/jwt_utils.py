import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import logging
from fastapi import HTTPException, status
from shared.utils.config import config
from shared.utils.logger import get_auth_logger
from shared.database.database import db
import mysql.connector

logger = get_auth_logger()

class JWTManager:
    def __init__(self):
        self.secret_key = config.jwt_secret
        self.algorithm = config.jwt_algorithm
    
    def get_user_roles_and_permissions(self, user_id: str) -> Dict[str, List[str]]:
        """Get user roles and permissions from database"""
        connection = None
        try:
            connection = db.get_connection()
            cursor = connection.cursor(dictionary=True)
            
            # Get user roles
            cursor.execute("""
                SELECT ur.name 
                FROM user_roles ur
                JOIN user_role_assignments ura ON ur.id = ura.role_id
                WHERE ura.user_id = %s
            """, (user_id,))
            roles = [row['name'] for row in cursor.fetchall()]
            
            # Get user permissions
            cursor.execute("""
                SELECT DISTINCT p.name
                FROM permissions p
                JOIN role_permissions rp ON p.id = rp.permission_id
                JOIN user_roles ur ON rp.role_id = ur.id
                JOIN user_role_assignments ura ON ur.id = ura.role_id
                WHERE ura.user_id = %s
            """, (user_id,))
            permissions = [row['name'] for row in cursor.fetchall()]
            
            return {
                "roles": roles,
                "permissions": permissions
            }
        except Exception as e:
            logger.error(f"Error getting user roles/permissions: {e}")
            return {"roles": [], "permissions": []}
        finally:
            if connection and connection.is_connected():
                connection.close()
    
    def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        try:
            to_encode = data.copy()
            if expires_delta:
                expire = datetime.utcnow() + expires_delta
            else:
                expire = datetime.utcnow() + timedelta(minutes=30)
            
            # Get user roles and permissions
            user_data = self.get_user_roles_and_permissions(data.get("sub"))
            
            to_encode.update({
                "exp": expire, 
                "iat": datetime.utcnow(),
                "iss": "pavitra-trading",
                "roles": user_data["roles"],
                "permissions": user_data["permissions"]
            })
            
            encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
            logger.info(f"JWT token created for user: {data.get('sub')} with roles: {user_data['roles']}")
            return encoded_jwt
        except Exception as e:
            logger.error(f"JWT creation failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Could not create access token"
            )
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("JWT token expired")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid JWT token: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
    
    def extract_user_id(self, token: str) -> str:
        payload = self.verify_token(token)
        user_id = payload.get("sub")
        if not user_id:
            logger.warning("JWT token missing user ID")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload"
            )
        return user_id
    
    def has_permission(self, token: str, permission: str) -> bool:
        """Check if user has specific permission"""
        try:
            payload = self.verify_token(token)
            user_permissions = payload.get("permissions", [])
            return permission in user_permissions
        except Exception:
            return False
    
    def has_role(self, token: str, role: str) -> bool:
        """Check if user has specific role"""
        try:
            payload = self.verify_token(token)
            user_roles = payload.get("roles", [])
            return role in user_roles
        except Exception:
            return False
    
    def is_super_admin(self, token: str) -> bool:
        return self.has_role(token, "super_admin")
    
    def is_admin(self, token: str) -> bool:
        return self.has_role(token, "admin") or self.is_super_admin(token)
