"""
Structured logging configuration for Clintra.
"""
import logging
import sys
from datetime import datetime
from typing import Dict, Any
import json

class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured JSON logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields
        if hasattr(record, 'extra_fields'):
            log_entry.update(record.extra_fields)
        
        return json.dumps(log_entry, ensure_ascii=False)

def setup_logging():
    """Setup structured logging for the application."""
    
    # Create logger
    logger = logging.getLogger("clintra")
    logger.setLevel(logging.INFO)
    
    # Remove existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Console handler with structured formatting
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(StructuredFormatter())
    
    # File handler for errors
    file_handler = logging.FileHandler("clintra.log")
    file_handler.setLevel(logging.ERROR)
    file_handler.setFormatter(StructuredFormatter())
    
    # Add handlers
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    # Set levels for third-party libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)
    
    return logger

def log_api_call(endpoint: str, method: str, status_code: int, duration: float, user_id: int = None):
    """Log API call with structured data."""
    logger = logging.getLogger("clintra.api")
    logger.info(
        f"API call: {method} {endpoint}",
        extra={
            "extra_fields": {
                "endpoint": endpoint,
                "method": method,
                "status_code": status_code,
                "duration_ms": round(duration * 1000, 2),
                "user_id": user_id
            }
        }
    )

def log_error(error: Exception, context: Dict[str, Any] = None):
    """Log error with context."""
    logger = logging.getLogger("clintra.error")
    logger.error(
        f"Error: {str(error)}",
        extra={
            "extra_fields": {
                "error_type": type(error).__name__,
                "context": context or {}
            }
        },
        exc_info=True
    )

def log_performance(operation: str, duration: float, details: Dict[str, Any] = None):
    """Log performance metrics."""
    logger = logging.getLogger("clintra.performance")
    logger.info(
        f"Performance: {operation}",
        extra={
            "extra_fields": {
                "operation": operation,
                "duration_ms": round(duration * 1000, 2),
                "details": details or {}
            }
        }
    )

def log_security(event: str, details: Dict[str, Any] = None):
    """Log security events."""
    logger = logging.getLogger("clintra.security")
    logger.warning(
        f"Security event: {event}",
        extra={
            "extra_fields": {
                "event": event,
                "details": details or {}
            }
        }
    )

