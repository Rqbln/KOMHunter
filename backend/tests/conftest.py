"""
Pytest configuration and fixtures for KOMHunter tests.
"""
import os
import pytest
from typing import Generator, AsyncGenerator

from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport

# Set test environment variables before importing app
os.environ["STRAVA_CLIENT_ID"] = "test_client_id"
os.environ["STRAVA_CLIENT_SECRET"] = "test_client_secret"
os.environ["JWT_SECRET_KEY"] = "test_jwt_secret_key"

from app.main import app
from app.services.scoring import ScoringService
from app.services.geocoding import GeocodingService


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    """Create a synchronous test client."""
    with TestClient(app) as c:
        yield c


@pytest.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """Create an async test client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def scoring_service() -> ScoringService:
    """Create a scoring service instance."""
    return ScoringService()


@pytest.fixture
def geocoding_service() -> GeocodingService:
    """Create a geocoding service instance."""
    return GeocodingService()


@pytest.fixture
def sample_segment() -> dict:
    """Sample segment data for testing."""
    return {
        "id": 12345678,
        "name": "Test Climb",
        "distance": 5200,
        "avg_grade": 8.1,
        "elev_difference": 340,
        "start_latlng": [40.0150, -105.2705],
        "end_latlng": [40.0089, -105.2890],
        "climb_category": 3,
    }


@pytest.fixture
def sample_athlete() -> dict:
    """Sample athlete data for testing."""
    return {
        "id": 12345,
        "firstname": "Test",
        "lastname": "User",
        "profile": "https://example.com/profile.jpg",
        "city": "Boulder",
        "state": "Colorado",
        "country": "United States",
        "premium": True,
    }


@pytest.fixture
def mock_strava_token() -> dict:
    """Mock Strava token response."""
    return {
        "access_token": "test_access_token",
        "refresh_token": "test_refresh_token",
        "expires_at": 1735689600,  # Future timestamp
        "token_type": "Bearer",
        "athlete": {
            "id": 12345,
            "firstname": "Test",
            "lastname": "User",
        }
    }
