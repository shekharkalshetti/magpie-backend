"""
Log business logic service.

Contains core business logic for execution log operations.
"""
from typing import Optional, List, Dict, Any
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import func

from src.logs.schemas import ExecutionLogCreate
from src.models import ExecutionLog, ReviewQueue, ContentType, ModerationSeverity
import uuid


async def create_execution_log(
    db: Session,
    project_id: str,
    data: ExecutionLogCreate,
) -> ExecutionLog:
    """
    Create a new execution log with comprehensive metrics.

    This function is designed to never fail - it will always create a log entry.

    Args:
        db: Database session
        project_id: Project ID
        data: Execution log data with metrics

    Returns:
        Created ExecutionLog object
    """
    try:
        # Calculate total tokens if both input and output are present
        total_tokens = None
        if data.input_tokens and data.output_tokens:
            total_tokens = data.input_tokens + data.output_tokens

        # Calculate total cost if both input and output costs are present
        total_cost = None
        if data.input_cost is not None and data.output_cost is not None:
            total_cost = data.input_cost + data.output_cost

        execution_log = ExecutionLog(
            project_id=project_id,
            trace_id=data.trace_id,
            input=data.input,
            output=data.output,
            custom_data=data.custom,
            started_at=data.started_at,
            completed_at=data.completed_at,
            total_latency_ms=data.total_latency_ms,
            status=data.status,
            error_message=data.error_message,
            function_name=data.function_name,
            input_tokens=data.input_tokens,
            output_tokens=data.output_tokens,
            total_tokens=total_tokens,
            context_utilization=data.context_utilization,
            input_cost=data.input_cost,
            output_cost=data.output_cost,
            total_cost=total_cost,
            pii_detection=data.pii_detection,
            content_moderation=data.content_moderation,
        )

        db.add(execution_log)
        db.commit()
        db.refresh(execution_log)

        # Auto-create ReviewQueue item for blocked inputs with content moderation violations
        _create_review_queue_for_blocked_input(db, execution_log)
        
        # Commit any ReviewQueue items that were added
        try:
            db.commit()
        except:
            # If review queue commit fails, it's okay - log still exists
            pass

        return execution_log

    except Exception as e:
        # Fail open - log creation error but don't crash
        db.rollback()
        # In production, you might want to log this error
        raise


