import requests
from typing import List, Dict, Any, Union, Optional

# Compatibilité pydantic pour Python 3.13
try:
    from pydantic import AliasChoices
except ImportError:
    # Créer une implémentation de remplacement si nécessaire
    class AliasChoices:
        def __init__(self, *aliases):
            self.aliases = aliases

def explore_segments(access_token, lat, lon, radius_km=10, activity_type="riding", max_segments=50):
    """
    Explore Strava segments in a given area.
    
    Args:
        access_token: Strava API access token
        lat: Center latitude
        lon: Center longitude
        radius_km: Radius in kilometers to search (default 10km)
        activity_type: 'riding' or 'running'
        max_segments: Maximum number of segments to return (default 50)
        
    Returns:
        List of segment dictionaries from Strava API
    """
    
    # Convert radius to approximate latitude/longitude delta
    # 1 degree latitude ≈ 111km
    delta = radius_km / 111  
    
    # Calculate bounding box
    sw_lat, sw_lon = lat - delta, lon - delta
    ne_lat, ne_lon = lat + delta, lon + delta
    
    # Prepare API request
    bounds = f"{sw_lat},{sw_lon},{ne_lat},{ne_lon}"
    url = "https://www.strava.com/api/v3/segments/explore"
    headers = {"Authorization": f"Bearer {access_token}"}
    params = {
        "bounds": bounds,
        "activity_type": activity_type.lower(),
        "min_cat": 0,
        "max_cat": 5
    }
    
    # Note: Strava API doesn't actually honor per_page for segment explore
    # We'll limit the results after getting them

    # Execute request
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    
    # Get segments and limit to max_segments
    segments = response.json()["segments"]
    return segments[:max_segments] if len(segments) > max_segments else segments

def get_segment_details(access_token, segment_id):
    """
    Get detailed information about a specific segment, including KOM data and map points.
    
    Args:
        access_token: Strava API access token
        segment_id: ID of the segment to retrieve
        
    Returns:
        Segment details dictionary with additional KOM information and map data
    """
    headers = {"Authorization": f"Bearer {access_token}"}
    
    # Get basic segment details
    segment_url = f"https://www.strava.com/api/v3/segments/{segment_id}"
    segment_response = requests.get(segment_url, headers=headers)
    segment_response.raise_for_status()
    segment_data = segment_response.json()
    
    # Get leaderboard information (KOMs)
    leaderboard_url = f"https://www.strava.com/api/v3/segments/{segment_id}/leaderboard"
    leaderboard_params = {
        "per_page": 1,  # Just get the KOM
        "page": 1
    }
    leaderboard_response = requests.get(leaderboard_url, headers=headers, params=leaderboard_params)
    
    # Add KOM information if available
    if leaderboard_response.status_code == 200:
        leaderboard_data = leaderboard_response.json()
        if leaderboard_data.get("entries") and len(leaderboard_data["entries"]) > 0:
            kom_entry = leaderboard_data["entries"][0]
            segment_data["kom_data"] = {
                "athlete_name": kom_entry.get("athlete_name", "Unknown"),
                "elapsed_time": kom_entry.get("elapsed_time", 0),
                "elapsed_time_formatted": format_seconds_to_time(kom_entry.get("elapsed_time", 0)),
                "start_date": kom_entry.get("start_date", ""),
                "rank": kom_entry.get("rank", 1),
                "athlete_id": kom_entry.get("athlete_id", 0)
            }
        else:
            segment_data["kom_data"] = None
    else:
        segment_data["kom_data"] = None
    
    # Get detailed map data for the segment
    try:
        # Strava stores polyline data in the map field
        if "map" in segment_data and "polyline" in segment_data["map"]:
            # The polyline is already in the segment data
            segment_data["detailed_points"] = decode_polyline(segment_data["map"]["polyline"])
        else:
            # Fallback to just the start and end points
            segment_data["detailed_points"] = [
                segment_data["start_latlng"],
                segment_data["end_latlng"]
            ]
    except Exception:
        # Fallback to just the start and end points if there's an error
        segment_data["detailed_points"] = [
            segment_data["start_latlng"],
            segment_data["end_latlng"]
        ]
    
    return segment_data

def decode_polyline(polyline):
    """
    Decode a Google Maps encoded polyline to a list of coordinate points.
    
    Args:
        polyline: String in Google polyline format
        
    Returns:
        List of [lat, lng] coordinates
    """
    try:
        # If you're using Python 3.6+, this is a cleaner implementation
        import polyline
        return polyline.decode(polyline)
    except ImportError:
        # Fallback to manual implementation if polyline is not installed
        points = []
        index, lat, lng = 0, 0, 0
        
        while index < len(polyline):
            result = 1
            shift = 0
            while True:
                b = ord(polyline[index]) - 63 - 1
                index += 1
                result += b << shift
                shift += 5
                if b < 0x1f:
                    break
            lat += (~(result >> 1) if (result & 1) else (result >> 1))
            
            result = 1
            shift = 0
            while True:
                b = ord(polyline[index]) - 63 - 1
                index += 1
                result += b << shift
                shift += 5
                if b < 0x1f:
                    break
            lng += (~(result >> 1) if (result & 1) else (result >> 1))
            
            points.append([lat * 1e-5, lng * 1e-5])
        
        return points

def format_seconds_to_time(seconds):
    """Format seconds to mm:ss or hh:mm:ss format"""
    if seconds < 3600:  # Less than one hour
        minutes = seconds // 60
        remaining_seconds = seconds % 60
        return f"{minutes}:{remaining_seconds:02d}"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        remaining_seconds = seconds % 60
        return f"{hours}:{minutes:02d}:{remaining_seconds:02d}"