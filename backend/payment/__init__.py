"""
Payment Processing Service for Pavitra Trading

This service handles:
- Payment method management
- Payment processing
- Transaction history
- Refund processing
- Payment gateway integration
"""

__version__ = "1.0.0"
__service_name__ = "payment-service"

from .main import app

__all__ = ['app']
