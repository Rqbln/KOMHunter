"""
Pydantic models for authentication.
"""
from typing import Optional
from datetime import datetime

from pydantic import BaseModel, Field


class AuthState(BaseModel):
    """OAuth state for CSRF protection."""
    
    state: str = Field(..., description="Random state token")
    redirect_url: str = Field(..., description="URL to redirect after auth")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class TokenResponse(BaseModel):
    """OAuth token response."""
    
    access_token: str = Field(..., description="Strava access token")
    refresh_token: str = Field(..., description="Strava refresh token")
    expires_at: int = Field(..., description="Token expiration timestamp")
    token_type: str = Field("Bearer", description="Token type")
    
    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "abc123...",
                "refresh_token": "xyz789...",
                "expires_at": 1704067200,
                "token_type": "Bearer",
            }
        }


class SessionRefreshRequest(BaseModel):
    """Request body for session (JWT) refresh."""

    token: str = Field(..., description="Current KOMHunter JWT session token")


class SessionTokenResponse(BaseModel):
    """Response containing a freshly minted JWT session token."""

    token: str = Field(..., description="New KOMHunter JWT session token")


class SessionInfoResponse(BaseModel):
    """Current session information (no Strava network call)."""

    athlete_id: str = Field(..., description="Strava athlete ID (JWT subject)")
    strava_token_expires_at: int = Field(
        ..., description="Embedded Strava access token expiration timestamp"
    )
    session_expires_at: int = Field(..., description="JWT session expiration timestamp")
    strava_token_expired: bool = Field(
        ..., description="Whether the embedded Strava token is expired (5-min buffer)"
    )


class JWTPayload(BaseModel):
    """JWT token payload."""
    
    sub: str = Field(..., description="Subject (athlete ID)")
    access_token: str = Field(..., description="Strava access token")
    refresh_token: str = Field(..., description="Strava refresh token")
    expires_at: int = Field(..., description="Strava token expiration")
    iat: int = Field(..., description="Issued at timestamp")
    exp: int = Field(..., description="JWT expiration timestamp")
