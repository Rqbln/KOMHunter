"""
Tests for health check endpoints.
"""
import pytest
from fastapi.testclient import TestClient


def test_health_check(client: TestClient):
    """Test the main health check endpoint."""
    response = client.get("/api/health")
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "healthy"
    assert "app_name" in data
    assert "version" in data
    assert "timestamp" in data


def test_readiness_check(client: TestClient):
    """Test the readiness probe endpoint."""
    response = client.get("/api/health/ready")
    assert response.status_code == 200
    assert response.json()["status"] == "ready"


def test_liveness_check(client: TestClient):
    """Test the liveness probe endpoint."""
    response = client.get("/api/health/live")
    assert response.status_code == 200
    assert response.json()["status"] == "alive"


def test_root_endpoint(client: TestClient):
    """Test the root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    
    data = response.json()
    assert "message" in data
    assert "docs" in data
