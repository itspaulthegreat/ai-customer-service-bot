# src/utils/logger.py
import logging
import sys
from datetime import datetime
from typing import Optional

class Logger:
    """Enhanced logging for the AI customer service system"""
    
    def __init__(self, name: str, level: str = "INFO"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, level.upper()))
        
        # Remove existing handlers to avoid duplication
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        # Create console handler with custom formatting
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(getattr(logging, level.upper()))
        
        # Custom formatter with emojis and colors
        formatter = CustomFormatter()
        handler.setFormatter(formatter)
        
        self.logger.addHandler(handler)
    
    def info(self, message: str, extra: Optional[dict] = None):
        """Log info message"""
        self.logger.info(message, extra=extra or {})
    
    def error(self, message: str, extra: Optional[dict] = None):
        """Log error message"""
        self.logger.error(message, extra=extra or {})
    
    def warning(self, message: str, extra: Optional[dict] = None):
        """Log warning message"""
        self.logger.warning(message, extra=extra or {})
    
    def debug(self, message: str, extra: Optional[dict] = None):
        """Log debug message"""
        self.logger.debug(message, extra=extra or {})

class CustomFormatter(logging.Formatter):
    """Custom formatter with emojis and colors"""
    
    def __init__(self):
        super().__init__()
        
        # Color codes
        self.COLORS = {
            'DEBUG': '\033[36m',    # Cyan
            'INFO': '\033[32m',     # Green
            'WARNING': '\033[33m',  # Yellow
            'ERROR': '\033[31m',    # Red
            'CRITICAL': '\033[35m', # Magenta
            'RESET': '\033[0m'      # Reset
        }
        
        # Emojis for different log levels
        self.EMOJIS = {
            'DEBUG': '🔍',
            'INFO': '✅',
            'WARNING': '⚠️',
            'ERROR': '❌',
            'CRITICAL': '🚨'
        }
    
    def format(self, record):
        """Format log record with colors and emojis"""
        log_color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        emoji = self.EMOJIS.get(record.levelname, '📝')
        reset = self.COLORS['RESET']
        
        # Format timestamp
        timestamp = datetime.fromtimestamp(record.created).strftime('%H:%M:%S')
        
        # Create formatted message
        formatted = f"{log_color}{emoji} [{timestamp}] {record.name}: {record.getMessage()}{reset}"
        
        return formatted