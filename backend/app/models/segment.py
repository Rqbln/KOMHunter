"""
Pydantic models for Strava segments.
"""
from typing import List, Optional, Dict, Any
from enum import Enum

from pydantic import BaseModel, Field


class ActivityType(str, Enum):
    """Supported activity types for segment exploration."""
    RIDE = "riding"
    RUN = "running"


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
            }
        }


class KOMData(BaseModel):
    """KOM/QOM holder information."""
    
    kom_time: Optional[str] = Field(None, description="KOM time formatted (mm:ss)")
    qom_time: Optional[str] = Field(None, description="QOM time formatted (mm:ss)")
    overall_time: Optional[str] = Field(None, description="Overall best time formatted (mm:ss)")
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
    kom: Optional[Dict[str, Any]] = Field(None, description="KOM/QOM data")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": 12345678,
                "name": "Flagstaff Super Climb",
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
                "difficulty_score": 42.5,
                "kom": {
                    "athlete_name": "Sepp Kuss",
                    "elapsed_time": 862,
                    "elapsed_time_formatted": "14:22",
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
    
    class Config:
        json_schema_extra = {
            "example": {
                "latitude": 40.015,
                "longitude": -105.270,
                "radius_km": 25,
                "activity_type": "riding",
                "max_segments": 50,
            }
        }


class SegmentExploreResponse(BaseModel):
    """Response from segment exploration."""
    
    segments: List[SegmentSummary] = Field(..., description="List of discovered segments")
    total_count: int = Field(..., description="Total number of segments found")
    center_lat: float = Field(..., description="Search center latitude")
    center_lon: float = Field(..., description="Search center longitude")
    radius_km: float = Field(..., description="Search radius used")
