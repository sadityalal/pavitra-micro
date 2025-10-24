from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List
from shared.security.jwt_utils import JWTManager
from shared.utils.logger import get_auth_logger

logger = get_auth_logger()
jwt_manager = JWTManager()
security = HTTPBearer()

class RoleChecker:
    def __init__(self, allowed_roles: List[str] = None, allowed_permissions: List[str] = None):
        self.allowed_roles = allowed_roles or []
        self.allowed_permissions = allowed_permissions or []
    
    def __call__(self, credentials: HTTPAuthorizationCredentials = Depends(security)):
        token = credentials.credentials
        
        # Super admin has access to everything
        if jwt_manager.is_super_admin(token):
            return jwt_manager.verify_token(token)
        
        # Check roles
        if self.allowed_roles:
            has_role = any(jwt_manager.has_role(token, role) for role in self.allowed_roles)
            if not has_role:
                logger.warning(f"Access denied: User doesn't have required roles: {self.allowed_roles}")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient role permissions"
                )
        
        # Check specific permissions
        if self.allowed_permissions:
            has_permission = all(jwt_manager.has_permission(token, perm) for perm in self.allowed_permissions)
            if not has_permission:
                logger.warning(f"Access denied: User doesn't have required permissions: {self.allowed_permissions}")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions"
                )
        
        return jwt_manager.verify_token(token)

# Common role checkers
allow_super_admin = RoleChecker(allowed_roles=["super_admin"])
allow_admin = RoleChecker(allowed_roles=["super_admin", "admin"])
allow_vendor = RoleChecker(allowed_roles=["super_admin", "admin", "vendor"])
allow_content_manager = RoleChecker(allowed_roles=["super_admin", "admin", "content_manager"])
allow_support_staff = RoleChecker(allowed_roles=["super_admin", "admin", "support_staff"])
allow_authenticated = RoleChecker()  # Just requires valid token

# Permission-based checkers
allow_manage_users = RoleChecker(allowed_permissions=["manage_users"])
allow_manage_products = RoleChecker(allowed_permissions=["manage_products"])
allow_manage_orders = RoleChecker(allowed_permissions=["manage_orders"])
allow_manage_site_settings = RoleChecker(allowed_permissions=["manage_site_settings"])
allow_view_analytics = RoleChecker(allowed_permissions=["view_analytics"])
