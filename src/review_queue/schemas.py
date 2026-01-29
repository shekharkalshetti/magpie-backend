"""Schemas for ReviewQueue API requests and responses."""
from datetime import datetime
from typing import Optional, List
from enum import Enum
from pydantic import BaseModel, ConfigDict, Field


class ReviewStatus(str, Enum):
    """Valid review statuses."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class ReviewQueueItemResponse(BaseModel):
    """Review queue item response."""

    id: str
    execution_log_id: str
    project_id: str
    content_type: str  # user_input or ai_output
    content_text: str
    severity: str  # low, medium, high, critical
    flagged_policies: Optional[List[str]] = None
    violation_reasons: Optional[dict] = None
    status: str  # pending, approved, rejected
    reviewed_by_user_id: Optional[str] = None
    review_notes: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UpdateReviewItemRequest(BaseModel):
    """Request to update a review queue item."""

    status: ReviewStatus
    notes: Optional[str] = None


class ReviewQueueListResponse(BaseModel):
    """Paginated list of review queue items."""
    
    items: List[ReviewQueueItemResponse]
    total: int
    skip: int = Field(ge=0)
    limit: int = Field(ge=1)


class ReviewQueueStatsResponse(BaseModel):
    """Review queue statistics response."""

    total: int
    pending: int
    approved: int
    rejected: int
