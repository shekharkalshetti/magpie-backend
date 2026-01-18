"""
Authentication exceptions.
"""

from src.exceptions import UnauthorizedError


class MissingApiKeyError(UnauthorizedError):
    """Raised when API key is not provided."""

    def __init__(self):
        super().__init__(
            detail="Missing or invalid Authorization header. Expected: Bearer <api_key>"
        )


class InvalidApiKeyError(UnauthorizedError):
    """Raised when API key is invalid or inactive."""

    def __init__(self):
        super().__init__(detail="Invalid or inactive API key")

class AuthenticationError(UnauthorizedError):
    """Raised for user authentication errors."""

    def __init__(self, detail: str = "Authentication failed"):
        super().__init__(detail=detail)