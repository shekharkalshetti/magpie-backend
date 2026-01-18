"""
Authentication configuration.

Module-specific settings for authentication.
Re-exports from global config for convenience.
"""

from src.config import settings

# Re-export auth-related settings for convenience
API_KEY_HEADER = settings.API_KEY_HEADER
SECRET_KEY = settings.SECRET_KEY

# Module-specific constants
API_KEY_PREFIX = "tr"
API_KEY_LENGTH = 32
