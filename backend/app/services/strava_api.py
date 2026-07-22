"""
Strava API service for segment and athlete data.

Handles all interactions with the Strava REST API including
segment exploration, details, and leaderboards.
"""
from typing import Dict, Any, List, Optional

import httpx

from app.utils.polyline import decode_polyline
from app.utils.formatters import format_seconds_to_time


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
    ) -> List[Dict[str, Any]]:
        """
        Explore segments in a given area.
        
        Args:
            lat: Center latitude
            lon: Center longitude
            radius_km: Search radius in kilometers
            activity_type: 'riding' or 'running'
            max_segments: Maximum segments to return
            
        Returns:
            List of segment summaries
        """
        # Convert radius to approximate bounding box
        # 1 degree latitude ≈ 111km
        delta = radius_km / 111
        
        bounds = f"{lat - delta},{lon - delta},{lat + delta},{lon + delta}"
        
        params = {
            "bounds": bounds,
            "activity_type": activity_type.lower(),
            "min_cat": 0,
            "max_cat": 5,
        }
        
        response = await self._request("GET", "/segments/explore", params=params)
        segments = response.get("segments", [])
        
        # Limit results
        return segments[:max_segments] if len(segments) > max_segments else segments
    
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
