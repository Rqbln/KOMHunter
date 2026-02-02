"""
Athlete profile endpoints.
"""
from fastapi import APIRouter, HTTPException, Depends

from app.models.athlete import AthleteProfile
from app.services.strava_api import StravaAPIService
from app.api.dependencies import get_strava_api_service

router = APIRouter()


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
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get athlete profile: {str(e)}")
