"""
User Profile Service for Pavitra Trading

This service handles:
- User profile management
- Address management
- Password changes
- Avatar uploads
- User preferences
"""

__version__ = "1.0.0"
__service_name__ = "user-service"

from .main import app

__all__ = ['app']
