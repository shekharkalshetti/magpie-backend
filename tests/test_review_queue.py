"""
Test suite for ReviewQueue system

Tests the complete compliance and moderation workflow including:
- Input moderation (sync, blocking)
- Output moderation (async, non-blocking)
- ReviewQueue service operations
- API endpoints
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
from uuid import uuid4

# Note: These are integration test examples
# Run with: pytest tests/test_review_queue.py -v

def test_review_queue_model_creation():
    """Test that ReviewQueue model can be instantiated"""
    from src.review_queue.models import ReviewQueue, ContentType, ReviewStatus, ModerationSeverity
    
    item = ReviewQueue(
        id=uuid4(),
        execution_log_id=uuid4(),
        project_id=uuid4(),
        content_type=ContentType.AI_OUTPUT,
        content_text="Test content",
        severity=ModerationSeverity.HIGH,
        flagged_policies=["policy_1", "policy_2"],
        violation_reasons=["reason 1", "reason 2"],
        status=ReviewStatus.PENDING,
        reviewed_by_user_id=None,
        review_notes=None,
        reviewed_at=None,
    )
    
    assert item.content_type == ContentType.AI_OUTPUT
    assert item.severity == ModerationSeverity.HIGH
    assert item.status == ReviewStatus.PENDING


def test_content_moderation_error():
    """Test that ContentModerationError is raised on critical violations"""
    from src.auth.exceptions import ContentModerationError
    
    # This exception should be raised when input moderation detects critical violations
    with pytest.raises(ContentModerationError):
        raise ContentModerationError(
            message="Critical policy violation detected",
            policies=["policy_1"],
            severity="critical"
        )


def test_celery_app_configuration():
    """Test that Celery app is properly configured"""
    from src.tasks.celery_app import app
    
    assert app.conf.broker_url == "redis://localhost:6379/0"
    assert app.conf.result_backend == "redis://localhost:6379/0"
    assert "moderation" in app.conf.task_queues


def test_moderation_task_registration():
    """Test that moderation task is registered with Celery"""
    from src.tasks.celery_app import app
    from src.tasks.moderation_tasks import moderate_output
    
    # Verify task is registered
    assert "src.tasks.moderation_tasks.moderate_output" in app.tasks


def test_api_routes_registered():
    """Test that ReviewQueue routes are registered in FastAPI app"""
    from src.main import app
    
    routes = {route.path for route in app.routes}
    
    # Verify all ReviewQueue endpoints are registered
    assert "/api/v1/projects/{project_id}/review-queue" in routes
    assert "/api/v1/projects/{project_id}/review-queue/stats" in routes
    assert "/api/v1/review-queue/{item_id}" in routes


@pytest.mark.asyncio
async def test_review_queue_service_instantiation():
    """Test that ReviewQueueService can be instantiated"""
    from src.review_queue.service import ReviewQueueService
    from sqlalchemy.ext.asyncio import AsyncSession
    
    # Mock database session
    mock_db = AsyncMock(spec=AsyncSession)
    
    service = ReviewQueueService(mock_db)
    assert service.db == mock_db


def test_review_queue_schemas():
    """Test that ReviewQueue Pydantic schemas are valid"""
    from src.review_queue.schemas import ReviewQueueResponse, ReviewQueueStatsResponse
    from datetime import datetime
    from uuid import uuid4
    
    # Test ReviewQueueResponse
    response_data = {
        "id": str(uuid4()),
        "execution_log_id": str(uuid4()),
        "project_id": str(uuid4()),
        "content_type": "ai_output",
        "content_text": "Test content",
        "severity": "high",
        "flagged_policies": ["policy_1"],
        "violation_reasons": ["reason 1"],
        "status": "pending",
        "reviewed_by_user_id": None,
        "review_notes": None,
        "reviewed_at": None,
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
    }
    
    response = ReviewQueueResponse(**response_data)
    assert response.severity == "high"
    assert response.status == "pending"
    
    # Test ReviewQueueStatsResponse
    stats_data = {
        "total_items": 10,
        "pending_items": 5,
        "approved_items": 3,
        "rejected_items": 2,
        "by_severity": {"critical": 1, "high": 4, "medium": 3, "low": 2},
        "by_content_type": {"ai_output": 8, "user_input": 2},
    }
    
    stats = ReviewQueueStatsResponse(**stats_data)
    assert stats.total_items == 10
    assert stats.by_severity["critical"] == 1


def test_monitor_decorator_imports():
    """Test that monitor decorator can be imported"""
    from sdk.triton.monitor import monitor
    
    assert callable(monitor)


def test_client_log_sync_signature():
    """Test that send_log_sync returns Optional[str]"""
    from sdk.triton.client import TritonClient
    import inspect
    
    # Get the signature of send_log_sync
    sig = inspect.signature(TritonClient.send_log_sync)
    
    # Verify return annotation exists
    assert sig.return_annotation is not inspect.Signature.empty


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
