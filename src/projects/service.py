"""
Project business logic service.

Contains core business logic for project and metadata key operations.
"""

from typing import Any

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.models import MetadataKey, MetadataType, Project
from src.projects.exceptions import (
    MetadataKeyExistsError,
    ProjectNameExistsError,
    ProjectNotFoundError,
)
from src.projects.schemas import MetadataKeyCreate, ProjectCreate, ProjectUpdate


async def create_project(db: Session, data: ProjectCreate) -> Project:
    """
    Create a new project.

    Args:
        db: Database session
        data: Project creation data

    Returns:
        Created Project object

    Raises:
        ProjectNameExistsError: If project name already exists
    """
    # Check if name already exists
    existing = db.query(Project).filter(Project.name == data.name).first()
    if existing:
        raise ProjectNameExistsError(data.name)

    project = Project(
        name=data.name,
        description=data.description,
    )

    db.add(project)
    db.commit()
    db.refresh(project)

    return project


async def get_project(db: Session, project_id: str) -> Project | None:
    """
    Get a project by ID.

    Args:
        db: Database session
        project_id: Project ID

    Returns:
        Project if found, None otherwise
    """
    return db.query(Project).filter(Project.id == project_id).first()


async def list_projects(db: Session, skip: int = 0, limit: int = 100) -> list[Project]:
    """
    List all projects with pagination.

    Args:
        db: Database session
        skip: Number of records to skip
        limit: Maximum number of records to return

    Returns:
        List of Project objects
    """
    return db.query(Project).offset(skip).limit(limit).all()


async def update_project(db: Session, project_id: str, data: ProjectUpdate) -> Project:
    """
    Update a project.

    Args:
        db: Database session
        project_id: Project ID to update
        data: Project update data

    Returns:
        Updated Project object

    Raises:
        ProjectNotFoundError: If project doesn't exist
        ProjectNameExistsError: If new name already exists
    """
    project = db.query(Project).filter(Project.id == project_id).first()

    if not project:
        raise ProjectNotFoundError(project_id)

    # Check if new name already exists (if name is being updated)
    if data.name and data.name != project.name:
        existing = db.query(Project).filter(Project.name == data.name).first()
        if existing:
            raise ProjectNameExistsError(data.name)

    # Update fields
    if data.name is not None:
        project.name = data.name
    if data.description is not None:
        project.description = data.description

    db.commit()
    db.refresh(project)

    return project


async def delete_project(db: Session, project_id: str) -> None:
    """
    Delete a project and all associated data.

    Args:
        db: Database session
        project_id: Project ID to delete

    Raises:
        ProjectNotFoundError: If project doesn't exist
    """
    project = db.query(Project).filter(Project.id == project_id).first()

    if not project:
        raise ProjectNotFoundError(project_id)

    db.delete(project)
    db.commit()


async def create_metadata_key(
    db: Session,
    project_id: str,
    data: MetadataKeyCreate,
) -> MetadataKey:
    """
    Create a new metadata key for a project.

    Args:
        db: Database session
        project_id: Project ID
        data: Metadata key creation data

    Returns:
        Created MetadataKey object

    Raises:
        ProjectNotFoundError: If project doesn't exist
        MetadataKeyExistsError: If key already exists for project
    """
    # Verify project exists
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise ProjectNotFoundError(project_id)

    metadata_key = MetadataKey(
        project_id=project_id,
        key=data.key,
        description=data.description,
        required=data.required,
        value_type=data.value_type,
        enum_values=data.enum_values,
    )

    try:
        db.add(metadata_key)
        db.commit()
        db.refresh(metadata_key)
    except IntegrityError:
        db.rollback()
        raise MetadataKeyExistsError(data.key, project_id)

    return metadata_key


async def list_metadata_keys(db: Session, project_id: str) -> list[MetadataKey]:
    """
    List all metadata keys for a project.

    Args:
        db: Database session
        project_id: Project ID

    Returns:
        List of MetadataKey objects

    Raises:
        ProjectNotFoundError: If project doesn't exist
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise ProjectNotFoundError(project_id)

    return (
        db.query(MetadataKey)
        .filter(MetadataKey.project_id == project_id)
        .order_by(MetadataKey.created_at)
        .all()
    )


def get_metadata_schema(db: Session, project_id: str) -> dict[str, Any]:
    """
    Get the metadata schema for a project.

    Returns a dictionary describing all configured metadata keys.
    Useful for SDK clients to know what metadata is expected.

    Args:
        db: Database session
        project_id: Project ID

    Returns:
        Schema dictionary with key definitions
    """
    keys = db.query(MetadataKey).filter(
        MetadataKey.project_id == project_id).all()

    schema = {}
    for key in keys:
        schema[key.key] = {
            "description": key.description,
            "required": key.required,
            "value_type": key.value_type.value,
            "enum_values": key.enum_values if key.value_type == MetadataType.ENUM else None,
        }

    return schema
