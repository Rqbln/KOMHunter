"""
Athlete profile and statistics endpoints.
"""
import logging
import math
import time
from collections import OrderedDict
from typing import Any, Dict, List, Optional, Tuple

import httpx
from fastapi import APIRouter, HTTPException, Depends, Query

from app.models.athlete import (
    AthleteProfile,
    AthleteStats,
    ActivityTotals,
    AthleteKOM,
    SegmentEffort,
    StarredSegment,
    KOMsResponse,
    StarredSegmentsResponse,
    PRsResponse,
    HeatmapResponse,
)
from app.services.strava_api import StravaAPIService
from app.services.scoring import ScoringService
from app.api.dependencies import (
    get_strava_api_service,
    get_scoring_service,
    get_token_payload,
)
from app.api.errors import map_strava_error
from app.utils.formatters import format_seconds_to_time
from app.utils.polyline import decode_polyline

router = APIRouter()

logger = logging.getLogger(__name__)

# --- Training-heatmap tuning constants -------------------------------------
# Strava caps activities pagination at 200/page. Using the max keeps the number
# of upstream calls low (rate limits: 100 req/15min, 1000/day).
_HEATMAP_PER_PAGE = 200
# Absolute ceiling on Strava calls per heatmap build, regardless of the
# requested max_activities, so a single request can never exhaust the budget.
_HEATMAP_MAX_PAGES = 5
# Target upper bound on the total number of points returned. Activities are
# down-sampled with a global step so the payload stays JSON-light.
_HEATMAP_TARGET_POINTS = 5000

# Simple in-memory TTL cache keyed by (athlete_id, sport, after, before,
# max_activities). Avoids re-hammering Strava when the frontend toggles filters
# back and forth. Module-level dict, no external deps.
#
# The cache key includes user-controlled query params (after/before are
# arbitrary epoch ints, max_activities 1..500, sport an arbitrary string), so
# without an explicit bound an authenticated user could grow the cache without
# limit by varying those params — each miss stores a HeatmapResponse of up to
# ~5000 points and lazy per-key expiry never reclaims keys that aren't re-read.
# We therefore back the cache with an OrderedDict and enforce two invariants on
# every write: expired entries are swept, and the total entry count is capped
# via least-recently-used eviction. This bounds worst-case memory to
# ``_HEATMAP_CACHE_MAX_ENTRIES`` responses regardless of request patterns.
_HEATMAP_CACHE_TTL = 300.0  # seconds
_HEATMAP_CACHE_MAX_ENTRIES = 128
_HEATMAP_CACHE: "OrderedDict[Tuple, Tuple[float, HeatmapResponse]]" = OrderedDict()


def _heatmap_cache_get(key: Tuple) -> Optional[HeatmapResponse]:
    """Return a cached response for ``key`` if present and not expired."""
    entry = _HEATMAP_CACHE.get(key)
    if entry is None:
        return None
    stored_at, value = entry
    if time.monotonic() - stored_at > _HEATMAP_CACHE_TTL:
        _HEATMAP_CACHE.pop(key, None)
        return None
    # Mark as most-recently-used so it survives LRU eviction longest.
    _HEATMAP_CACHE.move_to_end(key)
    return value


def _heatmap_cache_set(key: Tuple, value: HeatmapResponse) -> None:
    """Store ``value`` under ``key``, keeping the cache bounded.

    On every write we (1) sweep every expired entry so stale keys can't
    accumulate even when they're never re-read, and (2) evict the
    least-recently-used entries until the count is within
    ``_HEATMAP_CACHE_MAX_ENTRIES``. This caps worst-case memory regardless of
    how many distinct (user-controlled) cache keys are generated.
    """
    now = time.monotonic()

    # Sweep expired entries (list() snapshots keys so we can mutate while iterating).
    for cached_key, (stored_at, _) in list(_HEATMAP_CACHE.items()):
        if now - stored_at > _HEATMAP_CACHE_TTL:
            _HEATMAP_CACHE.pop(cached_key, None)

    # Insert/refresh and mark most-recently-used.
    _HEATMAP_CACHE[key] = (now, value)
    _HEATMAP_CACHE.move_to_end(key)

    # Enforce the hard size cap via LRU eviction (oldest first).
    while len(_HEATMAP_CACHE) > _HEATMAP_CACHE_MAX_ENTRIES:
        _HEATMAP_CACHE.popitem(last=False)


