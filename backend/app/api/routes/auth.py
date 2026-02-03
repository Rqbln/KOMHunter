"""
Authentication endpoints for Strava OAuth2 flow.
"""
from typing import Optional
from urllib.parse import urlencode
import secrets

from fastapi import APIRouter, HTTPException, Query, Response, Depends
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

from app.config import get_settings
from app.models.auth import TokenResponse, AuthState
from app.services.strava_auth import StravaAuthService
from app.api.dependencies import get_strava_auth_service

router = APIRouter()

# In-memory state storage (use Redis in production)
_auth_states: dict[str, AuthState] = {}


@router.get("/login")
async def login(
    redirect_url: Optional[str] = Query(None, description="URL to redirect after auth"),
    auth_service: StravaAuthService = Depends(get_strava_auth_service),
) -> RedirectResponse:
    """
    Initiate Strava OAuth2 authentication flow.
    
    Generates a state token and redirects the user to Strava's
    authorization page. After authorization, Strava will redirect
    back to the callback endpoint.
    """
    settings = get_settings()
    
    # Generate state for CSRF protection
    state = secrets.token_urlsafe(32)
    _auth_states[state] = AuthState(
        state=state,
        redirect_url=redirect_url or "http://localhost:3000",
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
    then creates a JWT session token and redirects to the frontend.
    """
    # Verify state
    auth_state = _auth_states.pop(state, None)
    if not auth_state:
        raise HTTPException(status_code=400, detail="Invalid or expired state token")
    
    try:
        # Exchange code for tokens
        token_data = await auth_service.exchange_code(code)
        
        # Create JWT session
        jwt_token = auth_service.create_jwt_token(token_data)
        
        # Redirect to frontend with token
        redirect_url = f"{auth_state.redirect_url}?token={jwt_token}"
        return RedirectResponse(url=redirect_url, status_code=302)
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Authentication failed: {str(e)}")


class RefreshTokenRequest(BaseModel):
    """Request body for token refresh."""
    refresh_token: str


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    request: RefreshTokenRequest,
    auth_service: StravaAuthService = Depends(get_strava_auth_service),
) -> TokenResponse:
    """
    Refresh an expired access token using the refresh token.
    
    Returns a new access token and optionally a new refresh token.
    """
    try:
        token_data = await auth_service.refresh_access_token(request.refresh_token)
        return TokenResponse(
            access_token=token_data["access_token"],
            refresh_token=token_data.get("refresh_token", request.refresh_token),
            expires_at=token_data["expires_at"],
            token_type="Bearer",
        )
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Token refresh failed: {str(e)}")


@router.get("/me")
async def get_current_user(
    auth_service: StravaAuthService = Depends(get_strava_auth_service),
    # TODO: Add JWT token dependency
):
    """
    Get the current authenticated user's profile.
    
    Returns the athlete information from Strava.
    """
    # This will be implemented with proper JWT authentication
    raise HTTPException(status_code=501, detail="Not implemented yet")
