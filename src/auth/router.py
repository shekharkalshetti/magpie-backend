"""
API Key management routes.

Handles listing, generation, and revocation of API keys.
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from src.auth import service
from src.auth.schemas import ApiKeyCreate, ApiKeyResponse, GeneratedApiKeyResponse
from src.database import get_db
from src.projects.dependencies import verify_project_access

router = APIRouter()


@router.get(
    "/projects/{project_id}/api-keys",
    response_model=list[ApiKeyResponse],
    summary="List API keys for a project",
    description="Get all API keys for a project (active and inactive). Requires user to have access to the project.",
)
async def list_api_keys(
    project_id: str = Depends(verify_project_access),
    db: Session = Depends(get_db),
):
    """
    List all API keys for a project.

    Requires authentication and project access.
    Returns masked keys for security - full keys are only shown once at creation.
    """
    api_keys = await service.list_api_keys(db, project_id)
    return [ApiKeyResponse.from_orm_model(key) for key in api_keys]


@router.post(
    "/projects/{project_id}/api-keys",
    response_model=GeneratedApiKeyResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate a new API key",
    description="Generate a new API key for a project. The full key is only returned once. Requires project access.",
)
async def create_api_key(
    key_data: ApiKeyCreate,
    project_id: str = Depends(verify_project_access),
    db: Session = Depends(get_db),
):
    """
    Generate a new API key for a project.

    Requires authentication and project access.
    IMPORTANT: The plaintext key is only returned once in this response.
    Store it securely - it cannot be retrieved later.
    """
    api_key, plaintext_key = await service.create_api_key(db, project_id, key_data)
    return GeneratedApiKeyResponse.from_orm_model(api_key, plaintext_key)


@router.delete(
    "/projects/{project_id}/api-keys/{key_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an API key",
    description="Permanently delete an API key. This action cannot be undone. Requires project access.",
)
async def delete_api_key(
    key_id: str,
    project_id: str = Depends(verify_project_access),
    db: Session = Depends(get_db),
):
    """
    Delete an API key.

    Requires authentication and project access.
    This immediately invalidates the key - any requests using it will fail.
    """
    await service.delete_api_key(db, project_id, key_id)
    return None
