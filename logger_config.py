"""Logging configuration for Zimbra migration."""

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path


class LoggerConfig:
    """Configure logging for the application."""
    
    LOG_LEVELS = {
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'DEBUG': logging.DEBUG,
        'ERROR': logging.ERROR,
    }
    
    @classmethod
    def setup_logger(cls, log_level: str = 'INFO', 
                     log_file: str = 'activity-migration.log') -> logging.Logger:
        """Setup and configure logger.
        
        Args:
            log_level: Logging level (INFO, WARNING, DEBUG, ERROR)
            log_file: Path to log file
            
        Returns:
            Configured logger instance
        """
        logger = logging.getLogger('zimbra_migration')
        logger.setLevel(cls.LOG_LEVELS.get(log_level, logging.INFO))
        
        # Avoid duplicate handlers
        if logger.handlers:
            return logger
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s :: %(levelname)s :: %(message)s'
        )
        
        # File handler
        file_handler = RotatingFileHandler(
            log_file, mode='a', maxBytes=1000000, backupCount=10
        )
        file_handler.setLevel(cls.LOG_LEVELS.get(log_level, logging.INFO))
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        # Stream handler
        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(cls.LOG_LEVELS.get(log_level, logging.INFO))
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)
        
        return logger