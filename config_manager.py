#!/usr/bin/env python3
"""
Centralized configuration management with environment variable support.
Addresses security concerns by avoiding hard-coded credentials.
"""

import os
import logging
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)

class Config:
    """Production-ready configuration management"""
    
    # API Configuration
    API_TOKEN: str = os.getenv('API_TOKEN', '')
    if not API_TOKEN:
        logger.warning("API_TOKEN not set! Please set it in .env file")
        API_TOKEN = 'change-me-in-production'
    
    API_HOST: str = os.getenv('API_HOST', '0.0.0.0')
    API_PORT: int = int(os.getenv('API_PORT', '8000'))
    
    # Database Configuration
    DB_URL: str = os.getenv('DB_URL', 'postgresql://scraper:scraper123@localhost/mobile_scraper')
    DB_POOL_SIZE: int = int(os.getenv('DB_POOL_SIZE', '10'))
    DB_MAX_OVERFLOW: int = int(os.getenv('DB_MAX_OVERFLOW', '20'))
    
    # Scraper Configuration
    SCRAPER_DELAY: int = int(os.getenv('SCRAPER_DELAY', '2'))
    MAX_PAGES: int = int(os.getenv('MAX_PAGES', '10'))
    HEADLESS_MODE: bool = os.getenv('HEADLESS_MODE', 'true').lower() == 'true'
    WORKER_INTERVAL_HOURS: int = int(os.getenv('WORKER_INTERVAL_HOURS', '6'))
    
    # Logging Configuration
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')
    LOG_DIR: str = os.getenv('LOG_DIR', './logs')
    
    # Chrome Configuration
    CHROME_BINARY_PATH: Optional[str] = os.getenv('CHROME_BINARY_PATH')
    CHROMEDRIVER_PATH: Optional[str] = os.getenv('CHROMEDRIVER_PATH')
    
    # Deployment Environment
    ENVIRONMENT: str = os.getenv('ENVIRONMENT', 'development')
    DEBUG: bool = ENVIRONMENT == 'development'
    
    @classmethod
    def get_db_pool_settings(cls):
        """Get database pool settings for production"""
        if cls.ENVIRONMENT == 'production':
            return {
                'poolclass': 'QueuePool',
                'pool_size': cls.DB_POOL_SIZE,
                'max_overflow': cls.DB_MAX_OVERFLOW,
                'pool_pre_ping': True,
                'pool_recycle': 3600
            }
        return {}
    
    @classmethod
    def validate_production(cls):
        """Validate configuration for production deployment"""
        issues = []
        
        if cls.API_TOKEN == 'change-me-in-production':
            issues.append("API_TOKEN not changed from default")
        
        if cls.ENVIRONMENT == 'production':
            if 'localhost' in cls.DB_URL:
                issues.append("Database URL contains localhost in production")
            if 'scraper123' in cls.DB_URL:
                issues.append("Default database password detected in production")
        
        return issues