def _matches_sport(activity_type: Optional[str], sport: Optional[str]) -> bool:
    """
    Whether a Strava activity ``type`` matches the requested sport filter.

    Strava types look like "Ride", "VirtualRide", "EBikeRide", "Run",
    "TrailRun", "VirtualRun". A substring match on the normalized type keeps
    all ride/run variants while excluding the other discipline.
    """
    if not sport:
        return True
    normalized = (activity_type or "").lower()
    if sport == "ride":
        return "ride" in normalized
    if sport == "run":
        return "run" in normalized
    # Unknown sport value: don't filter anything out.
    return True


def parse_activity_totals(data: Optional[dict]) -> Optional[ActivityTotals]:
    """Parse activity totals from Strava API response."""
    if not data:
        return None
    return ActivityTotals(
        count=data.get("count", 0),
        distance=data.get("distance", 0),
        moving_time=data.get("moving_time", 0),
        elapsed_time=data.get("elapsed_time", 0),
        elevation_gain=data.get("elevation_gain", 0),
        achievement_count=data.get("achievement_count"),
    )


@router.get("/me", response_model=AthleteProfile)
async def get_my_profile(
    strava_service: StravaAPIService = Depends(get_strava_api_service),
) -> AthleteProfile:
    """
    Get the authenticated athlete's profile.
    
    Returns profile information including name, location, and stats.
    """
    try:
        athlete_data = await strava_service.get_athlete()
        
        return AthleteProfile(
            id=athlete_data["id"],
            firstname=athlete_data.get("firstname", ""),
            lastname=athlete_data.get("lastname", ""),
            profile=athlete_data.get("profile", ""),
            profile_medium=athlete_data.get("profile_medium", ""),
            city=athlete_data.get("city", ""),
            state=athlete_data.get("state", ""),
            country=athlete_data.get("country", ""),
            sex=athlete_data.get("sex", ""),
            premium=athlete_data.get("premium", False),
            created_at=athlete_data.get("created_at", ""),
            updated_at=athlete_data.get("updated_at", ""),
        )
        
    except HTTPException:
        raise
    except httpx.HTTPStatusError as e:
        raise map_strava_error(e) from e
    except Exception:
        logger.exception("Failed to get athlete profile")
        raise HTTPException(status_code=500, detail="Failed to get athlete profile")


@router.get("/me/stats", response_model=AthleteStats)
async def get_my_stats(
    strava_service: StravaAPIService = Depends(get_strava_api_service),
) -> AthleteStats:
    """
    Get the authenticated athlete's statistics.
    
    Returns activity totals and records.
    """
    try:
        # First get athlete ID
        athlete_data = await strava_service.get_athlete()
        athlete_id = athlete_data["id"]
        
        # Then get stats
        stats_data = await strava_service.get_athlete_stats(athlete_id)
        
        return AthleteStats(
            biggest_ride_distance=stats_data.get("biggest_ride_distance"),
            biggest_climb_elevation_gain=stats_data.get("biggest_climb_elevation_gain"),
            recent_ride_totals=parse_activity_totals(stats_data.get("recent_ride_totals")),
            recent_run_totals=parse_activity_totals(stats_data.get("recent_run_totals")),
            ytd_ride_totals=parse_activity_totals(stats_data.get("ytd_ride_totals")),
            ytd_run_totals=parse_activity_totals(stats_data.get("ytd_run_totals")),
            all_ride_totals=parse_activity_totals(stats_data.get("all_ride_totals")),
            all_run_totals=parse_activity_totals(stats_data.get("all_run_totals")),
        )
        
    except HTTPException:
        raise
    except httpx.HTTPStatusError as e:
        raise map_strava_error(e) from e
    except Exception:
        logger.exception("Failed to get athlete stats")
        raise HTTPException(status_code=500, detail="Failed to get athlete stats")


