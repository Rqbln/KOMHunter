"""
Strava API service for segment and athlete data.

Handles all interactions with the Strava REST API including
segment exploration, details, and leaderboards.
"""
import asyncio
import logging
import math
import time
from typing import Dict, Any, List, Optional, Tuple

import httpx

from app.utils.polyline import decode_polyline
from app.utils.formatters import format_seconds_to_time

logger = logging.getLogger(__name__)

# Strava /segments/explore returns at most ~10 segments per bounding box, so to
# retrieve more we tile the search area into a small grid of sub-boxes.
_EXPLORE_PER_BOX = 10          # observed per-bbox cap from Strava
_MAX_TILES_PER_SIDE = 4        # hard cap: 4x4 = 16 tiles (protect 100 req/15min)
_TILE_CONCURRENCY = 5          # bounded concurrent explore calls

# Strava's short-term rate-limit window is a wall-clock-aligned 15-minute
# (900-second) bucket: it resets at :00, :15, :30, :45 past the hour, not 15
# minutes after your first call.
_RATE_LIMIT_WINDOW = 900

# Latest rate-limit usage captured from Strava response headers. Strava returns
# these on EVERY response (including 429s): X-RateLimit-Limit / X-RateLimit-Usage
# are the general "100,1000" short,daily counters, and X-ReadRateLimit-* mirror
# them for read requests specifically. All our calls are reads, so we prefer the
# read-specific values when present and fall back to the general ones. Values
# stay None until the first successful capture.
_RATE_LIMIT: Dict[str, Any] = {
    "short_term_usage": None,
    "short_term_limit": None,
    "daily_usage": None,
    "daily_limit": None,
    "updated_at": None,
}


def get_rate_limit_status() -> Dict[str, Any]:
    """Return a shallow copy of the latest captured rate-limit snapshot."""
    return dict(_RATE_LIMIT)


def seconds_until_reset() -> int:
    """Seconds until Strava's wall-clock-aligned 15-minute window resets."""
    return _RATE_LIMIT_WINDOW - (int(time.time()) % _RATE_LIMIT_WINDOW)


def _parse_limit_pair(value: Optional[str]) -> Tuple[Optional[int], Optional[int]]:
    """Parse a Strava ``"short,daily"`` header into two ints.

    Returns ``(None, None)`` when the header is missing or garbled so the caller
    can leave the previously captured values untouched.
    """
    if not value:
        return None, None
    parts = value.split(",")
    if len(parts) < 2:
        return None, None
    try:
        return int(parts[0].strip()), int(parts[1].strip())
    except (ValueError, TypeError):
        return None, None


def _capture_rate_limit(headers: Any) -> None:
    """Update ``_RATE_LIMIT`` from a Strava response's headers (best-effort).

    Prefers the read-specific headers (our calls are all reads) and falls back
    to the general counters. Missing or unparseable headers leave the prior
    values intact rather than clobbering them with ``None``.
    """
    read_usage = headers.get("X-ReadRateLimit-Usage")
    read_limit = headers.get("X-ReadRateLimit-Limit")
    usage_su, usage_du = _parse_limit_pair(
        read_usage if read_usage else headers.get("X-RateLimit-Usage")
    )
    limit_sl, limit_dl = _parse_limit_pair(
        read_limit if read_limit else headers.get("X-RateLimit-Limit")
    )

    updated = False
    if usage_su is not None and usage_du is not None:
        _RATE_LIMIT["short_term_usage"] = usage_su
        _RATE_LIMIT["daily_usage"] = usage_du
        updated = True
    if limit_sl is not None and limit_dl is not None:
        _RATE_LIMIT["short_term_limit"] = limit_sl
        _RATE_LIMIT["daily_limit"] = limit_dl
        updated = True
    if updated:
        _RATE_LIMIT["updated_at"] = time.time()


