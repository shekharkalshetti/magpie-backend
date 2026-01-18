"""
Audit logs API routes.

Endpoints for retrieving audit logs and audit trail information.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, Request, status, HTTPException, Query

from sqlalchemy.orm import Session
from src.database import get_db
from src.audit_logs.service import AuditLogService
from src.audit_logs.schemas import AuditLogResponse, AuditLogListResponse
from src.audit_logs.models import AuditAction

router = APIRouter()


@router.get(
    "/audit-logs",
    response_model=AuditLogListResponse,
    summary="List audit logs",
    description="List audit logs for a project.",
)
async def list_audit_logs(
    project_id: str = Query(...,
                            description="Project ID to retrieve audit logs for"),
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    action: Optional[str] = Query(None),
    user_id: Optional[str] = Query(None),
):
    """
    List audit logs for a project.

    Supports filtering by action and user.
    Results are ordered by most recent first.

    Query parameters:
    - project_id: Project ID (required)
    - skip: Number of records to skip (default: 0)
    - limit: Maximum records to return (default: 100, max: 500)
    - action: Filter by action type (create, update, delete, reset)
    - user_id: Filter by user who made the change
    """
    # Parse optional filters
    action_filter = None
    if action:
        try:
            action_filter = AuditAction(action)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid action: {action}"
            )

    audit_logs = AuditLogService.list_audit_logs(
        db=db,
        project_id=project_id,
        skip=skip,
        limit=limit,
        action=action_filter,
        user_id=user_id,
    )

    # Count total records for this project (approximate)
    from sqlalchemy import func
    from src.audit_logs.models import AuditLog

    total_query = db.query(func.count(AuditLog.id)).filter(
        AuditLog.project_id == project_id)

    # Apply same filters to total count
    if action_filter:
        total_query = total_query.filter(AuditLog.action == action_filter)
    if user_id:
        total_query = total_query.filter(AuditLog.user_id == user_id)

    total = total_query.scalar() or 0

    # Convert audit logs using the response schema to include user_email
    audit_log_responses = [
        AuditLogResponse.from_orm(log) for log in audit_logs]

    return AuditLogListResponse(
        items=audit_log_responses,
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/audit-logs/{audit_log_id}",
    response_model=AuditLogResponse,
    summary="Get audit log",
    description="Retrieve a single audit log entry by ID.",
)
async def get_audit_log(
    audit_log_id: str,
    project_id: str = Query(..., description="Project ID"),
    db: Session = Depends(get_db),
):
    """
    Get a single audit log entry by ID.
    """
    audit_log = AuditLogService.get_audit_log(db, audit_log_id)

    if not audit_log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audit log not found"
        )

    # Verify the audit log belongs to this project
    if audit_log.project_id != project_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    return audit_log
