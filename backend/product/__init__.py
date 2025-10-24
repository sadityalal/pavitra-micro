"""
Product Catalog Service for Pavitra Trading

This service handles:
- Product catalog management
- Category and brand management
- Inventory management
- Product search and filtering
- Featured products
"""

__version__ = "1.0.0"
__service_name__ = "product-service"

from .main import app

__all__ = ['app']
