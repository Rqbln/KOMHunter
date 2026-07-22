"""
Tests for the JWT auth dependency chain (get_token_payload / get_strava_api_service).

Covers the original production bug: the backend must decode the session JWT
and use the embedded Strava access token — never pass the JWT to Strava.
"""
import time

import httpx
import jwt as pyjwt
import pytest
import respx
from fastapi.testclient import TestClient

from tests.conftest import TEST_JWT_SECRET

STRAVA_ATHLETE_URL = "https://www.strava.com/api/v3/athlete"
STRAVA_TOKEN_URL = "https://www.strava.com/oauth/token"

SAMPLE_ATHLETE = {
    "id": 12345,
    "firstname": "Test",
    "lastname": "User",
    "profile": "https://example.com/profile.jpg",
    "profile_medium": "https://example.com/profile_medium.jpg",
    "city": "Boulder",
    "state": "Colorado",
    "country": "United States",
    "sex": "M",
    "premium": True,
    "created_at": "2020-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z",
}


class TestAuthHeaderParsing:
    """401 contract for missing/malformed Authorization headers."""

    def test_missing_header_returns_401(self, client: TestClient):
        response = client.get("/api/athletes/me")
        assert response.status_code == 401
        assert response.json()["detail"] == "Authorization header required"

    def test_malformed_header_returns_401(self, client: TestClient):
        response = client.get(
            "/api/athletes/me",
            headers={"Authorization": "NotBearer token extra"},
        )
        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid authorization header format"

    def test_bearer_without_token_returns_401(self, client: TestClient):
        response = client.get(
            "/api/athletes/me",
            headers={"Authorization": "Bearer"},
        )
        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid authorization header format"


