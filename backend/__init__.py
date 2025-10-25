"""
Pavitra Trading E-commerce Backend
Microservices architecture with shared components
"""

__version__ = "1.0.0"
__author__ = "Pavitra Trading Team"

# Import shared modules to make them easily accessible
from shared.config import config
from shared.database import db
from shared.security import (
    verify_password, get_password_hash, create_access_token,
    verify_token, sanitize_input, validate_email, validate_phone
)
from shared.logging_config import setup_logging, get_logger

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
    'get_logger'
]
