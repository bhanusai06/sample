"""
Enterprise Data Sanitization Platform
Forensic Logging Engine
"""
import logging
import os
from logging.handlers import TimedRotatingFileHandler
from datetime import datetime, timezone
from typing import Dict, Any

import sys
# Ensure utils can be imported
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.constants import LOG_DIR, LOG_FORMAT, DATE_FORMAT

class UTCFormatter(logging.Formatter):
    """Custom formatter to enforce strict ISO-8601 UTC timestamps."""
    def formatTime(self, record: logging.LogRecord, datefmt: str | None = None) -> str:
        dt = datetime.fromtimestamp(record.created, tz=timezone.utc)
        if datefmt:
            return dt.strftime(datefmt)
        return dt.isoformat()

def _setup_logger(name: str, log_file: str, level: int = logging.INFO) -> logging.Logger:
    """
    Configure a rotating, append-only logger.
    
    Args:
        name: The internal name of the logger.
        log_file: The filename for the log.
        level: The logging level.
        
    Returns:
        Configured logging.Logger instance.
    """
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR, exist_ok=True)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Prevent adding multiple handlers if already configured
    if logger.hasHandlers():
        return logger

    file_path = os.path.join(LOG_DIR, log_file)
    
    # Daily rotation, keep 365 days of logs for audit purposes
    handler = TimedRotatingFileHandler(
        file_path, 
        when="midnight", 
        interval=1, 
        backupCount=365, 
        encoding="utf-8"
    )
    
    formatter = UTCFormatter(LOG_FORMAT, DATE_FORMAT)
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    # Do not propagate to root logger to avoid console prints
    logger.propagate = False
    
    return logger

# Initialize core loggers
device_logger = _setup_logger("device", "device.log")
wipe_logger = _setup_logger("wipe", "wipe.log")
certificate_logger = _setup_logger("certificate", "certificate.log")
security_logger = _setup_logger("security", "security.log")
error_logger = _setup_logger("error", "error.log", level=logging.ERROR)

def log_security_event(module_name: str, function_name: str, message: str) -> None:
    """Log a security-critical event."""
    # We inject custom_module and custom_funcName via extra to avoid overwriting built-in LogRecord attributes
    security_logger.warning(message, extra={"custom_module": module_name, "custom_funcName": function_name})

def log_error_event(module_name: str, function_name: str, message: str, exc_info: bool = False) -> None:
    """Log an error event."""
    error_logger.error(message, exc_info=exc_info, extra={"custom_module": module_name, "custom_funcName": function_name})
