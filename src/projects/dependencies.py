"""
Project dependencies for validation.

Provides reusable dependencies for project validation in routes.
"""

from fastapi import Depends
from sqlalchemy.orm import Session

from src.database import get_db
from src.models import Project
from src.projects.exceptions import ProjectNotFoundError


async def valid_project_id(
    project_id: str,
    db: Session = Depends(get_db),
) -> Project:
    """
    Validate that a project exists and return it.

    Use this dependency in routes that need to validate project existence.

    Args:
        project_id: The project ID from the path
        db: Database session

    Returns:
        The Project object if found

    Raises:
        ProjectNotFoundError: If project doesn't exist

    Example:
        @router.get("/projects/{project_id}")
        async def get_project(project: Project = Depends(valid_project_id)):
            return project
    """
    project = db.query(Project).filter(Project.id == project_id).first()

    if not project:
        raise ProjectNotFoundError(project_id)

    return project
