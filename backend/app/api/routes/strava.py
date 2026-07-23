"""
Strava rate-limit status endpoint.

Exposes the latest Strava rate-limit usage that the Strava API service captured
from upstream response headers. This route makes NO Strava call and requires no
auth: it only reads the in-memory snapshot maintained by ``strava_api``, so the
frontend can poll it (and refresh it after a 429) to show a live usage bar
without ever spending part of the rate budget itself.
"""
from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.services.strava_api import get_rate_limit_status, seconds_until_reset

router = APIRouter()


class RateLimitBucket(BaseModel):
    """One rate-limit counter (short-term or daily)."""

    usage: Optional[int] = Field(
        None, description="Requests used in the window (null until first capture)"
    )
    limit: Optional[int] = Field(
        None, description="Request ceiling for the window (null until first capture)"
    )


class RateLimitStatus(BaseModel):
    """Latest captured Strava rate-limit usage plus the next reset countdown."""

    short_term: RateLimitBucket = Field(
        ..., description="15-minute window (default limit 100)"
    )
    daily: RateLimitBucket = Field(
        ..., description="Rolling daily window (default limit 1000)"
    )
    seconds_until_reset: int = Field(
        ...,
        description="Seconds until Strava's wall-clock-aligned 15-min window resets",
    )
    updated_at: Optional[float] = Field(
        None, description="Epoch seconds of the last header capture (null if none yet)"
    )


@router.get("/rate-limit", response_model=RateLimitStatus)
async def get_rate_limit() -> RateLimitStatus:
    """Return the latest captured Strava rate-limit usage (no Strava call)."""
    status = get_rate_limit_status()
    return RateLimitStatus(
        short_term=RateLimitBucket(
            usage=status.get("short_term_usage"),
            limit=status.get("short_term_limit"),
        ),
        daily=RateLimitBucket(
            usage=status.get("daily_usage"),
            limit=status.get("daily_limit"),
        ),
        seconds_until_reset=seconds_until_reset(),
        updated_at=status.get("updated_at"),
    )
