"""
Audit logging service.

Handles creating and querying audit log entries.
"""
from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc

from src.audit_logs.models import AuditLog, AuditAction


class AuditLogService:
    """Service for audit log operations."""

    @staticmethod
    def create_audit_log(
        db: Session,
        user_id: str,
        project_id: str,
        action: AuditAction,
        description: Optional[str] = None,
    ) -> AuditLog:
        """
        Create a new audit log entry.

        Args:
            db: Database session
            user_id: ID of user who made the change
            project_id: Project ID
            action: Type of action (create, update, delete, reset)
            description: Human-readable description of the change

        Returns:
            Created AuditLog object
        """
        audit_log = AuditLog(
            user_id=user_id,
            project_id=project_id,
            action=action,
            description=description,
            created_at=datetime.utcnow(),
        )

        db.add(audit_log)
        # Don't commit here - let the caller manage the transaction
        # db.commit()
        # db.refresh(audit_log)

        return audit_log

    @staticmethod
    def list_audit_logs(
        db: Session,
        project_id: str,
        skip: int = 0,
        limit: int = 100,
        user_id: Optional[str] = None,
        action: Optional[AuditAction] = None,
    ) -> List[AuditLog]:
        """
        List audit logs for a project.

        Args:
            db: Database session
            project_id: Project ID to filter by
            skip: Number of records to skip
            limit: Maximum number of records to return
            user_id: Optional filter by user
            action: Optional filter by action type

        Returns:
            List of AuditLog objects
        """
        from sqlalchemy.orm import joinedload

        query = db.query(AuditLog).filter(AuditLog.project_id == project_id)

        if user_id:
            query = query.filter(AuditLog.user_id == user_id)

        if action:
            query = query.filter(AuditLog.action == action)

        # Eager load the user relationship
        query = query.options(joinedload(AuditLog.user))

        # Order by created_at descending (most recent first)
        query = query.order_by(desc(AuditLog.created_at))

        return query.offset(skip).limit(limit).all()

    @staticmethod
    def get_audit_log(db: Session, audit_log_id: str) -> Optional[AuditLog]:
        """Get a single audit log by ID."""
        return db.query(AuditLog).filter(AuditLog.id == audit_log_id).first()
