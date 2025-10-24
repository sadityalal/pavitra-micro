import logging
import logging.handlers
import os
from datetime import datetime
from typing import Dict

class ServiceLogger:
    def __init__(self, service_name: str, log_level: str = "INFO"):
        self.service_name = service_name
        self.log_level = getattr(logging, log_level.upper())
        self.setup_logging()
    
    def setup_logging(self):
        """Setup logging configuration for each service"""
        # Create logs directory if not exists
        logs_dir = f"backend/logs/{self.service_name}"
        os.makedirs(logs_dir, exist_ok=True)
        
        # Create logger
        logger = logging.getLogger(self.service_name)
        logger.setLevel(self.log_level)
        
        # Clear existing handlers
        logger.handlers.clear()
        
        # Formatter
        formatter = logging.Formatter(
            f'%(asctime)s - {self.service_name} - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # File Handler (Rotating)
        log_file = f"{logs_dir}/{self.service_name}.log"
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        # Console Handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        return logger

# Create loggers for each service
def get_service_logger(service_name: str) -> logging.Logger:
    """Get logger for specific service"""
    return ServiceLogger(service_name).setup_logging()

# Audit logging for security events
class AuditLogger:
    def __init__(self):
        self.logger = get_service_logger("audit")
    
    def log_security_event(self, event_type: str, user_id: str, details: Dict):
        """Log security-related events"""
        self.logger.warning(
            f"SECURITY_EVENT - {event_type} - User: {user_id} - Details: {details}"
        )
    
    def log_authentication(self, event_type: str, user_id: str, success: bool, ip: str = None):
        """Log authentication events"""
        status = "SUCCESS" if success else "FAILED"
        self.logger.info(
            f"AUTH_{event_type.upper()} - {status} - User: {user_id} - IP: {ip}"
        )
