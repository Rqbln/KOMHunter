"""
FastAPI dependency injection for services.
"""
from typing import Optional
from functools import lru_cache

from fastapi import Depends, HTTPException, Header

from app.config import get_settings, Settings
from app.services.strava_auth import StravaAuthService
from app.services.strava_api import StravaAPIService
from app.services.scoring import ScoringService


@lru_cache()
def get_strava_auth_service() -> StravaAuthService:
    """Get cached Strava auth service instance."""
    settings = get_settings()
    return StravaAuthService(
        client_id=settings.strava_client_id,
        client_secret=settings.strava_client_secret,
        redirect_uri=settings.strava_redirect_uri,
    )


def get_strava_api_service(
    authorization: Optional[str] = Header(None, description="Bearer token"),
) -> StravaAPIService:
    """
    Get Strava API service with access token from header.
    
    Extracts the access token from the Authorization header
    and creates a configured StravaAPIService instance.
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
    
    access_token = parts[1]
    return StravaAPIService(access_token=access_token)


@lru_cache()
def get_scoring_service() -> ScoringService:
    """Get cached scoring service instance."""
    return ScoringService()
