"""
FastAPI dependency injection for services.

The auth chain is JWT-only: the browser sends the KOMHunter session JWT
(never a raw Strava token). ``get_token_payload`` verifies the JWT and
transparently refreshes the embedded Strava token when needed, surfacing
the new session token via the ``X-KOM-Refreshed-Token`` response header.
"""
from typing import Any, Dict, Optional
from functools import lru_cache

import httpx
import jwt
from fastapi import Depends, HTTPException, Header, Response

from app.config import get_settings, Settings
from app.services.strava_auth import StravaAuthService
from app.services.strava_api import StravaAPIService
from app.services.scoring import ScoringService
from app.services.geocoding import GeocodingService


@lru_cache()
def get_strava_auth_service() -> StravaAuthService:
    """Get cached Strava auth service instance."""
    settings = get_settings()
    return StravaAuthService(
        client_id=settings.strava_client_id,
        client_secret=settings.strava_client_secret,
        redirect_uri=settings.strava_redirect_uri,
    )


async def get_token_payload(
    response: Response,
    authorization: Optional[str] = Header(None, description="Bearer JWT session token"),
    auth_service: StravaAuthService = Depends(get_strava_auth_service),
) -> Dict[str, Any]:
    """
    Verify the JWT session token and return its decoded payload.

    - Parses the ``Authorization: Bearer <JWT>`` header (401 on missing or
      malformed header, with the exact legacy messages).
    - Verifies the JWT signature and expiry (401 on failure).
    - If the embedded Strava access token is expired (or expires within the
      5-minute buffer), refreshes it against Strava, mints a NEW JWT that
      preserves the original ``sub``, and exposes it to the client via the
      ``X-KOM-Refreshed-Token`` response header. The returned payload always
      contains a usable (fresh) Strava access token.
    """
    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Authorization header required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Extract token from "Bearer <token>"
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=401,
            detail="Invalid authorization header format",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = parts[1]

    try:
        payload = auth_service.verify_jwt_token(token)
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired session - please log in with Strava again",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if auth_service.is_token_expired(payload["expires_at"]):
        try:
            token_data = await auth_service.refresh_access_token(payload["refresh_token"])
        except httpx.HTTPStatusError as e:
            status = e.response.status_code
            if status == 429:
                # Rate limited upstream: not an auth failure — keep the session
                raise HTTPException(
                    status_code=429,
                    detail="Strava rate limit exceeded - try again later",
                )
            if status >= 500:
                # Strava outage: keep the session so the frontend can retry
                raise HTTPException(
                    status_code=503,
                    detail="Strava is unreachable - try again later",
                )
            # 400/401/403: the refresh token itself is invalid — end the session
            raise HTTPException(
                status_code=401,
                detail="Invalid or expired session - please log in with Strava again",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except httpx.RequestError:
            # Network failure (DNS, timeout, refused) is not an auth failure:
            # 503 so the frontend keeps the session token instead of clearing it
            raise HTTPException(
                status_code=503,
                detail="Strava is unreachable - try again later",
            )

        # RFC 6749 makes refresh_token optional in refresh responses; keep the
        # current one so create_jwt_token never KeyErrors on a minimal response
        token_data.setdefault("refresh_token", payload["refresh_token"])

        # Mint a new JWT preserving the original athlete id (refresh
        # responses carry no "athlete" object) and hand it to the client.
        new_jwt = auth_service.create_jwt_token(token_data, athlete_id=payload["sub"])
        response.headers["X-KOM-Refreshed-Token"] = new_jwt

        payload = {
            **payload,
            "access_token": token_data["access_token"],
            "refresh_token": token_data["refresh_token"],
            "expires_at": token_data["expires_at"],
        }

    return payload


def get_strava_api_service(
    payload: Dict[str, Any] = Depends(get_token_payload),
) -> StravaAPIService:
    """
    Get a Strava API service configured with the session's access token.

    Strict JWT-only: the access token always comes from the verified JWT
    payload — raw Strava tokens in the Authorization header are rejected
    upstream by ``get_token_payload``.
    """
    return StravaAPIService(access_token=payload["access_token"])


@lru_cache()
def get_scoring_service() -> ScoringService:
    """Get cached scoring service instance."""
    return ScoringService()


@lru_cache()
def get_geocoding_service() -> GeocodingService:
    """
    Get cached geocoding service instance.

    Caching the instance (rather than building a fresh one per request) is what
    keeps the service's in-memory ``_cache`` alive across calls, so repeated
    autocomplete lookups for the same query avoid re-hitting Nominatim.
    """
    return GeocodingService()
