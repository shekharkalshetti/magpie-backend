"""
Tests for project endpoints.
"""
import pytest


@pytest.mark.asyncio
async def test_health_check(client):
    """Test the health check endpoint."""
    response = await client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


@pytest.mark.asyncio
async def test_root_endpoint(client):
    """Test the root endpoint."""
    response = await client.get("/")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "triton-control-plane"
