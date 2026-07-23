"""
Tests for authentication endpoints and services.
"""
from urllib.parse import parse_qs, urlsplit

import httpx
import jwt as pyjwt
import pytest
import respx
from fastapi.testclient import TestClient

from app.services.strava_auth import StravaAuthService
from tests.conftest import TEST_JWT_SECRET


class TestAuthEndpoints:
    """Tests for authentication API endpoints."""
    
    def test_login_redirect(self, client: TestClient):
        """Test that login redirects to Strava."""
        response = client.get("/api/auth/login", follow_redirects=False)
        
        assert response.status_code == 302
        assert "strava.com" in response.headers["location"]
        assert "oauth/authorize" in response.headers["location"]
    
    def test_login_includes_required_params(self, client: TestClient):
        """Test that login URL includes required OAuth params."""
        response = client.get("/api/auth/login", follow_redirects=False)
        location = response.headers["location"]
        
        assert "client_id=" in location
        assert "redirect_uri=" in location
        assert "response_type=code" in location
        assert "state=" in location
    
    def test_callback_requires_code(self, client: TestClient):
        """Test that callback requires authorization code."""
        response = client.get("/api/auth/callback?state=test")
        assert response.status_code == 422  # Validation error
    
    def test_callback_requires_state(self, client: TestClient):
        """Test that callback requires state token."""
        response = client.get("/api/auth/callback?code=test")
        assert response.status_code == 422  # Validation error
    
    def test_callback_validates_state(self, client: TestClient):
        """Test that callback validates state token."""
        response = client.get("/api/auth/callback?code=test&state=invalid")
        assert response.status_code == 400
        assert "Invalid" in response.json()["detail"]


class TestRedirectUrlAllowlist:
    """Open-redirect guard: only configured frontend origins may receive the JWT."""

    @pytest.mark.parametrize(
        "redirect_url",
        [
            "https://evil.tld",
            "http://evil.tld/steal",
            # Host-smuggling variants: allowed origin as userinfo or subdomain prefix
            "http://localhost:3000@evil.tld",
            "http://localhost:3000.evil.tld",
            # Backslash trick (browsers treat "\" as "/")
            "http://localhost:3000\\@evil.tld",
            # Non-http(s) schemes
            "javascript:alert(1)",
            "data:text/html,<script>alert(1)</script>",
            # Scheme-relative / relative forms (no explicit allowed origin)
            "//evil.tld",
            "/relative/path",
        ],
    )
    def test_login_rejects_disallowed_redirect_url(
        self, client: TestClient, redirect_url: str
    ):
        response = client.get(
            "/api/auth/login",
            params={"redirect_url": redirect_url},
            follow_redirects=False,
        )
        assert response.status_code == 400
        assert response.json()["detail"] == "redirect_url is not an allowed origin"

    def test_login_accepts_allowed_origin_with_path_and_query(
        self, client: TestClient
    ):
        response = client.get(
            "/api/auth/login",
            params={"redirect_url": "http://localhost:3000/dashboard?tab=koms"},
            follow_redirects=False,
        )
        assert response.status_code == 302
        assert "strava.com" in response.headers["location"]

    @respx.mock
    def test_callback_redirects_only_to_allowed_origin_with_token_fragment(
        self, client: TestClient, mock_strava_token: dict
    ):
        """Full flow: validated redirect target, pre-existing fragment stripped,
        JWT delivered in the #token= fragment."""
        login_response = client.get(
            "/api/auth/login",
            params={"redirect_url": "http://localhost:3000/dashboard?tab=koms#old"},
            follow_redirects=False,
        )
        assert login_response.status_code == 302
        state = parse_qs(urlsplit(login_response.headers["location"]).query)["state"][0]

        respx.post("https://www.strava.com/oauth/token").mock(
            return_value=httpx.Response(200, json=mock_strava_token)
        )
        callback_response = client.get(
            "/api/auth/callback",
            params={"code": "auth_code", "state": state},
            follow_redirects=False,
        )

        assert callback_response.status_code == 302
        location = callback_response.headers["location"]
        assert location.startswith("http://localhost:3000/dashboard?tab=koms#token=")
        assert "#old" not in location  # original fragment stripped

        token = location.split("#token=", 1)[1]
        decoded = pyjwt.decode(token, TEST_JWT_SECRET, algorithms=["HS256"])
        assert decoded["sub"] == "12345"

    def test_login_without_redirect_url_defaults_to_frontend_origin(
        self, client: TestClient, mock_strava_token: dict
    ):
        """Omitted redirect_url falls back to the first configured CORS origin."""
        login_response = client.get("/api/auth/login", follow_redirects=False)
        state = parse_qs(urlsplit(login_response.headers["location"]).query)["state"][0]

        with respx.mock:
            respx.post("https://www.strava.com/oauth/token").mock(
                return_value=httpx.Response(200, json=mock_strava_token)
            )
            callback_response = client.get(
                "/api/auth/callback",
                params={"code": "auth_code", "state": state},
                follow_redirects=False,
            )

        assert callback_response.status_code == 302
        assert callback_response.headers["location"].startswith(
            "http://localhost:3000#token="
        )


