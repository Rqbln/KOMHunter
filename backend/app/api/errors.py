"""
Shared mapping of upstream Strava API errors to HTTP responses.

Contract:
- Strava 401/403 -> HTTP 401 "Strava authorization failed - please log in again"
- Strava 429     -> HTTP 429 "Strava rate limit exceeded - retry in {n}s" with a
                    Retry-After header (n = seconds until the 15-min window resets)
- other 4xx/5xx  -> HTTP 502
"""
import httpx
from fastapi import HTTPException

from app.services.strava_api import _capture_rate_limit, seconds_until_reset


def map_strava_error(exc: httpx.HTTPStatusError) -> HTTPException:
    """Translate an httpx.HTTPStatusError from Strava into an HTTPException."""
    status = exc.response.status_code
    if status in (401, 403):
        return HTTPException(
            status_code=401,
            detail="Strava authorization failed - please log in again",
        )
    if status == 429:
        # The 429 response still carries the X-RateLimit-* usage headers; capture
        # them so the usage bar reflects the exhausted state immediately, then
        # tell the client exactly how long to wait (Strava's 15-min window is
        # wall-clock aligned, so this is the true cooldown).
        _capture_rate_limit(exc.response.headers)
        cooldown = seconds_until_reset()
        return HTTPException(
            status_code=429,
            detail=f"Strava rate limit exceeded - retry in {cooldown}s",
            headers={"Retry-After": str(cooldown)},
        )
    return HTTPException(
        status_code=502,
        detail=f"Strava API error (HTTP {status})",
    )
