"""
Segment exploration and details endpoints.
"""
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query, Depends

from app.models.segment import (
    SegmentExploreRequest,
    SegmentExploreResponse,
    SegmentDetails,
    SegmentSummary,
)
from app.services.strava_api import StravaAPIService
from app.services.scoring import ScoringService
from app.api.dependencies import get_strava_api_service, get_scoring_service

router = APIRouter()


@router.post("/explore", response_model=SegmentExploreResponse)
async def explore_segments(
    request: SegmentExploreRequest,
    strava_service: StravaAPIService = Depends(get_strava_api_service),
    scoring_service: ScoringService = Depends(get_scoring_service),
) -> SegmentExploreResponse:
    """
    Explore Strava segments in a given area.
    
    Searches for segments within a radius of the specified location.
    Returns segment summaries with basic information and difficulty scores.
    """
    try:
        # Get segments from Strava API
        segments = await strava_service.explore_segments(
            lat=request.latitude,
            lon=request.longitude,
            radius_km=request.radius_km,
            activity_type=request.activity_type,
            max_segments=request.max_segments,
        )
        
        # Calculate difficulty scores
        scored_segments = []
        for segment in segments:
            difficulty = scoring_service.compute_difficulty(
                distance_m=segment.get("distance", 0),
                elevation_gain=segment.get("elev_difference", 0),
                avg_grade=segment.get("avg_grade", 0),
            )
            scored_segments.append(
                SegmentSummary(
                    id=segment["id"],
                    name=segment["name"],
                    distance=segment.get("distance", 0),
                    avg_grade=segment.get("avg_grade", 0),
                    elev_difference=segment.get("elev_difference", 0),
                    start_latlng=segment.get("start_latlng", [0, 0]),
                    end_latlng=segment.get("end_latlng", [0, 0]),
                    climb_category=segment.get("climb_category", 0),
                    difficulty_score=difficulty,
                )
            )
        
        # Sort by difficulty (easiest first)
        scored_segments.sort(key=lambda s: s.difficulty_score)
        
        return SegmentExploreResponse(
            segments=scored_segments,
            total_count=len(scored_segments),
            center_lat=request.latitude,
            center_lon=request.longitude,
            radius_km=request.radius_km,
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to explore segments: {str(e)}")


@router.get("/geocode")
async def geocode_location(
    query: str = Query(..., description="Location to geocode (city, address, etc.)"),
) -> dict:
    """
    Geocode a location string to coordinates.
    
    Uses Nominatim (OpenStreetMap) for geocoding.
    """
    from app.services.geocoding import GeocodingService
    
    geocoding = GeocodingService()
    result = await geocoding.geocode(query)
    
    if not result:
        raise HTTPException(status_code=404, detail="Location not found")
    
    return result


@router.get("/{segment_id}", response_model=SegmentDetails)
async def get_segment_details(
    segment_id: int,
    strava_service: StravaAPIService = Depends(get_strava_api_service),
    scoring_service: ScoringService = Depends(get_scoring_service),
) -> SegmentDetails:
    """
    Get detailed information about a specific segment.
    
    Returns segment details including the polyline for map display
    and KOM/QOM information from the xoms field.
    """
    try:
        # Get segment details from Strava
        segment_data = await strava_service.get_segment_details(segment_id)
        
        # Extract KOM/QOM data from xoms field
        kom_data = None
        xoms = segment_data.get("xoms", {})
        local_legend = segment_data.get("local_legend", {})
        
        if xoms or local_legend:
            kom_data = {
                "kom_time": xoms.get("kom"),
                "qom_time": xoms.get("qom"),
                "overall_time": xoms.get("overall"),
                "local_legend_name": local_legend.get("title") if local_legend else None,
                "local_legend_efforts": local_legend.get("effort_description") if local_legend else None,
            }
        
        # Calculate difficulty
        difficulty = scoring_service.compute_difficulty(
            distance_m=segment_data.get("distance", 0),
            elevation_gain=segment_data.get("total_elevation_gain", 0),
            avg_grade=segment_data.get("average_grade", 0),
        )
        
        return SegmentDetails(
            id=segment_data["id"],
            name=segment_data["name"],
            distance=segment_data.get("distance", 0),
            avg_grade=segment_data.get("average_grade", 0),
            max_grade=segment_data.get("maximum_grade", 0),
            elev_high=segment_data.get("elevation_high", 0),
            elev_low=segment_data.get("elevation_low", 0),
            total_elevation_gain=segment_data.get("total_elevation_gain", 0),
            start_latlng=segment_data.get("start_latlng", [0, 0]),
            end_latlng=segment_data.get("end_latlng", [0, 0]),
            climb_category=segment_data.get("climb_category", 0),
            city=segment_data.get("city", ""),
            state=segment_data.get("state", ""),
            country=segment_data.get("country", ""),
            effort_count=segment_data.get("effort_count", 0),
            athlete_count=segment_data.get("athlete_count", 0),
            star_count=segment_data.get("star_count", 0),
            polyline=segment_data.get("map", {}).get("polyline", ""),
            difficulty_score=difficulty,
            kom=kom_data,
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get segment details: {str(e)}")
