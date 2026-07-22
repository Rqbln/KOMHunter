"""
Pydantic models for Strava segments.
"""
from typing import List, Optional, Dict, Any, Literal
from enum import Enum

from pydantic import BaseModel, Field


class ActivityType(str, Enum):
    """Supported activity types for segment exploration."""
    RIDE = "riding"
    RUN = "running"


class DifficultyBreakdown(BaseModel):
    """
    Segment difficulty breakdown.

    The headline ``normalized_score`` (== ``physical_score``) is terrain-only,
    sport-aware difficulty (0-100). ``prestige_score`` (popularity) and
    ``competitiveness_score`` (KOM speed) are INDEPENDENT context metrics — they
    are shown alongside difficulty, not summed into it.
    """

    raw_score: float = Field(..., description="Terrain difficulty score (0-100)")
    normalized_score: float = Field(..., description="Terrain difficulty score (0-100)")
    category: str = Field(..., description="Difficulty category (easy/moderate/hard/expert)")
    physical_score: float = Field(..., description="Terrain difficulty (same as normalized_score)")
    prestige_score: float = Field(..., description="Independent popularity/prestige score (0-100)")
    competitiveness_score: float = Field(..., description="Independent KOM-speed competitiveness (0-100)")
    strava_category_points: int = Field(0, description="Strava category score (length × grade)")
    activity_type: Optional[str] = Field(None, description="Sport used for scoring (riding/running)")
    weights_used: Optional[Dict[str, float]] = Field(
        None,
        description="Deprecated: difficulty is no longer a weighted blend (always null)",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "raw_score": 52.3,
                "normalized_score": 52.3,
                "category": "hard",
                "physical_score": 52.3,
                "prestige_score": 58.2,
                "competitiveness_score": 55.0,
                "strava_category_points": 42120,
                "activity_type": "riding",
                "weights_used": None,
            }
        }


class SegmentSummary(BaseModel):
    """Summary information about a segment from exploration."""
    
    id: int = Field(..., description="Unique segment identifier")
    name: str = Field(..., description="Segment name")
    distance: float = Field(..., description="Distance in meters")
    avg_grade: float = Field(..., description="Average grade in percent")
    elev_difference: float = Field(0, description="Elevation difference in meters")
    start_latlng: List[float] = Field(..., description="Start coordinates [lat, lng]")
    end_latlng: List[float] = Field(..., description="End coordinates [lat, lng]")
    climb_category: int = Field(0, description="Climb category (0-5)")
    difficulty_score: float = Field(0, description="Calculated difficulty score")
    activity_type: Optional[str] = Field(
        None, description="Sport for this segment (riding/running)"
    )

    # --- Optional enrichment (populated only for popularity/competitiveness/
    # opportunity sorts, which fetch per-segment detail; null otherwise) ---
    prestige_score: Optional[float] = Field(
        None, description="Popularity/prestige score 0-100 (higher = more famous)"
    )
    competitiveness_score: Optional[float] = Field(
        None,
        description="KOM-speed competitiveness 0-100 (lower = slower KOM = easier to win)",
    )
    effort_count: Optional[int] = Field(
        None, description="Total number of efforts (from segment detail)"
    )
    athlete_count: Optional[int] = Field(
        None, description="Number of unique athletes (from segment detail)"
    )
    kom_time: Optional[str] = Field(
        None, description="KOM time formatted mm:ss (from segment detail)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "id": 12345678,
                "name": "Flagstaff Super Climb",
                "distance": 5200,
                "avg_grade": 8.1,
                "elev_difference": 340,
                "start_latlng": [40.0150, -105.2705],
                "end_latlng": [40.0089, -105.2890],
                "climb_category": 3,
                "difficulty_score": 42.5,
                "activity_type": "riding",
                "prestige_score": 58.2,
                "competitiveness_score": 55.0,
                "effort_count": 15234,
                "athlete_count": 4521,
                "kom_time": "14:22",
            }
        }


class KOMData(BaseModel):
    """KOM/QOM holder information."""
    
    kom_time: Optional[str] = Field(None, description="KOM time formatted (mm:ss)")
    qom_time: Optional[str] = Field(None, description="QOM time formatted (mm:ss)")
    overall_time: Optional[str] = Field(None, description="Overall best time formatted (mm:ss)")
    kom_time_seconds: Optional[int] = Field(None, description="KOM time in seconds")
    qom_time_seconds: Optional[int] = Field(None, description="QOM time in seconds")
    local_legend_name: Optional[str] = Field(None, description="Local legend athlete name")
    local_legend_efforts: Optional[str] = Field(None, description="Local legend effort count")


