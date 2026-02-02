"""
Pydantic models for Strava athletes.
"""
from typing import Optional

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


class AthleteStats(BaseModel):
    """Athlete statistics summary."""
    
    biggest_ride_distance: Optional[float] = Field(None, description="Longest ride in meters")
    biggest_climb_elevation_gain: Optional[float] = Field(None, description="Biggest climb in meters")
    recent_ride_totals: Optional[dict] = Field(None, description="Recent ride stats")
    recent_run_totals: Optional[dict] = Field(None, description="Recent run stats")
    all_ride_totals: Optional[dict] = Field(None, description="All-time ride stats")
    all_run_totals: Optional[dict] = Field(None, description="All-time run stats")