class TestJWTVerification:
    """JWT signature verification in the dependency chain."""

    def test_tampered_jwt_returns_401(self, client: TestClient):
        now = int(time.time())
        forged = pyjwt.encode(
            {
                "sub": "12345",
                "access_token": "stolen",
                "refresh_token": "stolen",
                "expires_at": now + 3600,
                "iat": now,
                "exp": now + 3600,
            },
            "wrong_secret",
            algorithm="HS256",
        )
        response = client.get(
            "/api/athletes/me",
            headers={"Authorization": f"Bearer {forged}"},
        )
        assert response.status_code == 401
        assert (
            response.json()["detail"]
            == "Invalid or expired session - please log in with Strava again"
        )

    def test_raw_strava_token_rejected(self, client: TestClient):
        """A raw (non-JWT) Strava token must be rejected — JWT-only auth."""
        response = client.get(
            "/api/athletes/me",
            headers={"Authorization": "Bearer raw_strava_access_token"},
        )
        assert response.status_code == 401
        assert (
            response.json()["detail"]
            == "Invalid or expired session - please log in with Strava again"
        )

    @respx.mock
    def test_valid_jwt_returns_200(self, client: TestClient, auth_headers: dict):
        respx.get(STRAVA_ATHLETE_URL).mock(
            return_value=httpx.Response(200, json=SAMPLE_ATHLETE)
        )
        response = client.get("/api/athletes/me", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["id"] == 12345
        # No refresh happened, so no refreshed-token header
        assert "X-KOM-Refreshed-Token" not in response.headers

    @respx.mock
    def test_valid_jwt_sends_embedded_access_token_to_strava(
        self, client: TestClient, auth_headers: dict
    ):
        """The Strava call must carry the embedded access token, not the JWT."""
        route = respx.get(STRAVA_ATHLETE_URL).mock(
            return_value=httpx.Response(200, json=SAMPLE_ATHLETE)
        )
        client.get("/api/athletes/me", headers=auth_headers)
        sent_auth = route.calls.last.request.headers["Authorization"]
        assert sent_auth == "Bearer test_access_token"


class TestTransparentRefresh:
    """Auto-refresh of the embedded Strava token with new JWT minting."""

    @respx.mock
    def test_expired_strava_token_triggers_refresh_and_new_jwt(
        self, client: TestClient, expired_strava_jwt: str
    ):
        new_expires_at = int(time.time()) + 6 * 3600
        respx.post(STRAVA_TOKEN_URL).mock(
            return_value=httpx.Response(
                200,
                json={
                    # Strava refresh responses have NO "athlete" object
                    "token_type": "Bearer",
                    "access_token": "refreshed_access_token",
                    "refresh_token": "refreshed_refresh_token",
                    "expires_at": new_expires_at,
                    "expires_in": 21600,
                },
            )
        )
        athlete_route = respx.get(STRAVA_ATHLETE_URL).mock(
            return_value=httpx.Response(200, json=SAMPLE_ATHLETE)
        )

        response = client.get(
            "/api/athletes/me",
            headers={"Authorization": f"Bearer {expired_strava_jwt}"},
        )

        assert response.status_code == 200
        assert "X-KOM-Refreshed-Token" in response.headers

        new_jwt = response.headers["X-KOM-Refreshed-Token"]
        decoded = pyjwt.decode(new_jwt, TEST_JWT_SECRET, algorithms=["HS256"])
        assert decoded["sub"] == "12345"  # original sub preserved
        assert decoded["access_token"] == "refreshed_access_token"
        assert decoded["refresh_token"] == "refreshed_refresh_token"
        assert decoded["expires_at"] == new_expires_at

        # The Strava call used the refreshed access token
        sent_auth = athlete_route.calls.last.request.headers["Authorization"]
        assert sent_auth == "Bearer refreshed_access_token"

    @respx.mock
    def test_strava_refresh_failure_returns_401(
        self, client: TestClient, expired_strava_jwt: str
    ):
        respx.post(STRAVA_TOKEN_URL).mock(
            return_value=httpx.Response(400, json={"message": "Bad Request"})
        )
        response = client.get(
            "/api/athletes/me",
            headers={"Authorization": f"Bearer {expired_strava_jwt}"},
        )
        assert response.status_code == 401
        assert (
            response.json()["detail"]
            == "Invalid or expired session - please log in with Strava again"
        )

    @respx.mock
    def test_strava_refresh_rate_limited_returns_429_not_401(
        self, client: TestClient, expired_strava_jwt: str
    ):
        """A Strava 429 during refresh must surface as 429 and keep the session
        (never log the user out)."""
        respx.post(STRAVA_TOKEN_URL).mock(
            return_value=httpx.Response(429, json={"message": "Rate Limit Exceeded"})
        )
        response = client.get(
            "/api/athletes/me",
            headers={"Authorization": f"Bearer {expired_strava_jwt}"},
        )
        assert response.status_code == 429
        assert (
            response.json()["detail"]
            == "Strava rate limit exceeded - try again later"
        )

    @respx.mock
    def test_strava_refresh_server_error_returns_503_not_401(
        self, client: TestClient, expired_strava_jwt: str
    ):
        """A Strava 5xx during refresh must surface as 503 and keep the session."""
        respx.post(STRAVA_TOKEN_URL).mock(
            return_value=httpx.Response(500, json={"message": "Server Error"})
        )
        response = client.get(
            "/api/athletes/me",
            headers={"Authorization": f"Bearer {expired_strava_jwt}"},
        )
        assert response.status_code == 503
        assert response.json()["detail"] == "Strava is unreachable - try again later"

    @respx.mock
    def test_strava_network_failure_returns_503_not_401(
        self, client: TestClient, expired_strava_jwt: str
    ):
        """A Strava outage must not log the user out: 503, never 401/500."""
        respx.post(STRAVA_TOKEN_URL).mock(
            side_effect=httpx.ConnectError("connection refused")
        )
        response = client.get(
            "/api/athletes/me",
            headers={"Authorization": f"Bearer {expired_strava_jwt}"},
        )
        assert response.status_code == 503
        assert response.json()["detail"] == "Strava is unreachable - try again later"

    @respx.mock
    def test_refresh_response_without_refresh_token_keeps_current_one(
        self, client: TestClient, expired_strava_jwt: str
    ):
        """refresh_token is optional per RFC 6749: the new JWT must fall back
        to the refresh token already embedded in the session."""
        new_expires_at = int(time.time()) + 6 * 3600
        respx.post(STRAVA_TOKEN_URL).mock(
            return_value=httpx.Response(
                200,
                json={
                    "token_type": "Bearer",
                    "access_token": "refreshed_access_token",
                    # no refresh_token field
                    "expires_at": new_expires_at,
                    "expires_in": 21600,
                },
            )
        )
        respx.get(STRAVA_ATHLETE_URL).mock(
            return_value=httpx.Response(200, json=SAMPLE_ATHLETE)
        )
        response = client.get(
            "/api/athletes/me",
            headers={"Authorization": f"Bearer {expired_strava_jwt}"},
        )
        assert response.status_code == 200
        new_jwt = response.headers["X-KOM-Refreshed-Token"]
        decoded = pyjwt.decode(new_jwt, TEST_JWT_SECRET, algorithms=["HS256"])
        original = pyjwt.decode(
            expired_strava_jwt, TEST_JWT_SECRET, algorithms=["HS256"]
        )
        assert decoded["refresh_token"] == original["refresh_token"]
