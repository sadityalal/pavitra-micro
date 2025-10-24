"""
Pavitra Trading Backend Microservices

A complete e-commerce backend built with FastAPI and microservices architecture.

Services:
- auth: Authentication and authorization
- product: Product catalog management  
- order: Order processing and management
- user: User profile management
- payment: Payment processing
- notification: Email and SMS notifications

Shared modules provide common functionality across all services.
"""

__version__ = "1.0.0"
__author__ = "Pavitra Trading Development Team"

# Service imports
from . import auth
from . import product
from . import order
from . import user
from . import payment
from . import notification

# Shared modules
from . import shared

__all__ = [
    'auth', 'product', 'order', 'user', 'payment', 'notification', 'shared'
]
