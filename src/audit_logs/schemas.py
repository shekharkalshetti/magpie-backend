"""
Schemas for audit logs API.
"""
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
from src.audit_logs.models import AuditAction


class AuditLogResponse(BaseModel):
    """Response schema for audit log entries."""
    id: str
    user_id: str
    action: str  # Will be returned as string from enum
    description: Optional[str]
    created_at: datetime
    user_email: Optional[str] = None  # Will be populated from relationship

    class Config:
        from_attributes = True

    @classmethod
    def from_orm(cls, obj):
        """Custom from_orm to include user_email from relationship."""
        data = {
            'id': obj.id,
            'user_id': obj.user_id,
            'action': obj.action.value if hasattr(obj.action, 'value') else str(obj.action),
            'description': obj.description,
            'created_at': obj.created_at,
            'user_email': obj.user.email if obj.user else None
        }
        return cls(**data)


class AuditLogListResponse(BaseModel):
    """Response schema for listing audit logs."""
    items: List[AuditLogResponse]
    total: int
    skip: int
    limit: int


class AuditLogCreate(BaseModel):
    """Schema for creating audit log entries."""
    action: AuditAction
    description: Optional[str] = None