class TestStravaAuthService:
    """Tests for StravaAuthService."""
    
    @pytest.fixture
    def auth_service(self):
        """Create an auth service instance for testing."""
        return StravaAuthService(
            client_id="test_id",
            client_secret="test_secret",
            redirect_uri="http://localhost:8000/callback",
        )
    
    def test_get_authorization_url(self, auth_service: StravaAuthService):
        """Test authorization URL generation."""
        url = auth_service.get_authorization_url("test_state")
        
        assert "strava.com/oauth/authorize" in url
        assert "client_id=test_id" in url
        assert "state=test_state" in url
        assert "response_type=code" in url
    
    def test_create_jwt_token(self, auth_service: StravaAuthService, mock_strava_token: dict):
        """Test JWT token creation."""
        jwt_token = auth_service.create_jwt_token(mock_strava_token)
        
        assert isinstance(jwt_token, str)
        assert len(jwt_token) > 0
    
    def test_verify_jwt_token(self, auth_service: StravaAuthService, mock_strava_token: dict):
        """Test JWT token verification."""
        jwt_token = auth_service.create_jwt_token(mock_strava_token)
        payload = auth_service.verify_jwt_token(jwt_token)
        
        assert payload["sub"] == "12345"  # Athlete ID from mock
        assert payload["access_token"] == mock_strava_token["access_token"]
    
    def test_is_token_expired_false(self, auth_service: StravaAuthService):
        """Test token expiration check when not expired."""
        import time
        future_time = int(time.time()) + 3600  # 1 hour in future
        
        assert not auth_service.is_token_expired(future_time)
    
    def test_is_token_expired_true(self, auth_service: StravaAuthService):
        """Test token expiration check when expired."""
        import time
        past_time = int(time.time()) - 3600  # 1 hour in past
        
        assert auth_service.is_token_expired(past_time)
    
    def test_is_token_expired_buffer(self, auth_service: StravaAuthService):
        """Test token expiration includes 5 minute buffer."""
        import time
        # 4 minutes in future (within 5 min buffer)
        near_future = int(time.time()) + 240
        
        assert auth_service.is_token_expired(near_future)
    
    @pytest.mark.asyncio
    @respx.mock
    async def test_exchange_code(self, auth_service: StravaAuthService):
        """Test code exchange against a mocked Strava token endpoint."""
        mock_response = {
            "access_token": "new_token",
            "refresh_token": "new_refresh",
            "expires_at": 1735689600,
            "athlete": {"id": 12345},
        }
        route = respx.post("https://www.strava.com/oauth/token").mock(
            return_value=httpx.Response(200, json=mock_response)
        )

        result = await auth_service.exchange_code("test_auth_code")

        assert result == mock_response
        assert route.called
        body = route.calls.last.request.content.decode()
        assert "grant_type=authorization_code" in body
        assert "code=test_auth_code" in body
        assert "client_id=test_id" in body

    @pytest.mark.asyncio
    @respx.mock
    async def test_exchange_code_error_raises(self, auth_service: StravaAuthService):
        """A Strava error response propagates as httpx.HTTPStatusError."""
        respx.post("https://www.strava.com/oauth/token").mock(
            return_value=httpx.Response(400, json={"message": "Bad Request"})
        )
        with pytest.raises(httpx.HTTPStatusError):
            await auth_service.exchange_code("bad_code")

    @pytest.mark.asyncio
    @respx.mock
    async def test_refresh_access_token(self, auth_service: StravaAuthService):
        """Test token refresh against a mocked Strava token endpoint."""
        mock_response = {
            "token_type": "Bearer",
            "access_token": "refreshed_token",
            "refresh_token": "rotated_refresh",
            "expires_at": 1735689600,
            "expires_in": 21600,
        }
        route = respx.post("https://www.strava.com/oauth/token").mock(
            return_value=httpx.Response(200, json=mock_response)
        )

        result = await auth_service.refresh_access_token("old_refresh_token")

        assert result == mock_response
        assert route.called
        body = route.calls.last.request.content.decode()
        assert "grant_type=refresh_token" in body
        assert "refresh_token=old_refresh_token" in body

    @pytest.mark.asyncio
    @respx.mock
    async def test_refresh_access_token_error_raises(
        self, auth_service: StravaAuthService
    ):
        """A Strava refresh failure propagates as httpx.HTTPStatusError."""
        respx.post("https://www.strava.com/oauth/token").mock(
            return_value=httpx.Response(400, json={"message": "Bad Request"})
        )
        with pytest.raises(httpx.HTTPStatusError):
            await auth_service.refresh_access_token("invalid_refresh_token")

    def test_create_jwt_token_with_explicit_athlete_id(
        self, auth_service: StravaAuthService
    ):
        """Refresh responses have no athlete object: explicit id preserves sub."""
        refresh_token_data = {
            "access_token": "refreshed_token",
            "refresh_token": "rotated_refresh",
            "expires_at": 1735689600,
            # No "athlete" key, as in a real Strava refresh response
        }
        token = auth_service.create_jwt_token(refresh_token_data, athlete_id="12345")
        payload = auth_service.verify_jwt_token(token)

        assert payload["sub"] == "12345"
        assert payload["access_token"] == "refreshed_token"
