"""
Async moderation tasks for content review queue.

Runs asynchronously to moderate AI outputs and create review queue items
without blocking the user's execution.
"""
import json
from uuid import UUID
from datetime import datetime

from src.tasks.celery_app import app
from src.database import SessionLocal
from src.models import ReviewQueue, ExecutionLog, ContentType, ModerationSeverity
from magpie_ai.content_moderation import get_moderator


@app.task(bind=True, max_retries=3, queue="moderation")
def moderate_output(
    self,
    execution_log_id: str,
    output_text: str,
    project_id: str,
    llm_url: str = "http://localhost:1234",
    llm_model: str = "qwen2.5-1.5b-instruct"
):
    """
    Async task to moderate AI output and create review queue items.

    Runs after LLM execution completes (non-blocking to user).
    Creates ReviewQueue items if violations are found.

    Args:
        execution_log_id: ID of the execution log
        output_text: AI-generated output to moderate
        project_id: Project ID for moderation context
        llm_url: LM Studio endpoint
        llm_model: Model to use for moderation
    """
    db = SessionLocal()
    try:
        # Verify execution log exists
        execution_log = db.query(ExecutionLog).filter_by(
            id=execution_log_id
        ).first()

        if not execution_log:
            return {"status": "error", "reason": "execution_log_not_found"}

        # Run moderation
        try:
            moderator = get_moderator()
            result = moderator.moderate(output_text)

            # Create review queue item if violations found
            if result.severity and result.severity in ["high", "critical"]:
                review_item = ReviewQueue(
                    id=str(__import__('uuid').uuid4()),  # Generate ID
                    execution_log_id=execution_log_id,
                    project_id=project_id,
                    content_type=ContentType.AI_OUTPUT.value,  # Use string value
                    content_text=output_text[:2000],  # Store first 2000 chars
                    severity=ModerationSeverity(
                        result.severity).value,  # Use string value
                    flagged_policies=result.violated_policies or [],
                    violation_reasons=result.violation_details or {},
                    status="pending",  # Awaiting human review
                )
                db.add(review_item)
                db.commit()

                return {
                    "status": "flagged",
                    "severity": result.severity,
                    "policies": result.violated_policies,
                }
            else:
                # No violations found
                return {
                    "status": "approved",
                    "severity": result.severity or "low",
                }

        except Exception as e:
            # Log error but don't fail - output already delivered to user
            return {
                "status": "error",
                "reason": str(e),
            }

    except Exception as e:
        # Retry with exponential backoff for database/transient errors
        try:
            raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))
        except self.MaxRetriesExceededError:
            return {
                "status": "error",
                "reason": f"Max retries exceeded: {str(e)}",
            }
    finally:
        db.close()
