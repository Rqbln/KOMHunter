"""
Athlete profile and statistics endpoints.
"""
from typing import List, Optional
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
)
from app.services.strava_api import StravaAPIService
from app.services.scoring import ScoringService
from app.api.dependencies import get_strava_api_service, get_scoring_service
from app.utils.formatters import format_seconds_to_time

router = APIRouter()


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
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get athlete profile: {str(e)}")


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
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get athlete stats: {str(e)}")


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
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get KOMs: {str(e)}")


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
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get starred segments: {str(e)}")


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
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get PRs: {str(e)}")
