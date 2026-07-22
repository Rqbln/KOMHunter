"""
Pydantic models for Strava athletes.
"""
from typing import Optional, List

from pydantic import BaseModel, Field


class AthleteProfile(BaseModel):
    """Athlete profile information from Strava."""
    
    id: int = Field(..., description="Unique athlete identifier")
    firstname: str = Field("", description="First name")
    lastname: str = Field("", description="Last name")
    profile: str = Field("", description="URL to profile picture (large)")
    profile_medium: str = Field("", description="URL to profile picture (medium)")
    city: str = Field("", description="City")
    state: str = Field("", description="State/region")
    country: str = Field("", description="Country")
    sex: str = Field("", description="M or F")
    premium: bool = Field(False, description="Strava premium subscriber")
    created_at: str = Field("", description="Account creation date")
    updated_at: str = Field("", description="Last profile update")
    
    @property
    def full_name(self) -> str:
        """Get full name."""
        return f"{self.firstname} {self.lastname}".strip()
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": 12345,
                "firstname": "Alex",
                "lastname": "Runner",
                "profile": "https://example.com/profile.jpg",
                "profile_medium": "https://example.com/profile_medium.jpg",
                "city": "Boulder",
                "state": "Colorado",
                "country": "United States",
                "sex": "M",
                "premium": True,
                "created_at": "2020-01-15T10:30:00Z",
                "updated_at": "2024-01-20T15:45:00Z",
            }
        }


class ActivityTotals(BaseModel):
    """Activity totals summary."""
    
    count: int = Field(0, description="Number of activities")
    distance: float = Field(0, description="Total distance in meters")
    moving_time: int = Field(0, description="Total moving time in seconds")
    elapsed_time: int = Field(0, description="Total elapsed time in seconds")
    elevation_gain: float = Field(0, description="Total elevation gain in meters")
    achievement_count: Optional[int] = Field(None, description="Number of achievements")


class AthleteStats(BaseModel):
    """Athlete statistics summary."""
    
    biggest_ride_distance: Optional[float] = Field(None, description="Longest ride in meters")
    biggest_climb_elevation_gain: Optional[float] = Field(None, description="Biggest climb in meters")
    recent_ride_totals: Optional[ActivityTotals] = Field(None, description="Recent ride stats (4 weeks)")
    recent_run_totals: Optional[ActivityTotals] = Field(None, description="Recent run stats (4 weeks)")
    ytd_ride_totals: Optional[ActivityTotals] = Field(None, description="Year-to-date ride stats")
    ytd_run_totals: Optional[ActivityTotals] = Field(None, description="Year-to-date run stats")
    all_ride_totals: Optional[ActivityTotals] = Field(None, description="All-time ride stats")
    all_run_totals: Optional[ActivityTotals] = Field(None, description="All-time run stats")
    
    class Config:
        json_schema_extra = {
            "example": {
                "biggest_ride_distance": 150000,
                "biggest_climb_elevation_gain": 2500,
                "recent_ride_totals": {
                    "count": 12,
                    "distance": 450000,
                    "moving_time": 54000,
                    "elapsed_time": 60000,
                    "elevation_gain": 5200
                }
            }
        }


class AthleteKOM(BaseModel):
    """KOM/QOM record held by an athlete."""
    
    segment_id: int = Field(..., description="Segment ID")
    segment_name: str = Field(..., description="Segment name")
    activity_id: int = Field(..., description="Activity ID where KOM was achieved")
    elapsed_time: int = Field(..., description="Effort time in seconds")
    elapsed_time_formatted: str = Field("", description="Effort time formatted (mm:ss)")
    distance: float = Field(0, description="Segment distance in meters")
    avg_grade: float = Field(0, description="Segment average grade")
    start_date: str = Field("", description="Date of the effort")
    start_date_local: str = Field("", description="Local date of the effort")
    kom_rank: Optional[int] = Field(None, description="Rank on segment (1 = KOM)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "segment_id": 12345678,
                "segment_name": "Flagstaff Super Climb",
                "activity_id": 98765432,
                "elapsed_time": 862,
                "elapsed_time_formatted": "14:22",
                "distance": 5200,
                "avg_grade": 8.1,
                "start_date": "2024-06-15T10:30:00Z",
                "start_date_local": "2024-06-15T12:30:00",
                "kom_rank": 1
            }
        }


