"""
Pavitra Trading E-commerce Backend
Microservices architecture with shared components
"""

__version__ = "1.0.0"
__author__ = "Pavitra Trading Team"

from shared.config import config
from shared.database import db
from shared.security import verify_password, get_password_hash, create_access_token, verify_token, sanitize_input, validate_email, validate_phone
from shared.logging_config import setup_logging, get_logger
from shared.redis_client import redis_client
from shared.rabbitmq_client import rabbitmq_client
from shared.auth_middleware import get_current_user, require_roles
from shared.rate_limiter import rate_limiter
from shared.session_middleware import SecureSessionMiddleware, get_session, get_session_id
from shared.session_service import session_service
from shared.session_models import SessionData, SessionType

__all__ = [
    'config', 'db', 'verify_password', 'get_password_hash', 'create_access_token',
    'verify_token', 'sanitize_input', 'validate_email', 'validate_phone',
    'setup_logging', 'get_logger', 'redis_client', 'rabbitmq_client',
    'get_current_user', 'require_roles', 'rate_limiter', 'SecureSessionMiddleware',
    'get_session', 'get_session_id', 'session_service', 'SessionData', 'SessionType'
]