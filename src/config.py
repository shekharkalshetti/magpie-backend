"""
Global configuration management for the Magpie backend.

Uses pydantic-settings for environment variable handling with validation.
"""

import json
from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from src.constants import Environment

# Get the backend directory path
BACKEND_DIR = Path(__file__).parent.parent
ENV_FILE = BACKEND_DIR / ".env"


class Settings(BaseSettings):
    """
    Global application settings.

    These are loaded from environment variables and/or .env file.
    Module-specific settings should be defined in their respective config.py files.
    """

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # Application
    DEBUG: bool = False
    ENVIRONMENT: Environment = Environment.DEVELOPMENT
    APP_VERSION: str = "0.2.0"

    # Database (Supabase PostgreSQL)
    DATABASE_URL: str
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20

    # Security
    SECRET_KEY: str = ""  # For signing tokens if needed
    API_KEY_HEADER: str = "X-API-Key"

    # CORS
    ALLOWED_ORIGINS: list[str] = ["http://localhost:3000"]

    # Logging
    LOG_LEVEL: str = "INFO"

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_allowed_origins(cls, v):
        """Parse ALLOWED_ORIGINS from JSON array string, comma-separated string, or list."""
        if isinstance(v, str):
            # Try parsing as JSON array first
            if v.strip().startswith("["):
                try:
                    return json.loads(v)
                except json.JSONDecodeError:
                    pass
            # Fall back to comma-separated
            return [origin.strip() for origin in v.split(",")]
        return v


settings = Settings()
