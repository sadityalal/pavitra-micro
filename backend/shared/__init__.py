from .config import config
from .database import db
from .security import (
    verify_password, get_password_hash, create_access_token,
    verify_token, sanitize_input, validate_email, validate_phone
)
from .logging_config import setup_logging, get_logger
from .session_service import session_service
from .redis_client import redis_client
from .rabbitmq_client import rabbitmq_client
from .auth_middleware import get_current_user, require_roles, require_permissions
from .rate_limiter import rate_limiter
from .session_middleware import SecureSessionMiddleware, get_session, get_session_id, is_new_session
from .session_models import SessionData, SessionType
from .cart_migration import migrate_guest_cart_to_user

__all__ = [
    'config',
    'db',
    'verify_password',
    'get_password_hash',
    'create_access_token',
    'verify_token',
    'sanitize_input',
    'validate_email',
    'validate_phone',
    'setup_logging',
    'get_logger',
    'redis_client',
    'rabbitmq_client',
    'get_current_user',
    'require_roles',
    'require_permissions',
    'rate_limiter',
    'SecureSessionMiddleware',
    'get_session',
    'get_session_id',
    'is_new_session',
    'session_service',
    'SessionData',
    'SessionType',
    'migrate_guest_cart_to_user',
]

# Backward compatibility
SessionMiddleware = SecureSessionMiddleware