"""
Shared mapping of upstream Strava API errors to HTTP responses.

Contract:
- Strava 401/403 -> HTTP 401 "Strava authorization failed - please log in again"
- Strava 429     -> HTTP 429 "Strava rate limit exceeded - try again later"
- other 4xx/5xx  -> HTTP 502
"""
import httpx
from fastapi import HTTPException


def map_strava_error(exc: httpx.HTTPStatusError) -> HTTPException:
    """Translate an httpx.HTTPStatusError from Strava into an HTTPException."""
    status = exc.response.status_code
    if status in (401, 403):
        return HTTPException(
            status_code=401,
            detail="Strava authorization failed - please log in again",
        )
    if status == 429:
        return HTTPException(
            status_code=429,
            detail="Strava rate limit exceeded - try again later",
        )
    return HTTPException(
        status_code=502,
        detail=f"Strava API error (HTTP {status})",
    )