@router.get("/me/koms", response_model=KOMsResponse)
async def get_my_koms(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(30, ge=1, le=100, description="Items per page"),
    strava_service: StravaAPIService = Depends(get_strava_api_service),
) -> KOMsResponse:
    """
    Get the authenticated athlete's KOMs/QOMs.
    
    Returns segments where the athlete holds a KOM or QOM.
    """
    try:
        # First get athlete ID
        athlete_data = await strava_service.get_athlete()
        athlete_id = athlete_data["id"]
        
        # Get KOMs
        koms_data = await strava_service.list_athlete_koms(
            athlete_id=athlete_id,
            page=page,
            per_page=per_page,
        )
        
        # Transform to response model
        koms = []
        for entry in koms_data:
            segment = entry.get("segment", {})
            koms.append(AthleteKOM(
                segment_id=segment.get("id", 0),
                segment_name=segment.get("name", "Unknown"),
                activity_id=entry.get("activity_id", 0),
                elapsed_time=entry.get("elapsed_time", 0),
                elapsed_time_formatted=entry.get("elapsed_time_formatted", ""),
                distance=segment.get("distance", 0),
                avg_grade=segment.get("average_grade", 0),
                start_date=entry.get("start_date", ""),
                start_date_local=entry.get("start_date_local", ""),
                kom_rank=entry.get("kom_rank"),
            ))
        
        return KOMsResponse(
            koms=koms,
            total_count=len(koms),  # Strava doesn't return total count
            page=page,
            per_page=per_page,
        )
        
    except HTTPException:
        raise
    except httpx.HTTPStatusError as e:
        raise map_strava_error(e) from e
    except Exception:
        logger.exception("Failed to get KOMs")
        raise HTTPException(status_code=500, detail="Failed to get KOMs")


@router.get("/me/starred", response_model=StarredSegmentsResponse)
async def get_my_starred_segments(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(30, ge=1, le=100, description="Items per page"),
    strava_service: StravaAPIService = Depends(get_strava_api_service),
) -> StarredSegmentsResponse:
    """
    Get the authenticated athlete's starred (favorite) segments.
    """
    try:
        starred_data = await strava_service.list_starred_segments(
            page=page,
            per_page=per_page,
        )
        
        # Transform to response model
        segments = []
        for seg in starred_data:
            segments.append(StarredSegment(
                id=seg.get("id", 0),
                name=seg.get("name", "Unknown"),
                distance=seg.get("distance", 0),
                avg_grade=seg.get("average_grade", 0),
                elev_difference=seg.get("elevation_high", 0) - seg.get("elevation_low", 0),
                climb_category=seg.get("climb_category", 0),
                city=seg.get("city", ""),
                state=seg.get("state", ""),
                country=seg.get("country", ""),
                activity_type=seg.get("activity_type", "Ride"),
                starred_date=seg.get("starred_date", ""),
                athlete_pr_effort=seg.get("athlete_pr_effort"),
            ))
        
        return StarredSegmentsResponse(
            segments=segments,
            total_count=len(segments),
            page=page,
            per_page=per_page,
        )
        
    except HTTPException:
        raise
    except httpx.HTTPStatusError as e:
        raise map_strava_error(e) from e
    except Exception:
        logger.exception("Failed to get starred segments")
        raise HTTPException(status_code=500, detail="Failed to get starred segments")


@router.get("/me/prs", response_model=PRsResponse)
async def get_my_prs(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(30, ge=1, le=100, description="Items per page"),
    strava_service: StravaAPIService = Depends(get_strava_api_service),
) -> PRsResponse:
    """
    Get the authenticated athlete's Personal Records (PRs).
    
    Returns recent activities with segment PRs.
    Note: This endpoint aggregates PRs from recent activities.
    """
    try:
        # Get recent activities
        activities = await strava_service.list_athlete_activities(
            page=page,
            per_page=per_page,
        )
        
        # Collect PRs from activities
        prs = []
        for activity in activities:
            # Each activity may have segment_efforts with PRs
            segment_efforts = activity.get("segment_efforts", [])
            for effort in segment_efforts:
                # Check if this is a PR (pr_rank = 1)
                pr_rank = effort.get("pr_rank")
                if pr_rank and pr_rank <= 3:  # Include top 3 PRs
                    segment = effort.get("segment", {})
                    prs.append(SegmentEffort(
                        id=effort.get("id", 0),
                        segment_id=segment.get("id", 0),
                        segment_name=segment.get("name", "Unknown"),
                        activity_id=activity.get("id", 0),
                        elapsed_time=effort.get("elapsed_time", 0),
                        elapsed_time_formatted=format_seconds_to_time(effort.get("elapsed_time", 0)),
                        moving_time=effort.get("moving_time", 0),
                        start_date=effort.get("start_date", ""),
                        start_date_local=effort.get("start_date_local", ""),
                        distance=effort.get("distance", 0),
                        pr_rank=pr_rank,
                        kom_rank=effort.get("kom_rank"),
                        achievements=effort.get("achievements"),
                    ))
        
        # Sort by date (most recent first)
        prs.sort(key=lambda x: x.start_date, reverse=True)
        
        return PRsResponse(
            prs=prs[:per_page],  # Limit to per_page
            total_count=len(prs),
            page=page,
            per_page=per_page,
        )
        
    except HTTPException:
        raise
    except httpx.HTTPStatusError as e:
        raise map_strava_error(e) from e
    except Exception:
        logger.exception("Failed to get PRs")
        raise HTTPException(status_code=500, detail="Failed to get PRs")


