"""
Global exceptions for the Triton backend.

Base exception classes that module-specific exceptions can inherit from.
"""

from fastapi import HTTPException, status


class TritonException(HTTPException):
    """Base exception for all Triton-specific HTTP errors."""

    def __init__(
        self,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail: str = "An error occurred",
        headers: dict | None = None,
    ):
        super().__init__(status_code=status_code, detail=detail, headers=headers)


class NotFoundError(TritonException):
    """Resource not found error."""

    def __init__(self, resource: str, identifier: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{resource} '{identifier}' not found",
        )


class ConflictError(TritonException):
    """Resource conflict error (e.g., duplicate)."""

    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail,
        )


class UnauthorizedError(TritonException):
    """Authentication required or failed."""

    def __init__(self, detail: str = "Authentication required"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )


class ForbiddenError(TritonException):
    """Access forbidden."""

    def __init__(self, detail: str = "Access forbidden"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
        )
