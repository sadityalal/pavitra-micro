import logging
import sys
import json
from typing import Optional
from .config import config

class CustomJsonFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            'timestamp': self.formatTime(record),
            'level': record.levelname,
            'service': getattr(record, 'service', 'unknown'),
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        if record.exc_info:
            log_record['exception'] = self.formatException(record.exc_info)
            
        return json.dumps(log_record)

def setup_logging(service_name: str):
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, config.log_level))
    
    # Remove existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Create console handler with JSON formatting
    handler = logging.StreamHandler(sys.stdout)
    formatter = CustomJsonFormatter()
    handler.setFormatter(formatter)
    
    logger.addHandler(handler)
    
    # Add service name to all log records
    old_factory = logging.getLogRecordFactory()
    
    def record_factory(*args, **kwargs):
        record = old_factory(*args, **kwargs)
        record.service = service_name
        return record
        
    logging.setLogRecordFactory(record_factory)
    
    return logger

def get_logger(name: str):
    return logging.getLogger(name)
