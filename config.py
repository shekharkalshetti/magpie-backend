"""
Configuration management for the Triton backend.

DEPRECATED: This file is kept for backward compatibility.
The new configuration is in src/config.py.

Import from src.config instead:
    from src.config import settings
"""
# Re-export from new location for backward compatibility
from src.config import settings, Settings, BACKEND_DIR, ENV_FILE

__all__ = ["settings", "Settings", "BACKEND_DIR", "ENV_FILE"]
