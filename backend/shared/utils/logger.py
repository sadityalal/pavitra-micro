import logging
import logging.handlers
import os

class ServiceLogger:
    _loggers = {}
    
    @classmethod
    def get_logger(cls, service_name: str, log_level: str = "INFO"):
        if service_name in cls._loggers:
            return cls._loggers[service_name]
        
        logger = logging.getLogger(service_name)
        logger.setLevel(getattr(logging, log_level.upper()))
        logger.handlers.clear()
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Console handler only
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        cls._loggers[service_name] = logger
        return logger

# Simple logger functions
def get_auth_logger():
    return ServiceLogger.get_logger("auth")

def get_product_logger():
    return ServiceLogger.get_logger("product")

def get_order_logger():
    return ServiceLogger.get_logger("order")

def get_user_logger():
    return ServiceLogger.get_logger("user")

def get_payment_logger():
    return ServiceLogger.get_logger("payment")

def get_notification_logger():
    return ServiceLogger.get_logger("notification")

def get_api_logger():
    return ServiceLogger.get_logger("api")

class AuditLogger:
    def __init__(self):
        self.logger = get_auth_logger()
    
    def log_login_attempt(self, user_id: str, success: bool, ip: str, user_agent: str):
        status = "SUCCESS" if success else "FAILED"
        self.logger.info(f"LOGIN_ATTEMPT - User: {user_id} - Status: {status} - IP: {ip}")
