"""
Authentication constants and error codes.
"""


class ErrorCode:
    """Error codes for authentication failures."""

    MISSING_API_KEY = "MISSING_API_KEY"
    INVALID_API_KEY = "INVALID_API_KEY"
    INACTIVE_API_KEY = "INACTIVE_API_KEY"
    INVALID_AUTH_HEADER = "INVALID_AUTH_HEADER"


# Paths that don't require authentication
PUBLIC_PATHS = {
    "/",
    "/health",
    "/docs",
    "/redoc",
    "/openapi.json",
    "/api/v1/auth/login",
    "/api/v1/auth/signup",
}

# Path prefixes that don't require authentication
PUBLIC_PREFIXES = [
    # All API endpoints require authentication
    # Team management, project operations, etc. are protected
]
