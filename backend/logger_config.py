"""
Centralized Logging Configuration Module

This module provides a consistent logging configuration across the entire application.
It supports different log levels for development and production environments,
and can optionally write logs to files.

Usage:
    from logger_config import setup_logging, get_logger
    
    # Setup logging (call once at application startup)
    setup_logging()
    
    # Get logger for your module
    logger = get_logger(__name__)
    logger.info("Application started")
"""

import os
import logging
import sys
from logging.handlers import RotatingFileHandler
from datetime import datetime


# Default log format
DEFAULT_LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
DETAILED_LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'

# Log levels
LOG_LEVELS = {
    'DEBUG': logging.DEBUG,
    'INFO': logging.INFO,
    'WARNING': logging.WARNING,
    'ERROR': logging.ERROR,
    'CRITICAL': logging.CRITICAL
}


def get_log_level():
    """
    Get log level from environment variable or default based on FLASK_ENV
    
    Returns:
        int: Logging level constant
    """
    env = os.getenv('FLASK_ENV', 'production')
    log_level_str = os.getenv('LOG_LEVEL', '').upper()
    
    # If LOG_LEVEL is explicitly set, use it
    if log_level_str in LOG_LEVELS:
        return LOG_LEVELS[log_level_str]
    
    # Otherwise, use defaults based on environment
    if env == 'production':
        return logging.WARNING  # Production: WARNING and above (reduce noise)
    else:
        return logging.INFO  # Development: INFO and above (reduced from DEBUG)


def get_log_format():
    """
    Get log format based on environment
    
    Returns:
        str: Log format string
    """
    env = os.getenv('FLASK_ENV', 'production')
    
    if env == 'production':
        return DEFAULT_LOG_FORMAT
    else:
        return DETAILED_LOG_FORMAT  # Development: Include file and line number


def setup_logging(
    log_file=None,
    max_bytes=10 * 1024 * 1024,  # 10MB
    backup_count=5,
    console=True
):
    """
    Setup centralized logging configuration for the application.
    
    This function should be called once at application startup.
    It configures:
    - Log level based on environment (DEBUG for dev, INFO for production)
    - Console logging (always enabled)
    - File logging (optional, if log_file is provided)
    - Consistent log format across all modules
    
    Args:
        log_file (str, optional): Path to log file. If None, no file logging.
        max_bytes (int): Maximum size of log file before rotation (default: 10MB)
        backup_count (int): Number of backup log files to keep (default: 5)
        console (bool): Whether to enable console logging (default: True)
    
    Example:
        # Basic setup (console only)
        setup_logging()
        
        # With file logging
        setup_logging(log_file='logs/app.log')
        
        # Custom configuration
        setup_logging(
            log_file='logs/app.log',
            max_bytes=20 * 1024 * 1024,  # 20MB
            backup_count=10
        )
    """
    # Get configuration
    log_level = get_log_level()
    log_format = get_log_format()
    
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Remove existing handlers to avoid duplicates
    root_logger.handlers.clear()
    
    # Create formatter
    formatter = logging.Formatter(log_format, datefmt='%Y-%m-%d %H:%M:%S')
    
    # Console handler (always enabled by default)
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
    
    # File handler (optional)
    if log_file:
        # Create logs directory if it doesn't exist
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
        
        # Use RotatingFileHandler to prevent log files from growing too large
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    # Set level for third-party libraries to ERROR to reduce noise
    logging.getLogger('werkzeug').setLevel(logging.ERROR)
    logging.getLogger('urllib3').setLevel(logging.ERROR)
    logging.getLogger('requests').setLevel(logging.ERROR)
    logging.getLogger('schedule').setLevel(logging.ERROR)
    logging.getLogger('pymongo').setLevel(logging.ERROR)
    logging.getLogger('redis').setLevel(logging.ERROR)
    
    # Log the configuration (only in debug mode to reduce startup noise)
    logger = logging.getLogger(__name__)
    logger.debug(f"Logging configured - Level: {logging.getLevelName(log_level)}, "
                f"Environment: {os.getenv('FLASK_ENV', 'production')}, "
                f"File: {log_file if log_file else 'Console only'}")


def get_logger(name):
    """
    Get a logger instance for a module.
    
    This is a convenience function that returns a logger with the given name.
    The logger will automatically use the centralized configuration set up by
    setup_logging().
    
    Args:
        name (str): Logger name (typically __name__)
    
    Returns:
        logging.Logger: Configured logger instance
    
    Example:
        logger = get_logger(__name__)
        logger.info("Module initialized")
        logger.error("An error occurred", exc_info=True)
    """
    return logging.getLogger(name)


def configure_flask_logging(app):
    """
    Configure Flask's built-in logging to use the centralized configuration.
    
    This function should be called after creating the Flask app instance.
    It ensures that Flask's request logging and error logging use the same
    format and level as the rest of the application.
    
    Args:
        app: Flask application instance
    
    Example:
        app = Flask(__name__)
        configure_flask_logging(app)
    """
    # Remove Flask's default handler
    if app.logger.handlers:
        app.logger.handlers.clear()
    
    # Get root logger handlers (set up by setup_logging)
    root_logger = logging.getLogger()
    
    # Add root logger handlers to Flask logger
    for handler in root_logger.handlers:
        app.logger.addHandler(handler)
    
    # Set Flask logger level
    app.logger.setLevel(get_log_level())
    
    # Disable Werkzeug's default request logging (we'll use our own)
    logging.getLogger('werkzeug').setLevel(logging.WARNING)


# Context manager for request logging
class RequestLogger:
    """
    Context manager for logging request/response cycles with timing.
    
    Usage:
        with RequestLogger(logger, request):
            # Process request
            pass
        # Automatically logs request details and duration
    """
    
    def __init__(self, logger, request, include_body=False):
        """
        Initialize request logger.
        
        Args:
            logger: Logger instance
            request: Flask request object
            include_body (bool): Whether to log request body (default: False)
        """
        self.logger = logger
        self.request = request
        self.include_body = include_body
        self.start_time = None
    
    def __enter__(self):
        self.start_time = datetime.now()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = (datetime.now() - self.start_time).total_seconds()
        
        # Build log message
        log_data = {
            'method': self.request.method,
            'path': self.request.path,
            'remote_addr': self.request.remote_addr,
            'duration_ms': round(duration * 1000, 2),
            'status': 'error' if exc_type else 'success'
        }
        
        # Add query parameters if present
        if self.request.args:
            log_data['query_params'] = dict(self.request.args)
        
        # Add request body if requested (be careful with sensitive data)
        if self.include_body and self.request.is_json:
            log_data['body'] = self.request.get_json()
        
        # Log at appropriate level
        if exc_type:
            self.logger.error(f"Request failed: {log_data}", exc_info=(exc_type, exc_val, exc_tb))
        else:
            self.logger.info(f"Request: {log_data}")
        
        return False  # Don't suppress exceptions

