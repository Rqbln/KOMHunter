"""
Authentication endpoints for Strava OAuth2 flow.

The browser only ever holds the KOMHunter session JWT ("kom_token") —
raw Strava tokens stay server-side, embedded in the signed JWT payload.
"""
from typing import Any, Dict, Optional
from urllib.parse import urlsplit, urlunsplit
import logging
import secrets

import httpx
import jwt
from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.responses import RedirectResponse

from app.config import get_settings
from app.models.auth import (
    AuthState,
    SessionInfoResponse,
    SessionRefreshRequest,
    SessionTokenResponse,
)
from app.services.strava_auth import StravaAuthService
from app.api.dependencies import get_strava_auth_service, get_token_payload

router = APIRouter()

logger = logging.getLogger(__name__)

# In-memory state storage (use Redis in production)
_auth_states: dict[str, AuthState] = {}


def _validate_redirect_url(redirect_url: Optional[str]) -> str:
    """
    Enforce an origin allowlist on the post-auth redirect target.

    The OAuth callback appends the session JWT to this URL, so an
    unvalidated value is an open redirect that exfiltrates the token
    (and the Strava tokens embedded in it) to an attacker-controlled
    host. Only the configured frontend origins (CORS origins) may
    receive the token; anything else is rejected with 400.

    Returns the validated URL with any fragment stripped, so the
    ``#token=`` fragment appended later is never ambiguous.
    """
    settings = get_settings()
    # Drop blank entries so an empty/misconfigured CORS_ORIGINS cannot yield an
    # empty allowlist (and never IndexErrors on the default-origin branch below).
    configured_origins = [o.rstrip("/") for o in settings.cors_origins_list if o.strip()]
    if not configured_origins:
        raise HTTPException(
            status_code=500,
            detail="Server misconfiguration: no allowed origins configured",
        )
    allowed_origins = {o.lower() for o in configured_origins}

    if not redirect_url:
        # Default to the first configured frontend origin
        return configured_origins[0]

    # Browsers treat "\" as "/" in URLs but urlsplit does not — reject outright
    if "\\" in redirect_url:
        raise HTTPException(
            status_code=400, detail="redirect_url is not an allowed origin"
        )

    parts = urlsplit(redirect_url)
    origin = f"{parts.scheme}://{parts.netloc}".lower()
    if parts.scheme not in ("http", "https") or not parts.netloc or origin not in allowed_origins:
        raise HTTPException(
            status_code=400, detail="redirect_url is not an allowed origin"
        )

    # Preserve path/query, drop any pre-existing fragment
    return urlunsplit((parts.scheme, parts.netloc, parts.path, parts.query, ""))


@router.get("/login")
async def login(
    redirect_url: Optional[str] = Query(None, description="URL to redirect after auth"),
    auth_service: StravaAuthService = Depends(get_strava_auth_service),
) -> RedirectResponse:
    """
    Initiate Strava OAuth2 authentication flow.

    Generates a state token and redirects the user to Strava's
    authorization page. After authorization, Strava will redirect
    back to the callback endpoint. The redirect_url is validated
    against the configured frontend origins (open-redirect guard).
    """
    # Generate state for CSRF protection
    state = secrets.token_urlsafe(32)
    _auth_states[state] = AuthState(
        state=state,
        redirect_url=_validate_redirect_url(redirect_url),
    )

    # Build authorization URL
    auth_url = auth_service.get_authorization_url(state)

    return RedirectResponse(url=auth_url, status_code=302)


@router.get("/callback")
async def callback(
    code: str = Query(..., description="Authorization code from Strava"),
    state: str = Query(..., description="State token for CSRF verification"),
    scope: Optional[str] = Query(None, description="Granted scopes"),
    auth_service: StravaAuthService = Depends(get_strava_auth_service),
) -> RedirectResponse:
    """
    Handle OAuth2 callback from Strava.

    Exchanges the authorization code for access and refresh tokens,
    then creates a JWT session token and redirects to the frontend with
    the token in the URL hash fragment (kept out of server logs/history).
    """
    # Verify state
    auth_state = _auth_states.pop(state, None)
    if not auth_state:
        raise HTTPException(status_code=400, detail="Invalid or expired state token")

    # Defense in depth: re-check the stored redirect target against the
    # origin allowlist before a token is ever attached to it
    safe_redirect_url = _validate_redirect_url(auth_state.redirect_url)

    try:
        # Exchange code for tokens
        token_data = await auth_service.exchange_code(code)

        # Create JWT session
        jwt_token = auth_service.create_jwt_token(token_data)

        # Redirect to frontend with token in the hash fragment (not query string)
        redirect_url = f"{safe_redirect_url}#token={jwt_token}"
        return RedirectResponse(url=redirect_url, status_code=302)

    except HTTPException:
        raise
    except Exception:
        logger.exception("OAuth callback failed during code exchange / session mint")
        raise HTTPException(status_code=400, detail="Authentication failed")


@router.post("/refresh", response_model=SessionTokenResponse)
async def refresh_session(
    request: SessionRefreshRequest,
    auth_service: StravaAuthService = Depends(get_strava_auth_service),
) -> SessionTokenResponse:
    """
    Refresh a KOMHunter session: JWT in, JWT out.

    The JWT signature is always verified, but the ``exp`` check is disabled
    so a session whose JWT lapsed can still be renewed via the embedded
    Strava refresh token. No raw Strava tokens are ever returned.
    """
    settings = get_settings()

    try:
        payload = jwt.decode(
            request.token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
            options={"verify_exp": False},
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired session - please log in with Strava again",
        )

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
        )
    except httpx.RequestError:
        raise HTTPException(
            status_code=503,
            detail="Strava is unreachable - try again later",
        )

    # refresh_token is optional in RFC 6749 refresh responses
    token_data.setdefault("refresh_token", payload["refresh_token"])

    # Refresh responses have no "athlete" object: preserve the original subject
    new_jwt = auth_service.create_jwt_token(token_data, athlete_id=payload["sub"])
    return SessionTokenResponse(token=new_jwt)


@router.get("/me", response_model=SessionInfoResponse)
async def get_session_info(
    payload: Dict[str, Any] = Depends(get_token_payload),
    auth_service: StravaAuthService = Depends(get_strava_auth_service),
) -> SessionInfoResponse:
    """
    Get information about the current session.

    Reads the verified JWT payload. If the embedded Strava token is stale,
    ``get_token_payload`` transparently refreshes it (one Strava call) and
    surfaces the new session JWT via ``X-KOM-Refreshed-Token``.
    """
    return SessionInfoResponse(
        athlete_id=payload["sub"],
        strava_token_expires_at=payload["expires_at"],
        session_expires_at=payload["exp"],
        strava_token_expired=auth_service.is_token_expired(payload["expires_at"]),
    )
