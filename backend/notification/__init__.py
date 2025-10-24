"""
Notification Service for Pavitra Trading

This service handles:
- Email notifications
- SMS notifications
- Push notifications
- Order confirmations
- Bulk messaging
"""

__version__ = "1.0.0"
__service_name__ = "notification-service"

from .main import app

__all__ = ['app']
