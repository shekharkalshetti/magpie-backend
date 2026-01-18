"""
Policy dependencies for FastAPI routes.
"""

from fastapi import Depends, HTTPException, Path, status
from sqlalchemy.orm import Session

from src.database import get_db
from src.policies.models import Policy
from src.policies.service import get_policy, get_policy_by_project


async def valid_policy_id(
    policy_id: str = Path(..., description="Policy ID"),
    db: Session = Depends(get_db),
) -> Policy:
    """
    Dependency to validate and retrieve a policy by ID.

    Args:
        policy_id: Policy ID from path parameter
        db: Database session

    Returns:
        Policy if found

    Raises:
        HTTPException: 404 if policy not found
    """
    policy = await get_policy(db, policy_id)
    if not policy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Policy with ID '{policy_id}' not found",
        )
    return policy


async def valid_project_policy(
    project_id: str = Path(..., description="Project ID"),
    db: Session = Depends(get_db),
) -> Policy | None:
    """
    Dependency to retrieve a policy by project ID.

    Args:
        project_id: Project ID from path parameter
        db: Database session

    Returns:
        Policy if found, None otherwise
    """
    return await get_policy_by_project(db, project_id)
