"""
Project dependencies for validation.

Provides reusable dependencies for project validation in routes.
"""

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.database import get_db
from src.models import Project, ProjectUser
from src.projects.exceptions import ProjectNotFoundError
from src.users.router import get_current_user_from_token
from src.users.schemas import UserResponse


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


async def verify_project_access(
    project_id: str,
    current_user: UserResponse = Depends(get_current_user_from_token),
    db: Session = Depends(get_db),
) -> str:
    """
    Verify that the current user has access to a project.

    Use this dependency in routes that need to validate user access to a project.

    Args:
        project_id: The project ID from the path
        current_user: Current authenticated user
        db: Database session

    Returns:
        The project_id if user has access

    Raises:
        HTTPException: 403 if user doesn't have access to the project

    Example:
        @router.get("/projects/{project_id}/data")
        async def get_data(
            project_id: str = Depends(verify_project_access),
            db: Session = Depends(get_db)
        ):
            return {"data": "..."}
    """
    project_user = (
        db.query(ProjectUser)
        .filter_by(user_id=current_user.id, project_id=project_id)
        .first()
    )

    if not project_user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User does not have access to this project",
        )

    return project_id
