"""
Order Management Service for Pavitra Trading

This service handles:
- Order creation and management
- Order status tracking
- Order history for customers
- Admin order management
- Sales reporting
"""

__version__ = "1.0.0"
__service_name__ = "order-service"

from .main import app

__all__ = ['app']
