"""
Configuration settings for KOMHunter backend.
Uses Pydantic Settings for environment variable management.
"""
from functools import lru_cache
from typing import Optional

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )
    
    # Application
    app_name: str = "KOMHunter API"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    
    # Strava OAuth
    strava_client_id: str
    strava_client_secret: str
    strava_redirect_uri: str = "http://localhost:8000/api/auth/callback"
    strava_scopes: str = "read,read_all,profile:read_all,activity:read_all"
    
    # JWT
    jwt_secret_key: str = "your-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24 * 7  # 7 days
    
    # CORS
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
    
    # Rate Limiting
    rate_limit_per_minute: int = 60
    
    # Cache
    cache_ttl_seconds: int = 300  # 5 minutes
    
    @field_validator("jwt_secret_key")
    @classmethod
    def _reject_placeholder_jwt_secret(cls, value: str) -> str:
        """
        Fail fast at settings load if the JWT signing key is missing or is
        still the insecure placeholder. A weak/known key lets anyone forge
        session JWTs (and the Strava tokens embedded in them), so this must
        never silently fall back to a default in any environment.
        """
        if value is None or not value.strip():
            raise ValueError(
                "JWT_SECRET_KEY must be set to a strong secret "
                "(e.g. `openssl rand -hex 32`)."
            )
        lowered = value.lower()
        if "change" in lowered or "your-secret" in lowered:
            raise ValueError(
                "JWT_SECRET_KEY is set to a placeholder value; generate a real "
                "secret (e.g. `openssl rand -hex 32`) before starting the app."
            )
        return value

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS origins from comma-separated string."""
        return [origin.strip() for origin in self.cors_origins.split(",")]


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
