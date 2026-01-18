"""
Authentication dependencies for FastAPI routes.

Provides reusable dependencies for API key validation.
"""

from datetime import datetime
from typing import Any

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from src.auth.exceptions import InvalidApiKeyError, MissingApiKeyError
from src.auth.utils import extract_bearer_token, hash_api_key
from src.database import get_db


async def get_api_key_from_header(request: Request) -> str:
    """
    Extract API key from Authorization header.

    Args:
        request: FastAPI request object

    Returns:
        The extracted API key

    Raises:
        MissingApiKeyError: If no valid API key is found
    """
    authorization = request.headers.get("authorization")
    api_key = extract_bearer_token(authorization)

    if not api_key:
        raise MissingApiKeyError()

    return api_key


async def get_current_project_id(
    request: Request,
    api_key: str = Depends(get_api_key_from_header),
    db: Session = Depends(get_db),
) -> str:
    """
    Validate API key and return the associated project ID.

    This dependency validates the API key and returns the project_id.
    Use this for routes that need authentication.

    Args:
        request: FastAPI request object
        api_key: API key from header
        db: Database session

    Returns:
        The project_id associated with the API key

    Raises:
        InvalidApiKeyError: If API key is invalid or inactive
    """
    # Import from central models to ensure all models are loaded
    from src.models import ApiKey

    key_hash = hash_api_key(api_key)

    api_key_record = (
        db.query(ApiKey)
        .filter(
            ApiKey.key_hash == key_hash,
            ApiKey.is_active,
        )
        .first()
    )

    if not api_key_record:
        raise InvalidApiKeyError()

    # Update last_used_at timestamp
    api_key_record.last_used_at = datetime.utcnow()
    db.commit()

    # Store in request state for access by other components
    request.state.project_id = api_key_record.project_id
    request.state.api_key_id = api_key_record.id

    return api_key_record.project_id


async def get_current_api_key_record(
    api_key: str = Depends(get_api_key_from_header),
    db: Session = Depends(get_db),
) -> Any:
    """
    Get the full API key record.

    Use this when you need access to the full API key record,
    not just the project_id.
    """
    from src.models import ApiKey

    key_hash = hash_api_key(api_key)

    api_key_record = (
        db.query(ApiKey)
        .filter(
            ApiKey.key_hash == key_hash,
            ApiKey.is_active,
        )
        .first()
    )

    if not api_key_record:
        raise InvalidApiKeyError()

    return api_key_record
