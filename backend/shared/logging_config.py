import logging
import sys
import json
import os
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

    # Create logs directory if it doesn't exist
    log_dir = "/app/logs"
    os.makedirs(log_dir, exist_ok=True)

    # File handler - writes to /app/logs/{service_name}.log
    file_handler = logging.FileHandler(f"{log_dir}/{service_name}.log")
    file_formatter = CustomJsonFormatter()
    file_handler.setFormatter(file_formatter)

    # Console handler - writes to stdout (for docker logs)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(file_formatter)

    # Add both handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

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
