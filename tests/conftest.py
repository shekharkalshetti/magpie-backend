"""
Test configuration and fixtures.
"""
import pytest
from httpx import ASGITransport, AsyncClient

from src.main import app


@pytest.fixture
async def client():
    """
    Async test client for FastAPI app.

    Use this fixture for integration tests.
    """
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client


@pytest.fixture
def test_project_data():
    """Sample project data for tests."""
    return {
        "name": "test-project",
        "description": "A test project",
    }