class SegmentEffort(BaseModel):
    """Athlete's effort on a segment."""
    
    id: int = Field(..., description="Effort ID")
    segment_id: int = Field(..., description="Segment ID")
    segment_name: str = Field(..., description="Segment name")
    activity_id: int = Field(..., description="Activity ID")
    elapsed_time: int = Field(..., description="Effort time in seconds")
    elapsed_time_formatted: str = Field("", description="Effort time formatted")
    moving_time: int = Field(0, description="Moving time in seconds")
    start_date: str = Field("", description="Date of the effort")
    start_date_local: str = Field("", description="Local date of the effort")
    distance: float = Field(0, description="Effort distance in meters")
    pr_rank: Optional[int] = Field(None, description="PR rank (1 = personal best)")
    kom_rank: Optional[int] = Field(None, description="KOM rank on leaderboard")
    achievements: Optional[List[dict]] = Field(None, description="Achievements earned")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": 1234567890,
                "segment_id": 12345678,
                "segment_name": "Flagstaff Super Climb",
                "activity_id": 98765432,
                "elapsed_time": 875,
                "elapsed_time_formatted": "14:35",
                "moving_time": 870,
                "start_date": "2024-06-15T10:30:00Z",
                "start_date_local": "2024-06-15T12:30:00",
                "distance": 5200,
                "pr_rank": 1,
                "kom_rank": 3
            }
        }


class StarredSegment(BaseModel):
    """A starred/favorite segment."""
    
    id: int = Field(..., description="Segment ID")
    name: str = Field(..., description="Segment name")
    distance: float = Field(0, description="Distance in meters")
    avg_grade: float = Field(0, description="Average grade in percent")
    elev_difference: float = Field(0, description="Elevation difference in meters")
    climb_category: int = Field(0, description="Climb category (0-5)")
    city: str = Field("", description="City")
    state: str = Field("", description="State/region")
    country: str = Field("", description="Country")
    activity_type: str = Field("Ride", description="Activity type")
    starred_date: str = Field("", description="Date starred")
    athlete_pr_effort: Optional[dict] = Field(None, description="Athlete's PR on this segment")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": 12345678,
                "name": "Flagstaff Super Climb",
                "distance": 5200,
                "avg_grade": 8.1,
                "elev_difference": 340,
                "climb_category": 3,
                "city": "Boulder",
                "state": "Colorado",
                "country": "United States",
                "activity_type": "Ride",
                "starred_date": "2024-01-15T10:00:00Z"
            }
        }


class KOMsResponse(BaseModel):
    """Response for athlete KOMs list."""
    
    koms: List[AthleteKOM] = Field(..., description="List of KOMs")
    total_count: int = Field(..., description="Total number of KOMs")
    page: int = Field(1, description="Current page")
    per_page: int = Field(30, description="Items per page")


class StarredSegmentsResponse(BaseModel):
    """Response for starred segments list."""
    
    segments: List[StarredSegment] = Field(..., description="List of starred segments")
    total_count: int = Field(..., description="Total count")
    page: int = Field(1, description="Current page")
    per_page: int = Field(30, description="Items per page")


class PRsResponse(BaseModel):
    """Response for athlete PRs list."""

    prs: List[SegmentEffort] = Field(..., description="List of PR efforts")
    total_count: int = Field(..., description="Total count")
    page: int = Field(1, description="Current page")
    per_page: int = Field(30, description="Items per page")


class HeatmapResponse(BaseModel):
    """
    Aggregated training-heatmap points built from activity summary polylines.

    Intentionally JSON-light: ``points`` is a flat list of ``[lat, lng]`` pairs
    sampled across the athlete's activities, ready to feed a Leaflet heat layer.
    """

    points: List[List[float]] = Field(
        default_factory=list,
        description="Aggregated [latitude, longitude] points across activities",
    )
    activity_count: int = Field(
        0, description="Number of activities that contributed points to the heatmap"
    )
    sport: Optional[str] = Field(
        None, description="Sport filter applied ('ride', 'run', or None for all)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "points": [
                    [38.5, -120.2],
                    [40.7, -120.95],
                ],
                "activity_count": 2,
                "sport": "ride",
            }
        }
