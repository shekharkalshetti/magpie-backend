"""
Audit Log models for tracking system actions and changes.
"""
from sqlalchemy import Column, String, DateTime, Enum as SQLEnum, ForeignKey, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum
import uuid

from src.database import Base


class AuditAction(str, Enum):
    """Audit action types."""
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    RESET = "reset"


class AuditLog(Base):
    """
    Audit log entry for tracking policy changes.

    Records who did what, when, and provides a description of the change.
    Used for compliance, debugging, and security monitoring.
    """
    __tablename__ = "audit_logs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"),
                     nullable=False, index=True)
    project_id = Column(String, ForeignKey("projects.id"),
                        nullable=False, index=True)

    # What happened
    action = Column(SQLEnum(AuditAction), nullable=False, index=True)

    # Human-readable description of change
    description = Column(String, nullable=True)

    # Metadata
    created_at = Column(DateTime, nullable=False,
                        default=datetime.utcnow, index=True)

    # Relationships
    user = relationship("User", back_populates="audit_logs")
    project = relationship("Project", back_populates="audit_logs")

    __table_args__ = (
        Index("ix_audit_logs_user_id_created_at", "user_id", "created_at"),
        Index("ix_audit_logs_project_id_created_at",
              "project_id", "created_at"),
    )
