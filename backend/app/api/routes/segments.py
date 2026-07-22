"""
Segment exploration and details endpoints.
"""
import logging
import re
from typing import List, Optional

import httpx
from fastapi import APIRouter, HTTPException, Query, Depends

from app.models.segment import (
    SegmentExploreRequest,
    SegmentExploreResponse,
    SegmentDetails,
    SegmentSummary,
    DifficultyBreakdown,
    KOMData,
)
from app.services.strava_api import StravaAPIService
from app.services.scoring import ScoringService
from app.api.dependencies import get_strava_api_service, get_scoring_service
from app.api.errors import map_strava_error

router = APIRouter()

logger = logging.getLogger(__name__)


def parse_time_to_seconds(time_str: Optional[str]) -> Optional[int]:
    """
    Parse a time string (mm:ss or hh:mm:ss) to seconds.
    
    Args:
        time_str: Time string like "14:22" or "1:14:22"
        
    Returns:
        Time in seconds, or None if parsing fails
    """
    if not time_str:
        return None
    
    try:
        # Handle formats like "14:22" or "1:14:22"
        parts = time_str.strip().split(":")
        if len(parts) == 2:
            # mm:ss format
            minutes, seconds = int(parts[0]), int(parts[1])
            return minutes * 60 + seconds
        elif len(parts) == 3:
            # hh:mm:ss format
            hours, minutes, seconds = int(parts[0]), int(parts[1]), int(parts[2])
            return hours * 3600 + minutes * 60 + seconds
        return None
    except (ValueError, IndexError):
        return None


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
            min_cat=request.min_cat,
            max_cat=request.max_cat,
        )

        # Normalize the requested sport to the model vocabulary (riding/running)
        sport = "running" if request.activity_type.value.startswith("run") else "riding"

        # Calculate difficulty scores (terrain-only, sport-aware)
        scored_segments = []
        for segment in segments:
            # Client-side grade/distance filters: drop out-of-range segments
            # before scoring. Omitted bounds (None) impose no constraint.
            avg_grade = segment.get("avg_grade", 0)
            distance_m = segment.get("distance", 0)
            if request.min_grade is not None and avg_grade < request.min_grade:
                continue
            if request.max_grade is not None and avg_grade > request.max_grade:
                continue
            if request.min_distance_m is not None and distance_m < request.min_distance_m:
                continue
            if request.max_distance_m is not None and distance_m > request.max_distance_m:
                continue

            difficulty = scoring_service.compute_difficulty(
                distance_m=segment.get("distance", 0),
                elevation_gain=segment.get("elev_difference", 0),
                avg_grade=segment.get("avg_grade", 0),
                activity_type=request.activity_type,
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
                    activity_type=sport,
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
        
    except HTTPException:
        raise
    except httpx.HTTPStatusError as e:
        raise map_strava_error(e) from e
    except Exception:
        logger.exception("Failed to explore segments")
        raise HTTPException(status_code=500, detail="Failed to explore segments")


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
    
    Returns segment details including:
    - Polyline for map display
    - KOM/QOM information from the xoms field
    - Full difficulty breakdown using the unified formula
    """
    try:
        # Get segment details from Strava
        segment_data = await strava_service.get_segment_details(segment_id)
        
        # Extract KOM/QOM data from xoms field
        xoms = segment_data.get("xoms", {})
        local_legend = segment_data.get("local_legend", {})
        
        # Parse KOM time to seconds for scoring
        kom_time_str = xoms.get("kom") if xoms else None
        qom_time_str = xoms.get("qom") if xoms else None
        kom_time_seconds = parse_time_to_seconds(kom_time_str)
        qom_time_seconds = parse_time_to_seconds(qom_time_str)
        
        # Build KOM data object
        kom_data = None
        if xoms or local_legend:
            kom_data = KOMData(
                kom_time=kom_time_str,
                qom_time=qom_time_str,
                overall_time=xoms.get("overall") if xoms else None,
                kom_time_seconds=kom_time_seconds,
                qom_time_seconds=qom_time_seconds,
                local_legend_name=local_legend.get("title") if local_legend else None,
                local_legend_efforts=local_legend.get("effort_description") if local_legend else None,
            )
        
        # Extract segment data for scoring
        distance_m = segment_data.get("distance", 0)
        elevation_gain = segment_data.get("total_elevation_gain", 0)
        avg_grade = segment_data.get("average_grade", 0)
        max_grade = segment_data.get("maximum_grade", 0)
        elev_high = segment_data.get("elevation_high", 0)
        effort_count = segment_data.get("effort_count", 0)
        athlete_count = segment_data.get("athlete_count", 0)
        # Strava returns activity_type "Ride" or "Run"
        activity_type = segment_data.get("activity_type", "Ride")
        # Normalize to the model vocabulary (riding/running) for the response
        sport = "running" if str(activity_type).lower().startswith("run") else "riding"

        # Calculate full breakdown: terrain difficulty + standalone context scores
        difficulty_result = scoring_service.compute_full_score(
            distance_m=distance_m,
            elevation_gain=elevation_gain,
            avg_grade=avg_grade,
            activity_type=activity_type,
            max_grade=max_grade,
            elev_high=elev_high,
            effort_count=effort_count,
            athlete_count=athlete_count,
            kom_time_seconds=kom_time_seconds,
        )
        
        # Create DifficultyBreakdown object
        difficulty_breakdown = DifficultyBreakdown(
            raw_score=difficulty_result["raw_score"],
            normalized_score=difficulty_result["normalized_score"],
            category=difficulty_result["category"],
            physical_score=difficulty_result["physical_score"],
            prestige_score=difficulty_result["prestige_score"],
            competitiveness_score=difficulty_result["competitiveness_score"],
            strava_category_points=difficulty_result["strava_category_points"],
            activity_type=difficulty_result.get("activity_type"),
            weights_used=difficulty_result.get("weights_used"),
        )
        
        return SegmentDetails(
            id=segment_data["id"],
            name=segment_data["name"],
            distance=distance_m,
            avg_grade=avg_grade,
            max_grade=max_grade,
            elev_high=elev_high,
            elev_low=segment_data.get("elevation_low", 0),
            total_elevation_gain=elevation_gain,
            start_latlng=segment_data.get("start_latlng", [0, 0]),
            end_latlng=segment_data.get("end_latlng", [0, 0]),
            climb_category=segment_data.get("climb_category", 0),
            city=segment_data.get("city", ""),
            state=segment_data.get("state", ""),
            country=segment_data.get("country", ""),
            effort_count=effort_count,
            athlete_count=athlete_count,
            star_count=segment_data.get("star_count", 0),
            polyline=segment_data.get("map", {}).get("polyline", ""),
            difficulty_score=difficulty_result["normalized_score"],
            difficulty_breakdown=difficulty_breakdown,
            kom=kom_data,
            activity_type=sport,
        )

    except HTTPException:
        raise
    except httpx.HTTPStatusError as e:
        raise map_strava_error(e) from e
    except Exception:
        logger.exception("Failed to get segment details")
        raise HTTPException(status_code=500, detail="Failed to get segment details")
