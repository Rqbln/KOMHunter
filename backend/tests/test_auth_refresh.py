"""
Tests for POST /api/auth/refresh (JWT-in/JWT-out) and GET /api/auth/me.
"""
import time

import httpx
import jwt as pyjwt
import respx
from fastapi.testclient import TestClient

from tests.conftest import TEST_JWT_SECRET

STRAVA_TOKEN_URL = "https://www.strava.com/oauth/token"


def _refresh_response(expires_at: int) -> dict:
    """Strava token refresh response — note: no 'athlete' object."""
    return {
        "token_type": "Bearer",
        "access_token": "refreshed_access_token",
        "refresh_token": "refreshed_refresh_token",
        "expires_at": expires_at,
        "expires_in": 21600,
    }


class TestRefreshSession:
    """POST /api/auth/refresh"""

    @respx.mock
    def test_refresh_jwt_in_jwt_out(self, client: TestClient, valid_jwt: str):
        new_expires_at = int(time.time()) + 6 * 3600
        respx.post(STRAVA_TOKEN_URL).mock(
            return_value=httpx.Response(200, json=_refresh_response(new_expires_at))
        )
        response = client.post("/api/auth/refresh", json={"token": valid_jwt})

        assert response.status_code == 200
        body = response.json()
        assert set(body.keys()) == {"token"}  # no raw Strava tokens returned

        decoded = pyjwt.decode(body["token"], TEST_JWT_SECRET, algorithms=["HS256"])
        assert decoded["sub"] == "12345"  # original subject preserved
        assert decoded["access_token"] == "refreshed_access_token"
        assert decoded["refresh_token"] == "refreshed_refresh_token"
        assert decoded["expires_at"] == new_expires_at

    @respx.mock
    def test_refresh_accepts_jwt_with_expired_exp(self, client: TestClient):
        """A lapsed session JWT (exp in the past) is still refreshable if the
        signature is valid — exp verification is disabled for this endpoint."""
        now = int(time.time())
        lapsed_jwt = pyjwt.encode(
            {
                "sub": "12345",
                "access_token": "old_access_token",
                "refresh_token": "old_refresh_token",
                "expires_at": now - 10000,
                "iat": now - 20000,
                "exp": now - 5000,  # JWT itself expired
            },
            TEST_JWT_SECRET,
            algorithm="HS256",
        )
        new_expires_at = now + 6 * 3600
        respx.post(STRAVA_TOKEN_URL).mock(
            return_value=httpx.Response(200, json=_refresh_response(new_expires_at))
        )
        response = client.post("/api/auth/refresh", json={"token": lapsed_jwt})

        assert response.status_code == 200
        decoded = pyjwt.decode(
            response.json()["token"], TEST_JWT_SECRET, algorithms=["HS256"]
        )
        assert decoded["sub"] == "12345"
        assert decoded["exp"] > now  # fresh session expiry

    def test_refresh_bad_signature_returns_401(self, client: TestClient):
        now = int(time.time())
        forged_jwt = pyjwt.encode(
            {
                "sub": "12345",
                "access_token": "a",
                "refresh_token": "r",
                "expires_at": now,
                "iat": now,
                "exp": now + 3600,
            },
            "wrong_secret",
            algorithm="HS256",
        )
        response = client.post("/api/auth/refresh", json={"token": forged_jwt})
        assert response.status_code == 401
        assert (
            response.json()["detail"]
            == "Invalid or expired session - please log in with Strava again"
        )

    @respx.mock
    def test_refresh_strava_failure_returns_401(
        self, client: TestClient, valid_jwt: str
    ):
        """A Strava 400 (invalid refresh token) ends the session with a 401."""
        respx.post(STRAVA_TOKEN_URL).mock(
            return_value=httpx.Response(400, json={"message": "Bad Request"})
        )
        response = client.post("/api/auth/refresh", json={"token": valid_jwt})
        assert response.status_code == 401
        assert (
            response.json()["detail"]
            == "Invalid or expired session - please log in with Strava again"
        )

    @respx.mock
    def test_refresh_strava_rate_limited_returns_429(
        self, client: TestClient, valid_jwt: str
    ):
        """A Strava 429 must surface as 429, not a 401 logout."""
        respx.post(STRAVA_TOKEN_URL).mock(
            return_value=httpx.Response(429, json={"message": "Rate Limit Exceeded"})
        )
        response = client.post("/api/auth/refresh", json={"token": valid_jwt})
        assert response.status_code == 429
        assert (
            response.json()["detail"]
            == "Strava rate limit exceeded - try again later"
        )

    @respx.mock
    def test_refresh_strava_server_error_returns_503(
        self, client: TestClient, valid_jwt: str
    ):
        """A Strava 5xx must surface as 503, not a 401 logout."""
        respx.post(STRAVA_TOKEN_URL).mock(
            return_value=httpx.Response(500, json={"message": "Server Error"})
        )
        response = client.post("/api/auth/refresh", json={"token": valid_jwt})
        assert response.status_code == 503
        assert response.json()["detail"] == "Strava is unreachable - try again later"


class TestAuthMe:
    """GET /api/auth/me"""

    def test_me_returns_contract_fields(self, client: TestClient, make_jwt):
        strava_expires_at = int(time.time()) + 6 * 3600
        token = make_jwt(expires_at=strava_expires_at)
        response = client.get(
            "/api/auth/me", headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert set(data.keys()) == {
            "athlete_id",
            "strava_token_expires_at",
            "session_expires_at",
            "strava_token_expired",
        }
        assert data["athlete_id"] == "12345"
        assert data["strava_token_expires_at"] == strava_expires_at
        assert data["session_expires_at"] > int(time.time())
        assert data["strava_token_expired"] is False

    def test_me_requires_auth(self, client: TestClient):
        response = client.get("/api/auth/me")
        assert response.status_code == 401
        assert response.json()["detail"] == "Authorization header required"

    def test_me_makes_no_strava_call(self, client: TestClient, valid_jwt: str):
        """With a fresh embedded token, /me must not hit the network."""
        with respx.mock:  # assert_all_mocked: any outbound call would raise
            response = client.get(
                "/api/auth/me", headers={"Authorization": f"Bearer {valid_jwt}"}
            )
        assert response.status_code == 200
