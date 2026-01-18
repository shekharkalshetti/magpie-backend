"""Service layer for ReviewQueue operations."""
from sqlalchemy.orm import Session
from uuid import UUID
from src.models import ReviewQueue, ReviewStatus


class ReviewQueueService:
    """Service for managing review queue items."""

    @staticmethod
    def get_project_review_queue(
        db: Session,
        project_id: UUID,
        status: str | None = None,
        severity: str | None = None,
        content_type: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ):
        """Get review queue items for a project with optional filters."""
        query = db.query(ReviewQueue).filter_by(project_id=project_id)

        if status:
            query = query.filter_by(status=status)
        if severity:
            query = query.filter_by(severity=severity)
        if content_type:
            query = query.filter_by(content_type=content_type)

        # Order by created_at descending (newest first)
        query = query.order_by(ReviewQueue.created_at.desc())

        total = query.count()
        items = query.offset(skip).limit(limit).all()

        return items, total

    @staticmethod
    def get_review_item(db: Session, item_id: UUID):
        """Get a specific review queue item."""
        return db.query(ReviewQueue).filter_by(id=item_id).first()

    @staticmethod
    def update_review_item(
        db: Session,
        item_id: UUID,
        status: str,
        notes: str | None,
        reviewed_by_user_id: str,
    ):
        """Update a review queue item with decision and notes."""
        item = db.query(ReviewQueue).filter_by(id=item_id).first()
        if not item:
            return None

        item.status = status
        item.review_notes = notes
        item.reviewed_by_user_id = reviewed_by_user_id
        item.reviewed_at = __import__('datetime').datetime.utcnow()

        db.commit()
        db.refresh(item)
        return item

    @staticmethod
    def get_stats(db: Session, project_id: UUID):
        """Get review queue statistics for a project."""
        total = db.query(ReviewQueue).filter_by(project_id=project_id).count()
        pending = (
            db.query(ReviewQueue)
            .filter_by(project_id=project_id, status="pending")
            .count()
        )
        approved = (
            db.query(ReviewQueue)
            .filter_by(project_id=project_id, status="approved")
            .count()
        )
        rejected = (
            db.query(ReviewQueue)
            .filter_by(project_id=project_id, status="rejected")
            .count()
        )

        return {
            "total": total,
            "pending": pending,
            "approved": approved,
            "rejected": rejected,
        }
