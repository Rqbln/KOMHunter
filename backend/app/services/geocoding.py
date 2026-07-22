"""
Geocoding service using Nominatim (OpenStreetMap).

Provides location to coordinates conversion with caching
to respect rate limits.
"""
from typing import Dict, Any, List, Optional

import httpx


class GeocodingService:
    """Service for geocoding locations using Nominatim."""
    
    NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
    
    # Default fallback coordinates (Paris, France)
    DEFAULT_LAT = 48.8566
    DEFAULT_LON = 2.3522
    DEFAULT_NAME = "Paris, France (default)"
    
    def __init__(self):
        self.headers = {
            "User-Agent": "KOMHunter/1.0 (https://github.com/komhunter)",
        }
        # Simple in-memory cache (values may be a single result dict or a
        # list of suggestion dicts, keyed by a mode-prefixed query string).
        self._cache: Dict[str, Any] = {}
    
    async def geocode(self, query: str) -> Optional[Dict[str, Any]]:
        """
        Geocode a location string to coordinates.
        
        Args:
            query: Location string (city, address, etc.)
            
        Returns:
            Dict with lat, lon, and display_name, or None if not found
        """
        # Check cache first
        cache_key = query.lower().strip()
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    self.NOMINATIM_URL,
                    params={
                        "q": query,
                        "format": "json",
                        "limit": 1,
                    },
                    headers=self.headers,
                    timeout=10.0,
                )
                response.raise_for_status()
                data = response.json()
                
                if data and len(data) > 0:
                    result = {
                        "latitude": float(data[0]["lat"]),
                        "longitude": float(data[0]["lon"]),
                        "display_name": data[0].get("display_name", query),
                        "type": data[0].get("type", "unknown"),
                    }
                    # Cache the result
                    self._cache[cache_key] = result
                    return result
                
                return None
                
        except Exception as e:
            print(f"Geocoding error for '{query}': {e}")
            return None

    async def geocode_suggestions(
        self, query: str, limit: int = 6
    ) -> List[Dict[str, Any]]:
        """
        Geocode a location string to a LIST of autocomplete suggestions.

        Requests Nominatim with ``limit`` results and maps every returned item
        to ``{latitude, longitude, display_name, type}`` (float lat/lon).

        Args:
            query: Partial or full location string (city, address, etc.)
            limit: Maximum number of suggestions to request (default 6)

        Returns:
            List of suggestion dicts. Empty/blank query, no match, or any
            network/parse error yields ``[]`` (never raises).
        """
        if not query or not query.strip():
            return []

        # Cache under a suggestions-specific key so it never collides with the
        # single-result geocode() cache for the same query.
        cache_key = f"suggest:{limit}:{query.lower().strip()}"
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    self.NOMINATIM_URL,
                    params={
                        "q": query,
                        "format": "json",
                        "limit": limit,
                    },
                    headers=self.headers,
                    timeout=10.0,
                )
                response.raise_for_status()
                data = response.json()

                results = [
                    {
                        "latitude": float(item["lat"]),
                        "longitude": float(item["lon"]),
                        "display_name": item.get("display_name", query),
                        "type": item.get("type", "unknown"),
                    }
                    for item in data
                ]

                # Cache successful lookups (including a valid empty result set).
                self._cache[cache_key] = results
                return results

        except Exception as e:
            print(f"Geocoding suggestions error for '{query}': {e}")
            return []

    async def geocode_with_fallback(self, query: str) -> Dict[str, Any]:
        """
        Geocode with fallback to default coordinates.
        
        Args:
            query: Location string
            
        Returns:
            Dict with coordinates, always returns valid data
        """
        result = await self.geocode(query)
        
        if result:
            return result
        
        return {
            "latitude": self.DEFAULT_LAT,
            "longitude": self.DEFAULT_LON,
            "display_name": self.DEFAULT_NAME,
            "type": "fallback",
        }
    
    async def reverse_geocode(
        self, 
        lat: float, 
        lon: float,
    ) -> Optional[Dict[str, Any]]:
        """
        Reverse geocode coordinates to location name.
        
        Args:
            lat: Latitude
            lon: Longitude
            
        Returns:
            Dict with display_name and address components
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://nominatim.openstreetmap.org/reverse",
                    params={
                        "lat": lat,
                        "lon": lon,
                        "format": "json",
                    },
                    headers=self.headers,
                    timeout=10.0,
                )
                response.raise_for_status()
                data = response.json()
                
                return {
                    "display_name": data.get("display_name", ""),
                    "address": data.get("address", {}),
                }
                
        except Exception as e:
            print(f"Reverse geocoding error: {e}")
            return None
