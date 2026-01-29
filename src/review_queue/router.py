"""Review queue API endpoints for compliance oversight."""
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.database import get_db
from src.models import ProjectUser
from src.projects.dependencies import verify_project_access
from src.users.router import get_current_user_from_token
from src.users.schemas import UserResponse
from src.review_queue.service import ReviewQueueService
from src.review_queue.schemas import (
    ReviewQueueItemResponse,
    UpdateReviewItemRequest,
    ReviewQueueStatsResponse,
)

router = APIRouter(tags=["Review Queue"])


def _verify_item_access(
    item_id: UUID,
    current_user: UserResponse,
    db: Session,
) -> "ReviewQueueItem":
    """
    Helper to verify user has access to a review queue item.
    
    Returns the item if found and user has access.
    Raises HTTPException if item not found or user lacks access.
    """
    item = ReviewQueueService.get_review_item(db=db, item_id=item_id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review item not found",
        )

    # Verify user has access to the project
    project_user = (
        db.query(ProjectUser)
        .filter_by(user_id=current_user.id, project_id=item.project_id)
        .first()
    )

    if not project_user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User does not have access to this project",
        )

    return item


@router.get(
    "/projects/{project_id}/review-queue",
    response_model=dict,
    summary="Get review queue items",
    description="Get review queue items for a project with optional filtering",
)
async def get_review_queue(
    project_id: str = Depends(verify_project_access),
    db: Session = Depends(get_db),
    status_filter: Optional[str] = None,
    severity: Optional[str] = None,
    content_type: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
):
    """
    Get review queue items for a project.

    Requires user to be authenticated and have access to the project.
    Supports filtering by status (pending/approved/rejected),
    severity (low/medium/high/critical), and content_type (user_input/ai_output).

    Returns paginated list of review items.
    """
    items, total = ReviewQueueService.get_project_review_queue(
        db=db,
        project_id=project_id,
        status=status_filter,
        severity=severity,
        content_type=content_type,
        skip=skip,
        limit=limit,
    )

    return {
        "items": [ReviewQueueItemResponse.model_validate(item) for item in items],
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.get(
    "/projects/{project_id}/review-queue/stats",
    response_model=ReviewQueueStatsResponse,
    summary="Get review queue statistics",
    description="Get summary statistics for review queue",
)
async def get_review_queue_stats(
    project_id: str = Depends(verify_project_access),
    db: Session = Depends(get_db),
):
    """Get review queue statistics for a project."""
    stats = ReviewQueueService.get_stats(db=db, project_id=project_id)
    return ReviewQueueStatsResponse(**stats)


@router.get(
    "/review-queue/{item_id}",
    response_model=ReviewQueueItemResponse,
    summary="Get review queue item",
    description="Get a specific review queue item by ID",
)
async def get_review_item(
    item_id: str,
    current_user: UserResponse = Depends(get_current_user_from_token),
    db: Session = Depends(get_db),
):
    """Get a specific review queue item."""
    try:
        item_uuid = UUID(item_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid item_id format",
        )

    item = _verify_item_access(item_uuid, current_user, db)
    return ReviewQueueItemResponse.model_validate(item)


@router.patch(
    "/review-queue/{item_id}",
    response_model=ReviewQueueItemResponse,
    summary="Update review queue item",
    description="Update review status and add notes for a review item",
)
async def update_review_item(
    item_id: str,
    request: UpdateReviewItemRequest,
    current_user: UserResponse = Depends(get_current_user_from_token),
    db: Session = Depends(get_db),
):
    """
    Update a review queue item with decision and notes.

    Transitions status from pending → approved/rejected.
    Records reviewer information and timestamp.
    """
    try:
        item_uuid = UUID(item_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid item_id format",
        )

    # Verify access and get the item
    item = _verify_item_access(item_uuid, current_user, db)

    # Validate status
    valid_statuses = ["pending", "approved", "rejected"]
    if request.status not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}",
        )

    # Update the item
    updated_item = ReviewQueueService.update_review_item(
        db=db,
        item_id=item_uuid,
        status=request.status,
        notes=request.notes,
        reviewed_by_user_id=current_user.id,
    )

    if not updated_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review item not found",
        )

    return ReviewQueueItemResponse.model_validate(updated_item)
