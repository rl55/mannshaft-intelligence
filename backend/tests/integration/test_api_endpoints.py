"""
Integration tests for API endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock

from api.main import app
from tests.conftest import load_fixture


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


def test_health_check(client):
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert "status" in response.json()


def test_root_endpoint(client):
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert "name" in response.json()


def test_trigger_analysis(client):
    """Test analysis trigger endpoint."""
    with patch('api.routes.analysis.run_analysis', new_callable=AsyncMock):
        response = client.post(
            "/api/v1/analysis/trigger",
            json={
                "week_number": 25,
                "analysis_type": "comprehensive",
                "user_id": "test_user"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
        assert data["status"] == "queued"


def test_get_analysis_status(client):
    """Test get analysis status endpoint."""
    # First trigger an analysis
    with patch('api.routes.analysis.run_analysis', new_callable=AsyncMock):
        trigger_response = client.post(
            "/api/v1/analysis/trigger",
            json={
                "week_number": 25,
                "analysis_type": "comprehensive",
                "user_id": "test_user"
            }
        )
        
        session_id = trigger_response.json()["session_id"]
        
        # Get status
        status_response = client.get(f"/api/v1/analysis/{session_id}/status")
        assert status_response.status_code == 200
        assert "status" in status_response.json()


def test_get_sessions(client):
    """Test get sessions endpoint."""
    response = client.get("/api/v1/sessions?limit=10")
    assert response.status_code == 200
    assert "sessions" in response.json()
    assert "total" in response.json()


def test_get_cache_stats(client):
    """Test get cache stats endpoint."""
    response = client.get("/api/v1/cache/stats?days=7")
    assert response.status_code == 200
    data = response.json()
    assert "prompt_cache_hits" in data
    assert "cache_hit_rate" in data


def test_get_monitoring_agents(client):
    """Test monitoring agents endpoint."""
    response = client.get("/api/v1/monitoring/agents?days=7")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_hitl_pending(client):
    """Test get pending HITL requests."""
    response = client.get("/api/v1/hitl/pending?limit=10")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

