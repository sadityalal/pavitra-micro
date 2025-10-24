"""
Authentication and Authorization Service for Pavitra Trading

This service handles:
- User registration and login
- JWT token management  
- Role-based access control
- User management for administrators
"""

__version__ = "1.0.0"
__service_name__ = "auth-service"

from .main import app

__all__ = ['app']
