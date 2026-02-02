#!/usr/bin/env python3

import os
from typing import Optional

class Config:
    """Centralized configuration management"""
    
    # API Configuration
    API_TOKEN: str = os.getenv('API_TOKEN', 'mobile-scraper-2026-secure-token')
    API_HOST: str = os.getenv('API_HOST', '0.0.0.0')
    API_PORT: int = int(os.getenv('API_PORT', '8000'))
    
    # Database Configuration
    DB_URL: str = os.getenv('DB_URL', 'postgresql://scraper:scraper123@localhost/mobile_scraper')
    
    # Scraper Configuration
    SCRAPER_DELAY: int = int(os.getenv('SCRAPER_DELAY', '2'))
    MAX_PAGES: int = int(os.getenv('MAX_PAGES', '10'))
    HEADLESS_MODE: bool = os.getenv('HEADLESS_MODE', 'true').lower() == 'true'
    
    # Logging Configuration
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')
    LOG_DIR: str = os.getenv('LOG_DIR', './logs')
    
    # Chrome Configuration
    CHROME_BINARY_PATH: Optional[str] = os.getenv('CHROME_BINARY_PATH')
    CHROMEDRIVER_PATH: Optional[str] = os.getenv('CHROMEDRIVER_PATH')
    
    @classmethod
    def validate(cls) -> bool:
        """Validate configuration"""
        required_vars = ['DB_URL', 'API_TOKEN']
        missing = [var for var in required_vars if not getattr(cls, var)]
        if missing:
            raise ValueError(f"Missing required environment variables: {missing}")
        return True

# Validate configuration on import
Config.validate()