async def list_execution_logs(
    db: Session,
    project_id: str,
    skip: int = 0,
    limit: int = 100,
    trace_id: Optional[str] = None,
    include_flagged: bool = False,
) -> list[ExecutionLog]:
    """
    List execution logs for a project.

    By default, excludes flagged/blocked items (items with ReviewQueue entries).
    These are tracked separately in the review_queue endpoints.

    Args:
        db: Database session
        project_id: Project ID
        skip: Number of records to skip
        limit: Maximum number of records to return
        trace_id: Optional trace_id filter
        include_flagged: If True, includes flagged items; if False, excludes them

    Returns:
        List of ExecutionLog objects
    """
    query = db.query(ExecutionLog).filter(
        ExecutionLog.project_id == project_id)

    if trace_id:
        query = query.filter(ExecutionLog.trace_id == trace_id)

    # Exclude flagged items by default
    if not include_flagged:
        flagged_log_ids = db.query(ReviewQueue.execution_log_id).filter(
            ReviewQueue.project_id == project_id
        ).all()
        flagged_log_ids = [item[0] for item in flagged_log_ids]
        if flagged_log_ids:
            query = query.filter(~ExecutionLog.id.in_(flagged_log_ids))

    return (
        query.order_by(ExecutionLog.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


async def get_execution_log(
    db: Session,
    project_id: str,
    log_id: str,
) -> Optional[ExecutionLog]:
    """
    Get a specific execution log.

    Args:
        db: Database session
        project_id: Project ID (for access control)
        log_id: Log ID

    Returns:
        ExecutionLog if found, None otherwise
    """
    return (
        db.query(ExecutionLog)
        .filter(
            ExecutionLog.id == log_id,
            ExecutionLog.project_id == project_id,
        )
        .first()
    )


async def get_observability_stats(
    db: Session,
    project_id: str,
) -> Dict[str, Any]:
    """
    Get aggregated observability statistics for a project.

    Returns:
    - total_requests: Total number of execution logs
    - success_rate: Percentage of successful executions (0-100)
    - total_cost: Sum of all costs in USD
    - avg_latency_ms: Average latency in milliseconds

    Note: Excludes blocked/flagged items (items with ReviewQueue entries).
    These are tracked separately in the review_queue endpoints.

    Args:
        db: Database session
        project_id: Project ID

    Returns:
        Dictionary with aggregated stats
    """
    # Get execution log IDs that have ReviewQueue items (blocked/flagged)
    flagged_log_ids = db.query(ReviewQueue.execution_log_id).filter(
        ReviewQueue.project_id == project_id
    ).all()
    flagged_log_ids = [item[0] for item in flagged_log_ids]

    # Get all logs for the project EXCLUDING flagged items
    logs = db.query(ExecutionLog).filter(
        ExecutionLog.project_id == project_id,
        ~ExecutionLog.id.in_(flagged_log_ids) if flagged_log_ids else True
    ).all()

    if not logs:
        return {
            "total_requests": 0,
            "success_rate": 0.0,
            "total_cost": 0.0,
            "avg_latency_ms": 0.0,
        }

    # Calculate stats
    total_requests = len(logs)
    successful = sum(1 for log in logs if log.status == "success")
    success_rate = (successful / total_requests *
                    100) if total_requests > 0 else 0.0

    # Calculate total cost
    total_cost = 0.0
    valid_costs = [
        log.total_cost for log in logs if log.total_cost is not None]
    if valid_costs:
        total_cost = sum(valid_costs)

    # Calculate average latency
    avg_latency_ms = 0.0
    valid_latencies = [
        log.total_latency_ms for log in logs if log.total_latency_ms is not None]
    if valid_latencies:
        avg_latency_ms = sum(valid_latencies) / len(valid_latencies)

    return {
        "total_requests": total_requests,
        "success_rate": round(success_rate, 1),
        "total_cost": round(total_cost, 4),
        "avg_latency_ms": round(avg_latency_ms, 1),
    }


def _create_review_queue_for_blocked_input(db: Session, execution_log: ExecutionLog) -> None:
    """
    Auto-create ReviewQueue item for blocked inputs with content moderation violations.

    Triggered when an ExecutionLog is created with:
    - status="error"
    - content_moderation violations detected

    This ensures all blocked inputs are auditable in the ReviewQueue without requiring
    the SDK to queue async tasks (which won't work in external environments).

    Args:
        db: Database session
        execution_log: The ExecutionLog that was just created
    """
    try:
        # Only process error logs with content moderation violations
        if execution_log.status != "error" or not execution_log.content_moderation:
            return

        moderation_data = execution_log.content_moderation

        # Check if this was a blocking violation
        # Can have violations list OR just blocked=True / action=block
        violations = moderation_data.get('violations', [])
        is_blocked = moderation_data.get('blocked', False)
        action = moderation_data.get('action', '')
        
        # Skip if not blocked and no violations
        if not violations and not is_blocked and action != 'block':
            return

        # Extract violation details (may be empty if just blocked without specific violations)
        violated_policies = [v.get('category', '') for v in violations]
        
        # If no specific policies but blocked, add generic "content_policy_violation"
        if not violated_policies and (is_blocked or action == 'block'):
            violated_policies = ['content_policy_violation']

        # Get max severity from violations, or default to high if blocked without violations
        max_severity = "high"  # Default for blocked content
        for v in violations:
            severity_val = v.get('severity', 'low')
            if severity_val == 'critical':
                max_severity = 'critical'
                break
            elif severity_val == 'high' and max_severity != 'critical':
                max_severity = 'high'

        # Create ReviewQueue item
        review_item = ReviewQueue(
            id=str(uuid.uuid4()),
            execution_log_id=execution_log.id,
            project_id=execution_log.project_id,
            content_type=ContentType.USER_INPUT.value,
            content_text=execution_log.input[:2000] if execution_log.input else "",
            severity=ModerationSeverity(max_severity).value,
            flagged_policies=violated_policies,
            violation_reasons={
                'violations': violations,
                'action': moderation_data.get('action'),
                'is_safe': moderation_data.get('is_safe')
            },
            status="pending",
        )

        db.add(review_item)
        db.flush()  # Flush to validate, but don't commit (caller commits)

    except Exception as e:
        # Fail open - don't crash if ReviewQueue creation fails
        # Just log and continue - execution log already committed
        print(f"[ReviewQueue] Failed to create item: {str(e)}")