class SegmentDetails(BaseModel):
    """Detailed information about a specific segment."""
    
    id: int = Field(..., description="Unique segment identifier")
    name: str = Field(..., description="Segment name")
    distance: float = Field(..., description="Distance in meters")
    avg_grade: float = Field(..., description="Average grade in percent")
    max_grade: float = Field(0, description="Maximum grade in percent")
    elev_high: float = Field(0, description="Highest elevation in meters")
    elev_low: float = Field(0, description="Lowest elevation in meters")
    total_elevation_gain: float = Field(0, description="Total elevation gain in meters")
    start_latlng: List[float] = Field(..., description="Start coordinates [lat, lng]")
    end_latlng: List[float] = Field(..., description="End coordinates [lat, lng]")
    climb_category: int = Field(0, description="Climb category (0-5)")
    city: str = Field("", description="City name")
    state: str = Field("", description="State/region name")
    country: str = Field("", description="Country name")
    effort_count: int = Field(0, description="Total number of efforts")
    athlete_count: int = Field(0, description="Number of unique athletes")
    star_count: int = Field(0, description="Number of stars/favorites")
    polyline: str = Field("", description="Encoded polyline for map display")
    difficulty_score: float = Field(0, description="Calculated difficulty score")
    difficulty_breakdown: Optional[DifficultyBreakdown] = Field(
        None, 
        description="Detailed difficulty breakdown"
    )
    kom: Optional[KOMData] = Field(None, description="KOM/QOM data")
    activity_type: Optional[str] = Field(
        None, description="Sport for this segment (riding/running)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "id": 12345678,
                "name": "Flagstaff Super Climb",
                "activity_type": "riding",
                "distance": 5200,
                "avg_grade": 8.1,
                "max_grade": 15.2,
                "elev_high": 2100,
                "elev_low": 1760,
                "total_elevation_gain": 340,
                "start_latlng": [40.0150, -105.2705],
                "end_latlng": [40.0089, -105.2890],
                "climb_category": 3,
                "city": "Boulder",
                "state": "Colorado",
                "country": "United States",
                "effort_count": 15234,
                "athlete_count": 4521,
                "star_count": 892,
                "polyline": "encoded_polyline_string",
                "difficulty_score": 52.3,
                "difficulty_breakdown": {
                    "raw_score": 52.3,
                    "normalized_score": 52.3,
                    "category": "hard",
                    "physical_score": 52.3,
                    "prestige_score": 58.2,
                    "competitiveness_score": 55.0,
                    "strava_category_points": 42120,
                    "activity_type": "riding",
                    "weights_used": None,
                },
                "kom": {
                    "kom_time": "14:22",
                    "qom_time": "16:45",
                    "overall_time": "14:22",
                    "kom_time_seconds": 862,
                    "local_legend_name": "Local Hero",
                    "local_legend_efforts": "52 efforts",
                },
            }
        }


class SegmentExploreRequest(BaseModel):
    """Request body for segment exploration."""
    
    latitude: float = Field(..., ge=-90, le=90, description="Center latitude")
    longitude: float = Field(..., ge=-180, le=180, description="Center longitude")
    radius_km: float = Field(10, ge=1, le=100, description="Search radius in km")
    activity_type: ActivityType = Field(
        ActivityType.RIDE, 
        description="Type of activity (riding or running)"
    )
    max_segments: int = Field(50, ge=1, le=200, description="Maximum segments to return")

    # Result ordering. "difficulty" (default) preserves current behavior.
    # popularity/competitiveness/opportunity trigger per-segment enrichment.
    # Any other value is rejected with 422 (Literal validation).
    sort_by: Literal[
        "difficulty",
        "distance",
        "grade",
        "popularity",
        "competitiveness",
        "opportunity",
    ] = Field(
        "difficulty",
        description=(
            "Sort order: difficulty (easiest terrain first), distance (shortest "
            "first), grade (steepest first), popularity (most famous first), "
            "competitiveness (slowest KOM = easiest to win first), opportunity "
            "(famous AND winnable first)."
        ),
    )

    # --- Advanced filters (all optional; omitting keeps current behavior) ---
    min_cat: int = Field(0, ge=0, le=5, description="Minimum Strava climb category")
    max_cat: int = Field(5, ge=0, le=5, description="Maximum Strava climb category")
    min_grade: Optional[float] = Field(
        None, description="Minimum average grade in percent (client-side filter)"
    )
    max_grade: Optional[float] = Field(
        None, description="Maximum average grade in percent (client-side filter)"
    )
    min_distance_m: Optional[float] = Field(
        None, description="Minimum distance in meters (client-side filter)"
    )
    max_distance_m: Optional[float] = Field(
        None, description="Maximum distance in meters (client-side filter)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "latitude": 40.015,
                "longitude": -105.270,
                "radius_km": 25,
                "activity_type": "riding",
                "max_segments": 50,
                "sort_by": "opportunity",
                "min_cat": 0,
                "max_cat": 5,
                "min_grade": 3.0,
                "max_grade": 12.0,
                "min_distance_m": 1000,
                "max_distance_m": 20000,
            }
        }


class SegmentExploreResponse(BaseModel):
    """Response from segment exploration."""
    
    segments: List[SegmentSummary] = Field(..., description="List of discovered segments")
    total_count: int = Field(..., description="Total number of segments found")
    center_lat: float = Field(..., description="Search center latitude")
    center_lon: float = Field(..., description="Search center longitude")
    radius_km: float = Field(..., description="Search radius used")
