"""
Project management routes.

Handles creation, listing, and management of projects and metadata keys.
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from src.database import get_db
from src.models import Project
from src.projects import service
from src.projects.dependencies import valid_project_id
from src.projects.schemas import (
    MetadataKeyCreate,
    MetadataKeyResponse,
    ProjectCreate,
    ProjectUpdate,
    ProjectResponse,
)

router = APIRouter()


# ============================================================================
# Project Endpoints
# ============================================================================


@router.post(
    "/",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new project",
    description="Create a new project. Returns the project_id needed for API key generation.",
)
async def create_project(
    project_data: ProjectCreate,
    db: Session = Depends(get_db),
):
    """
    Create a new project.

    Returns the project_id which is needed for API key generation.
    This endpoint does not require authentication.
    """
    project = await service.create_project(db, project_data)
    return ProjectResponse.from_orm_model(project)


@router.get(
    "/",
    response_model=list[ProjectResponse],
    summary="List all projects",
    description="List all projects with pagination support.",
)
async def list_projects(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
):
    """
    List all projects.

    Supports pagination via skip/limit query parameters.
    This endpoint does not require authentication.
    """
    projects = await service.list_projects(db, skip=skip, limit=limit)
    return [ProjectResponse.from_orm_model(p) for p in projects]


@router.get(
    "/{project_id}",
    response_model=ProjectResponse,
    summary="Get a project by ID",
)
async def get_project(
    project: Project = Depends(valid_project_id),
):
    """Get a specific project by ID."""
    return ProjectResponse.from_orm_model(project)


@router.patch(
    "/{project_id}",
    response_model=ProjectResponse,
    summary="Update a project",
    description="Update project name or description.",
)
async def update_project(
    project_id: str,
    project_data: ProjectUpdate,
    db: Session = Depends(get_db),
):
    """
    Update a project's name or description.

    At least one field must be provided.
    """
    project = await service.update_project(db, project_id, project_data)
    return ProjectResponse.from_orm_model(project)


@router.delete(
    "/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a project",
    description="Delete a project and all associated data (cascades to API keys, metadata, and logs).",
)
async def delete_project(
    project_id: str,
    db: Session = Depends(get_db),
):
    """
    Delete a project and all associated data.

    WARNING: This cascades to all metadata keys, API keys, and execution logs.
    """
    await service.delete_project(db, project_id)
    return None


# ============================================================================
# Metadata Key Endpoints
# ============================================================================


@router.post(
    "/{project_id}/metadata-keys",
    response_model=MetadataKeyResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a metadata key",
    description="Create a new metadata key for a project. Metadata keys define valid fields for execution logs.",
)
async def create_metadata_key(
    project_id: str,
    metadata_data: MetadataKeyCreate,
    db: Session = Depends(get_db),
):
    """
    Create a new metadata key for a project.

    Metadata keys define what fields are valid/required when logging executions.
    Supports typed fields: string, int, bool, enum.

    Example keys:
    - user_id (string)
    - retry_count (int)
    - is_production (bool)
    - environment (enum with values: ["dev", "staging", "prod"])
    """
    metadata_key = await service.create_metadata_key(db, project_id, metadata_data)
    return metadata_key


@router.get(
    "/{project_id}/metadata-keys",
    response_model=list[MetadataKeyResponse],
    summary="List metadata keys",
    description="List all metadata keys configured for a project.",
)
async def list_metadata_keys(
    project_id: str,
    db: Session = Depends(get_db),
):
    """
    List all metadata keys for a project.

    Returns the complete metadata schema configuration for the project.
    """
    return await service.list_metadata_keys(db, project_id)
