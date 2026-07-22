"""
Strava OAuth2 authentication service.

Handles the complete OAuth2 flow including authorization URL generation,
code exchange, and token refresh.
"""
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from urllib.parse import urlencode
import time

import httpx
import jwt

from app.config import get_settings


class StravaAuthService:
    """Service for Strava OAuth2 authentication."""
    
    AUTHORIZE_URL = "https://www.strava.com/oauth/authorize"
    TOKEN_URL = "https://www.strava.com/oauth/token"
    
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
    ):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.settings = get_settings()
    
    def get_authorization_url(self, state: str) -> str:
        """
        Generate Strava OAuth authorization URL.
        
        Args:
            state: Random state token for CSRF protection
            
        Returns:
            Full authorization URL for redirect
        """
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "approval_prompt": "auto",
            "scope": self.settings.strava_scopes,
            "state": state,
        }
        return f"{self.AUTHORIZE_URL}?{urlencode(params)}"
    
    async def exchange_code(self, code: str) -> Dict[str, Any]:
        """
        Exchange authorization code for access and refresh tokens.
        
        Args:
            code: Authorization code from Strava callback
            
        Returns:
            Token response containing access_token, refresh_token, expires_at
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.TOKEN_URL,
                data={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "code": code,
                    "grant_type": "authorization_code",
                },
            )
            response.raise_for_status()
            return response.json()
    
    async def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        Refresh an expired access token.
        
        Args:
            refresh_token: Valid refresh token
            
        Returns:
            New token response with fresh access_token
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.TOKEN_URL,
                data={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "refresh_token": refresh_token,
                    "grant_type": "refresh_token",
                },
            )
            response.raise_for_status()
            return response.json()
    
    def create_jwt_token(
        self,
        token_data: Dict[str, Any],
        athlete_id: Optional[str] = None,
    ) -> str:
        """
        Create a JWT session token from Strava token data.

        Args:
            token_data: Token response from Strava containing tokens and athlete info
            athlete_id: Explicit athlete ID to use as the JWT subject. Required
                when token_data has no "athlete" object (Strava token *refresh*
                responses don't include one) to preserve the original subject.

        Returns:
            Signed JWT token string
        """
        now = int(time.time())
        expire = now + (self.settings.jwt_expire_minutes * 60)

        # Prefer the explicit athlete ID, else extract it from the token response
        if athlete_id is None:
            athlete_id = str(token_data.get("athlete", {}).get("id", "unknown"))
        
        payload = {
            "sub": athlete_id,
            "access_token": token_data["access_token"],
            "refresh_token": token_data["refresh_token"],
            "expires_at": token_data["expires_at"],
            "iat": now,
            "exp": expire,
        }
        
        return jwt.encode(
            payload,
            self.settings.jwt_secret_key,
            algorithm=self.settings.jwt_algorithm,
        )
    
    def verify_jwt_token(self, token: str) -> Dict[str, Any]:
        """
        Verify and decode a JWT token.
        
        Args:
            token: JWT token string
            
        Returns:
            Decoded payload
            
        Raises:
            jwt.InvalidTokenError: If token is invalid or expired
        """
        return jwt.decode(
            token,
            self.settings.jwt_secret_key,
            algorithms=[self.settings.jwt_algorithm],
        )
    
    def is_token_expired(self, expires_at: int) -> bool:
        """
        Check if a Strava token is expired.
        
        Args:
            expires_at: Token expiration timestamp
            
        Returns:
            True if token is expired or will expire within 5 minutes
        """
        # Add 5 minute buffer
        return time.time() > (expires_at - 300)