@router.get("/me/heatmap", response_model=HeatmapResponse)
async def get_my_heatmap(
    sport: Optional[str] = Query(
        None, description="Filter by sport: 'ride', 'run', or omit for all"
    ),
    after: Optional[int] = Query(
        None,
        ge=0,
        description="Only include activities after this epoch timestamp",
    ),
    before: Optional[int] = Query(
        None,
        ge=0,
        description="Only include activities before this epoch timestamp",
    ),
    max_activities: int = Query(
        200,
        ge=1,
        le=500,
        description="Maximum number of activities to aggregate (cap)",
    ),
    payload: Dict[str, Any] = Depends(get_token_payload),
    strava_service: StravaAPIService = Depends(get_strava_api_service),
) -> HeatmapResponse:
    """
    Build a training heatmap from the athlete's activity summary polylines.

    Fetches recent activities (paginated, with a hard cap on Strava calls),
    decodes each activity's ``map.summary_polyline`` and down-samples the
    combined point set so the payload stays light. Results are cached
    in-memory for a short TTL keyed by the athlete and filters, so repeated
    filter toggles don't re-hammer Strava.
    """
    sport_norm = sport.lower() if sport else None
    athlete_id = payload.get("sub")
    cache_key = (athlete_id, sport_norm, after, before, max_activities)

    cached = _heatmap_cache_get(cache_key)
    if cached is not None:
        return cached

    try:
        # Bound the number of Strava calls: never more than what's needed to
        # reach max_activities, and never more than the hard page cap.
        max_pages = min(
            _HEATMAP_MAX_PAGES,
            math.ceil(max_activities / _HEATMAP_PER_PAGE),
        )

        activities: List[dict] = []
        for page in range(1, max_pages + 1):
            batch = await strava_service.list_athlete_activities(
                page=page,
                per_page=_HEATMAP_PER_PAGE,
                after=after,
                before=before,
            )
            if not batch:
                break
            activities.extend(batch)
            # A short page means Strava has no more data — stop paginating.
            if len(batch) < _HEATMAP_PER_PAGE:
                break
            if len(activities) >= max_activities:
                break

        activities = activities[:max_activities]

        # Decode the polyline of every activity matching the sport filter.
        decoded_tracks: List[list] = []
        for activity in activities:
            if not _matches_sport(activity.get("type"), sport_norm):
                continue
            map_data = activity.get("map") or {}
            encoded = map_data.get("summary_polyline")
            if not encoded:
                continue
            track = decode_polyline(encoded)
            if not track:
                continue
            decoded_tracks.append(track)

        # Global down-sample step so the total point count stays bounded.
        total_points = sum(len(track) for track in decoded_tracks)
        step = 1
        if total_points > _HEATMAP_TARGET_POINTS:
            step = math.ceil(total_points / _HEATMAP_TARGET_POINTS)

        points: List[List[float]] = []
        for track in decoded_tracks:
            for i in range(0, len(track), step):
                lat, lng = track[i]
                points.append([lat, lng])

        result = HeatmapResponse(
            points=points,
            activity_count=len(decoded_tracks),
            sport=sport_norm,
        )
        _heatmap_cache_set(cache_key, result)
        return result

    except HTTPException:
        raise
    except httpx.HTTPStatusError as e:
        raise map_strava_error(e) from e
    except Exception:
        logger.exception("Failed to build training heatmap")
        raise HTTPException(
            status_code=500, detail="Failed to build training heatmap"
        )
