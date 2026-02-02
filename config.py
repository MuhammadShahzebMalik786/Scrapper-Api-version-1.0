#!/usr/bin/env python3
"""
DEPRECATED: Use config_manager.py instead.
This file is kept for backward compatibility only.
"""

# For backward compatibility, import from config_manager
from config_manager import Config

__all__ = ['Config']
    def validate(cls) -> bool:
        """Validate configuration"""
        required_vars = ['DB_URL', 'API_TOKEN']
        missing = [var for var in required_vars if not getattr(cls, var)]
        if missing:
            raise ValueError(f"Missing required environment variables: {missing}")
        return True

# Validate configuration on import
Config.validate()
