"""
Centralized Logging System for Hyderabad Chatbot
Provides structured logging with file rotation and different log levels
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
from logging.handlers import RotatingFileHandler
from typing import Optional


class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors for console output"""
    
    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m'        # Reset
    }
    
    def format(self, record):
        # Add color to level name
        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname = f"{self.COLORS[levelname]}{levelname}{self.COLORS['RESET']}"
        
        return super().format(record)


def setup_logger(
    name: str,
    log_file: Optional[str] = None,
    level: int = logging.INFO,
    console_output: bool = True,
    max_bytes: int = 10485760,  # 10MB
    backup_count: int = 5
) -> logging.Logger:
    """
    Set up a logger with both console and file handlers.
    
    Args:
        name: Logger name (typically module name)
        log_file: Optional log file name (stored in logs/ directory)
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        console_output: Whether to output to console
        max_bytes: Max size of log file before rotation (default 10MB)
        backup_count: Number of backup files to keep
    
    Returns:
        Configured logger instance
    
    Example:
        >>> from services.logger import setup_logger
        >>> logger = setup_logger('news', 'news.log')
        >>> logger.info("Fetched 10 articles")
        >>> logger.error("API failed", exc_info=True)
    """
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Prevent duplicate handlers if logger already exists
    if logger.handlers:
        return logger
    
    # Console Handler (with colors)
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        
        console_formatter = ColoredFormatter(
            '%(levelname)s | %(name)s | %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
    
    # File Handler (with rotation)
    if log_file:
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        file_handler = RotatingFileHandler(
            log_dir / log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)  # File gets everything
        
        file_formatter = logging.Formatter(
            '%(asctime)s | %(name)s | %(levelname)s | %(funcName)s:%(lineno)d | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get an existing logger or create a basic one.
    
    Args:
        name: Logger name
    
    Returns:
        Logger instance
    
    Example:
        >>> from services.logger import get_logger
        >>> logger = get_logger(__name__)
        >>> logger.info("Processing request")
    """
    logger = logging.getLogger(name)
    
    # If logger has no handlers, set up a basic console logger
    if not logger.handlers:
        return setup_logger(name, console_output=True)
    
    return logger


class LogContext:
    """Context manager for temporary log level changes"""
    
    def __init__(self, logger: logging.Logger, level: int):
        self.logger = logger
        self.new_level = level
        self.old_level = logger.level
    
    def __enter__(self):
        self.logger.setLevel(self.new_level)
        return self.logger
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.logger.setLevel(self.old_level)


# Convenience function for debugging
def enable_debug_logging():
    """Enable DEBUG level for all loggers"""
    logging.getLogger().setLevel(logging.DEBUG)
    for handler in logging.getLogger().handlers:
        handler.setLevel(logging.DEBUG)


def disable_debug_logging():
    """Reset to INFO level"""
    logging.getLogger().setLevel(logging.INFO)
    for handler in logging.getLogger().handlers:
        handler.setLevel(logging.INFO)


# Example usage and testing
if __name__ == "__main__":
    # Test the logger
    logger = setup_logger('test', 'test.log', level=logging.DEBUG)
    
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    logger.critical("This is a critical message")
    
    # Test with exception
    try:
        raise ValueError("Test exception")
    except Exception as e:
        logger.error("Caught exception", exc_info=True)
    
    print("\n✅ Logger test complete! Check logs/test.log")