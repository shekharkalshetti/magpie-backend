"""
Global constants and enums for the Triton backend.
"""

from enum import Enum


class Environment(str, Enum):
    """Application environment types."""

    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    LOCAL = "local"


# Environments where API docs should be shown
SHOW_DOCS_ENVIRONMENTS = (Environment.LOCAL, Environment.DEVELOPMENT, Environment.STAGING)
