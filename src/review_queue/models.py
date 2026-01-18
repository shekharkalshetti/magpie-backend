"""
ReviewQueue model for compliance tracking and content moderation oversight.

Tracks flagged content (user input and AI output) for human review and approval.
"""
from datetime import datetime
from enum import Enum as PyEnum
from uuid import uuid4

from sqlalchemy import Column, String, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship

from src.database import Base


class ContentType(str, PyEnum):
    """Type of content being reviewed."""
    USER_INPUT = "user_input"
    AI_OUTPUT = "ai_output"


class ReviewStatus(str, PyEnum):
    """Status of the review."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class ModerationSeverity(str, PyEnum):
    """Severity level of moderation flag."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ReviewQueue(Base):
    """
    Review queue item for compliance oversight.
    
    Stores flagged content (user input or AI output) that needs human review.
    Provides immutable audit trail of all review decisions.
    """
    __tablename__ = "review_queue"

    # Primary key
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))

    # References - use String like other models
    execution_log_id = Column(
        String,
        ForeignKey("execution_logs.id"),
        nullable=False,
        index=True
    )
    project_id = Column(
        String,
        ForeignKey("projects.id"),
        nullable=False,
        index=True
    )

    # Content being reviewed
    content_type = Column(
        String,  # Store as string instead of native ENUM
        nullable=False,
        index=True
    )
    content_text = Column(String, nullable=False)

    # Moderation findings
    severity = Column(
        String,  # Store as string instead of native ENUM
        nullable=False,
        index=True
    )
    flagged_policies = Column(
        JSON,
        nullable=True,
        default=list
    )  # List of policy names that were violated
    violation_reasons = Column(
        JSON,
        nullable=True,
        default=dict
    )  # Detailed reasons per policy

    # Review status and decision
    status = Column(
        String,  # Store as string instead of native ENUM
        nullable=False,
        default="pending",  # Use string default
        index=True
    )
    reviewed_by_user_id = Column(
        String,
        ForeignKey("users.id"),
        nullable=True,
        index=True
    )
    review_notes = Column(String, nullable=True)
    reviewed_at = Column(DateTime, nullable=True)

    # Audit trail
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    execution_log = relationship("ExecutionLog", backref="review_items")
    project = relationship("Project", backref="review_queue_items")
    reviewed_by = relationship("User", backref="review_actions")

    def __repr__(self):
        return (
            f"<ReviewQueue(id={self.id}, content_type={self.content_type}, "
            f"severity={self.severity}, status={self.status})>"
        )
