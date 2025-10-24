"""
Shared modules for Pavitra Trading Microservices Architecture

This package contains common utilities, models, and security components
used across all microservices.
"""

__version__ = "1.0.0"
__author__ = "Pavitra Trading Team"
__description__ = "Shared components for microservices architecture"

# Import main components for easy access
from . import database
from . import models
from . import security
from . import utils

__all__ = ['database', 'models', 'security', 'utils']
