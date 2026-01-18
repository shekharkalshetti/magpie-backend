"""
API Key and JWT authentication middleware for Triton backend.

Extracts and validates API keys and JWT tokens from Authorization header.
API keys are hashed before database lookup for security.
JWT tokens are verified using the secret key.
"""

from datetime import datetime

from fastapi import Request, status, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from starlette.middleware.base import BaseHTTPMiddleware

from src.auth.constants import PUBLIC_PATHS, PUBLIC_PREFIXES
from src.auth.utils import extract_bearer_token, hash_api_key, verify_jwt_token
from src.config import settings
from src.database import SessionLocal


# ============================================================================
# FastAPI Dependency
# ============================================================================

async def get_current_user_id(request: Request) -> str:
    """
    FastAPI dependency to get the current authenticated user ID.

    The middleware must have already attached user_id to request.state.
    This dependency extracts it for use in route handlers.

    Raises:
        HTTPException: If user_id is not set in request state
    """
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        from fastapi.exceptions import HTTPException
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User ID not found in request state",
        )
    return user_id


# ============================================================================
# Middleware Class
# ============================================================================


class ApiKeyMiddleware(BaseHTTPMiddleware):
    """
    Middleware that validates API keys and JWT tokens, attaching project_id to request state.

    Behavior:
    - Extracts Authorization: Bearer <token> header
    - Tries to validate as JWT token first (for user/portal auth)
    - Falls back to API key validation (for SDK auth)
    - Attaches project_id to request.state
    - Returns 401 for missing or invalid credentials

    Public endpoints (health checks, docs, project management, auth) are exempt from authentication.
    """

    async def dispatch(self, request: Request, call_next):
        """Process the request and validate API key or JWT."""
        # Allow CORS preflight requests through without auth
        if request.method == "OPTIONS":
            return await call_next(request)

        # Skip authentication for public paths
        if request.url.path in PUBLIC_PATHS:
            return await call_next(request)

        # Skip authentication for public path prefixes
        for prefix in PUBLIC_PREFIXES:
            if request.url.path.startswith(prefix):
                return await call_next(request)
        # Extract token from Authorization header
        authorization = request.headers.get("authorization")
        token = extract_bearer_token(authorization)

        if not token:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "detail": "Missing or invalid Authorization header. Expected: Bearer <token>"
                },
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Try JWT token first (for user/portal auth)
        payload = verify_jwt_token(token, settings.SECRET_KEY)
        if payload:
            # JWT token is valid - get user's project from request params or body
            # For now, attach user_id and let the endpoint handler determine the project
            request.state.user_id = payload.get("user_id")
            request.state.auth_type = "jwt"
            return await call_next(request)

        # Fall back to API key validation (for SDK auth)
        key_hash = hash_api_key(token)

        # Look up API key in database
        db: Session = SessionLocal()
        try:
            # Import from central models to ensure all models are loaded
            from src.models import ApiKey, ProjectUser

            api_key_record = (
                db.query(ApiKey)
                .filter(
                    ApiKey.key_hash == key_hash,
                    ApiKey.is_active,
                )
                .first()
            )

            if not api_key_record:
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": "Invalid or inactive credentials"},
                    headers={"WWW-Authenticate": "Bearer"},
                )

            # Get the first user/owner of this project for audit logging
            project_user = (
                db.query(ProjectUser)
                .filter(ProjectUser.project_id == api_key_record.project_id)
                .first()
            )

            # Attach project_id to request state for API key auth
            request.state.project_id = api_key_record.project_id
            request.state.api_key_id = api_key_record.id
            request.state.auth_type = "api_key"
            # Set user_id from the project owner/member for audit logging
            if project_user:
                request.state.user_id = project_user.user_id

            # Update last_used_at timestamp
            api_key_record.last_used_at = datetime.utcnow()
            db.commit()

        finally:
            db.close()

        # Continue processing request
        response = await call_next(request)
        return response
