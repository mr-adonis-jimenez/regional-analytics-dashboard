"""Structured logging configuration for Geo-Analytics API.

Provides JSON-formatted logs with request tracking, performance metrics,
and error context for debugging and monitoring.
"""

import logging
import sys
import json
import time
from datetime import datetime
from typing import Any, Dict, Optional
from contextvars import ContextVar
import traceback

# Context variable for request tracking
request_id_var: ContextVar[Optional[str]] = ContextVar('request_id', default=None)


class JSONFormatter(logging.Formatter):
    """Custom formatter for JSON-structured logs."""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data: Dict[str, Any] = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }
        
        # Add request ID if available
        request_id = request_id_var.get()
        if request_id:
            log_data['request_id'] = request_id
        
        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': ''.join(traceback.format_exception(*record.exc_info))
            }
        
        # Add extra fields from record
        if hasattr(record, 'extra_fields'):
            log_data.update(record.extra_fields)
        
        return json.dumps(log_data)


def setup_logger(name: str = 'geo-analytics-api', level: str = 'INFO') -> logging.Logger:
    """Configure and return a logger with JSON formatting.
    
    Args:
        name: Logger name
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    # Remove existing handlers
    logger.handlers.clear()
    
    # Console handler with JSON formatting
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(JSONFormatter())
    logger.addHandler(console_handler)
    
    # Prevent propagation to avoid duplicate logs
    logger.propagate = False
    
    return logger


class LoggerAdapter(logging.LoggerAdapter):
    """Enhanced logger adapter with extra context."""
    
    def process(self, msg: str, kwargs: Dict) -> tuple:
        # Add extra fields if present
        if 'extra' not in kwargs:
            kwargs['extra'] = {}
        
        if 'extra_fields' not in kwargs['extra']:
            kwargs['extra']['extra_fields'] = {}
        
        # Merge self.extra into extra_fields
        kwargs['extra']['extra_fields'].update(self.extra)
        
        return msg, kwargs


def get_logger(name: str = 'geo-analytics-api', **extra_context) -> LoggerAdapter:
    """Get a logger with optional extra context.
    
    Args:
        name: Logger name
        **extra_context: Additional context fields to include in all logs
    
    Returns:
        LoggerAdapter instance with extra context
    """
    logger = logging.getLogger(name)
    return LoggerAdapter(logger, extra_context)


# Performance logging utilities
class PerformanceLogger:
    """Context manager for logging performance metrics."""
    
    def __init__(self, logger: logging.Logger, operation: str, **context):
        self.logger = logger
        self.operation = operation
        self.context = context
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        self.logger.info(f"Starting: {self.operation}", extra={'extra_fields': self.context})
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        log_data = {
            **self.context,
            'duration_ms': round(duration * 1000, 2),
            'success': exc_type is None
        }
        
        if exc_type:
            self.logger.error(
                f"Failed: {self.operation}",
                extra={'extra_fields': log_data},
                exc_info=(exc_type, exc_val, exc_tb)
            )
        else:
            self.logger.info(f"Completed: {self.operation}", extra={'extra_fields': log_data})
        
        return False  # Don't suppress exceptions


# Initialize default logger
default_logger = setup_logger()