class StravaAPIService:
    """Service for Strava API interactions."""

    BASE_URL = "https://www.strava.com/api/v3"
    
    def __init__(self, access_token: str):
        """
        Initialize with access token.
        
        Args:
            access_token: Valid Strava access token
        """
        self.access_token = access_token
        self.headers = {"Authorization": f"Bearer {access_token}"}
    
    async def _request(
        self, 
        method: str, 
        endpoint: str, 
        params: Optional[Dict] = None,
        data: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """
        Make an authenticated request to the Strava API.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint (without base URL)
            params: Query parameters
            data: Request body data
            
        Returns:
            JSON response from API
        """
        url = f"{self.BASE_URL}{endpoint}"
        
        async with httpx.AsyncClient() as client:
            response = await client.request(
                method=method,
                url=url,
                headers=self.headers,
                params=params,
                data=data,
                timeout=30.0,
            )
            # Capture rate-limit usage from EVERY response — including 429s —
            # BEFORE raise_for_status() can short-circuit and discard them.
            _capture_rate_limit(response.headers)
            response.raise_for_status()
            return response.json()
    
    async def get_athlete(self) -> Dict[str, Any]:
        """
        Get the authenticated athlete's profile.
        
        Returns:
            Athlete data from Strava
        """
        return await self._request("GET", "/athlete")
    
    async def explore_segments(
        self,
        lat: float,
        lon: float,
        radius_km: float = 10,
        activity_type: str = "riding",
        max_segments: int = 50,
        min_cat: int = 0,
        max_cat: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Explore segments in a given area.

        Args:
            lat: Center latitude
            lon: Center longitude
            radius_km: Search radius in kilometers
            activity_type: 'riding' or 'running'
            max_segments: Maximum segments to return
            min_cat: Minimum Strava climb category (0-5)
            max_cat: Maximum Strava climb category (0-5)

        Returns:
            List of segment summaries
        """
        # Convert radius to an approximate bounding box.
        # 1 degree of latitude ≈ 111 km everywhere. Longitude degrees shrink with
        # latitude (they converge at the poles), so a fixed lon delta would make
        # the box far too wide away from the equator; divide by cos(lat) to keep
        # the box roughly square in real-world distance.
        lat_delta = radius_km / 111.0
        lon_delta = radius_km / (111.0 * max(math.cos(math.radians(lat)), 0.01))

        # Params shared by every tile call; only "bounds" differs per tile.
        common_params = {
            "activity_type": activity_type.lower(),
            "min_cat": min_cat,
            "max_cat": max_cat,
        }

        # Small requests fit in a single bounding box — avoid needless calls.
        if max_segments <= _EXPLORE_PER_BOX:
            bounds = (
                f"{lat - lat_delta},{lon - lon_delta},"
                f"{lat + lat_delta},{lon + lon_delta}"
            )
            response = await self._request(
                "GET", "/segments/explore", params={"bounds": bounds, **common_params}
            )
            segments = response.get("segments", [])
            return segments[:max_segments]

        # Tile the radius box into an N×N grid. N grows with the requested count
        # but is hard-capped at 4 (=> at most 16 tiles) to protect the rate limit.
        n = min(
            _MAX_TILES_PER_SIDE,
            max(1, math.ceil(math.sqrt(max_segments / _EXPLORE_PER_BOX))),
        )

        south = lat - lat_delta
        west = lon - lon_delta
        tile_lat = (2 * lat_delta) / n
        tile_lon = (2 * lon_delta) / n

        tile_bounds: List[str] = []
        for i in range(n):
            for j in range(n):
                t_south = south + i * tile_lat
                t_north = south + (i + 1) * tile_lat
                t_west = west + j * tile_lon
                t_east = west + (j + 1) * tile_lon
                tile_bounds.append(f"{t_south},{t_west},{t_north},{t_east}")

        logger.info(
            "explore_segments: querying %d tiles (%dx%d grid) for max_segments=%d",
            len(tile_bounds),
            n,
            n,
            max_segments,
        )

        # Fire the per-tile explore calls concurrently under a bounded semaphore.
        # Upstream errors (401/429/5xx) propagate so the route can map them.
        semaphore = asyncio.Semaphore(_TILE_CONCURRENCY)

        async def _fetch_tile(bounds: str) -> List[Dict[str, Any]]:
            async with semaphore:
                response = await self._request(
                    "GET",
                    "/segments/explore",
                    params={"bounds": bounds, **common_params},
                )
                return response.get("segments", [])

        tile_results = await asyncio.gather(
            *(_fetch_tile(b) for b in tile_bounds)
        )

        # Merge, deduping by segment id (a segment can appear in adjacent tiles).
        merged: Dict[Any, Dict[str, Any]] = {}
        for segments in tile_results:
            for segment in segments:
                seg_id = segment.get("id")
                if seg_id is not None and seg_id not in merged:
                    merged[seg_id] = segment

        return list(merged.values())[:max_segments]
    
    async def get_segment_details(self, segment_id: int) -> Dict[str, Any]:
        """
        Get detailed information about a specific segment.
        
        Args:
            segment_id: Strava segment ID
            
        Returns:
            Segment details including polyline map data
        """
        segment_data = await self._request("GET", f"/segments/{segment_id}")
        
        # Decode polyline if present
        if "map" in segment_data and "polyline" in segment_data["map"]:
            try:
                segment_data["decoded_points"] = decode_polyline(
                    segment_data["map"]["polyline"]
                )
            except Exception:
                segment_data["decoded_points"] = [
                    segment_data.get("start_latlng", [0, 0]),
                    segment_data.get("end_latlng", [0, 0]),
                ]
        
        return segment_data
    
    async def get_segment_leaderboard(
        self,
        segment_id: int,
        per_page: int = 10,
        gender: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get the leaderboard for a segment.
        
        Args:
            segment_id: Strava segment ID
            per_page: Number of entries to return
            gender: Filter by gender ('M' or 'F')
            
        Returns:
            Leaderboard data including KOM/QOM
        """
        params = {"per_page": per_page, "page": 1}
        if gender:
            params["gender"] = gender
        
        leaderboard = await self._request(
            "GET", 
            f"/segments/{segment_id}/leaderboard",
            params=params,
        )
        
        # Format times in entries
        if "entries" in leaderboard:
            for entry in leaderboard["entries"]:
                if "elapsed_time" in entry:
                    entry["elapsed_time_formatted"] = format_seconds_to_time(
                        entry["elapsed_time"]
                    )
        
        return leaderboard
    
    async def get_segment_efforts(
        self,
        segment_id: int,
        athlete_id: Optional[int] = None,
        per_page: int = 30,
    ) -> List[Dict[str, Any]]:
        """
        Get efforts on a segment, optionally filtered by athlete.
        
        Args:
            segment_id: Strava segment ID
            athlete_id: Optional athlete ID to filter by
            per_page: Number of efforts to return
            
        Returns:
            List of segment efforts
        """
        params = {"per_page": per_page}
        if athlete_id:
            params["athlete_id"] = athlete_id
        
        # Note: This endpoint has specific requirements
        # For personal efforts, use /segment_efforts endpoint
        return await self._request(
            "GET",
            f"/segments/{segment_id}/all_efforts",
            params=params,
        )
    
    async def get_athlete_stats(self, athlete_id: int) -> Dict[str, Any]:
        """
        Get statistics for an athlete.
        
        Args:
            athlete_id: Strava athlete ID
            
        Returns:
            Athlete statistics including totals and records
        """
        return await self._request("GET", f"/athletes/{athlete_id}/stats")
    
    async def list_athlete_koms(
        self,
        athlete_id: int,
        page: int = 1,
        per_page: int = 30,
    ) -> List[Dict[str, Any]]:
        """
        Get KOMs/QOMs for an athlete.
        
        Args:
            athlete_id: Strava athlete ID
            page: Page number (1-indexed)
            per_page: Number of results per page
            
        Returns:
            List of segment efforts where athlete holds KOM/QOM
        """
        params = {"page": page, "per_page": per_page}
        
        koms = await self._request(
            "GET",
            f"/athletes/{athlete_id}/koms",
            params=params,
        )
        
        # Format times in results
        if isinstance(koms, list):
            for entry in koms:
                if "elapsed_time" in entry:
                    entry["elapsed_time_formatted"] = format_seconds_to_time(
                        entry["elapsed_time"]
                    )
        
        return koms
    
    async def list_starred_segments(
        self,
        page: int = 1,
        per_page: int = 30,
    ) -> List[Dict[str, Any]]:
        """
        Get the authenticated athlete's starred segments.
        
        Args:
            page: Page number (1-indexed)
            per_page: Number of results per page
            
        Returns:
            List of starred segments
        """
        params = {"page": page, "per_page": per_page}
        
        return await self._request(
            "GET",
            "/segments/starred",
            params=params,
        )
    
    async def list_athlete_activities(
        self,
        page: int = 1,
        per_page: int = 30,
        after: Optional[int] = None,
        before: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get the authenticated athlete's activities.
        
        Args:
            page: Page number (1-indexed)
            per_page: Number of results per page
            after: Epoch timestamp to filter activities after
            before: Epoch timestamp to filter activities before
            
        Returns:
            List of activities
        """
        params = {"page": page, "per_page": per_page}
        if after:
            params["after"] = after
        if before:
            params["before"] = before
        
        return await self._request(
            "GET",
            "/athlete/activities",
            params=params,
        )
    
    async def get_activity_segment_efforts(
        self,
        activity_id: int,
    ) -> List[Dict[str, Any]]:
        """
        Get segment efforts from a specific activity.
        
        Args:
            activity_id: Strava activity ID
            
        Returns:
            List of segment efforts from the activity
        """
        activity = await self._request("GET", f"/activities/{activity_id}")
        
        # Extract segment efforts from activity
        segment_efforts = activity.get("segment_efforts", [])
        
        # Format times in results
        for effort in segment_efforts:
            if "elapsed_time" in effort:
                effort["elapsed_time_formatted"] = format_seconds_to_time(
                    effort["elapsed_time"]
                )
        
        return segment_efforts
    
    async def get_athlete_segment_efforts(
        self,
        segment_id: int,
        start_date_local: Optional[str] = None,
        end_date_local: Optional[str] = None,
        per_page: int = 30,
    ) -> List[Dict[str, Any]]:
        """
        Get the authenticated athlete's efforts on a specific segment.
        
        Args:
            segment_id: Strava segment ID
            start_date_local: ISO 8601 formatted date string
            end_date_local: ISO 8601 formatted date string
            per_page: Number of results per page
            
        Returns:
            List of segment efforts by the authenticated athlete
        """
        params = {"segment_id": segment_id, "per_page": per_page}
        if start_date_local:
            params["start_date_local"] = start_date_local
        if end_date_local:
            params["end_date_local"] = end_date_local
        
        efforts = await self._request(
            "GET",
            "/segment_efforts",
            params=params,
        )
        
        # Format times in results
        if isinstance(efforts, list):
            for effort in efforts:
                if "elapsed_time" in effort:
                    effort["elapsed_time_formatted"] = format_seconds_to_time(
                        effort["elapsed_time"]
                    )
        
        return efforts
