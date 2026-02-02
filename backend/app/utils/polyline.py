"""
Google Polyline encoding/decoding utilities.

Handles conversion between encoded polyline strings and
coordinate arrays for map display.
"""
from typing import List, Tuple

# Type aliases
Coordinate = Tuple[float, float]  # (latitude, longitude)
CoordinateList = List[Coordinate]


def decode_polyline(encoded: str) -> CoordinateList:
    """
    Decode a Google-encoded polyline string to coordinates.
    
    The polyline encoding is a lossy algorithm that encodes
    latitude/longitude coordinates as a string of ASCII characters.
    
    Args:
        encoded: Encoded polyline string
        
    Returns:
        List of (latitude, longitude) tuples
    """
    if not encoded:
        return []
    
    # Try using the polyline library first if available
    try:
        import polyline
        return polyline.decode(encoded)
    except ImportError:
        pass
    
    # Fallback to manual implementation
    points: CoordinateList = []
    index = 0
    lat = 0
    lng = 0
    
    while index < len(encoded):
        # Decode latitude
        result = 0
        shift = 0
        while True:
            b = ord(encoded[index]) - 63
            index += 1
            result |= (b & 0x1f) << shift
            shift += 5
            if b < 0x20:
                break
        
        if result & 1:
            lat += ~(result >> 1)
        else:
            lat += result >> 1
        
        # Decode longitude
        result = 0
        shift = 0
        while True:
            b = ord(encoded[index]) - 63
            index += 1
            result |= (b & 0x1f) << shift
            shift += 5
            if b < 0x20:
                break
        
        if result & 1:
            lng += ~(result >> 1)
        else:
            lng += result >> 1
        
        points.append((lat * 1e-5, lng * 1e-5))
    
    return points


def encode_polyline(coordinates: CoordinateList) -> str:
    """
    Encode a list of coordinates to a Google polyline string.
    
    Args:
        coordinates: List of (latitude, longitude) tuples
        
    Returns:
        Encoded polyline string
    """
    if not coordinates:
        return ""
    
    # Try using the polyline library first if available
    try:
        import polyline
        return polyline.encode(coordinates)
    except ImportError:
        pass
    
    # Fallback to manual implementation
    def encode_value(value: int) -> str:
        """Encode a single value."""
        value = ~(value << 1) if value < 0 else value << 1
        chunks = []
        while value >= 0x20:
            chunks.append(chr((value & 0x1f) | 0x20 + 63))
            value >>= 5
        chunks.append(chr(value + 63))
        return "".join(chunks)
    
    result = []
    prev_lat = 0
    prev_lng = 0
    
    for lat, lng in coordinates:
        lat_int = round(lat * 1e5)
        lng_int = round(lng * 1e5)
        
        result.append(encode_value(lat_int - prev_lat))
        result.append(encode_value(lng_int - prev_lng))
        
        prev_lat = lat_int
        prev_lng = lng_int
    
    return "".join(result)


def polyline_to_geojson(encoded: str) -> dict:
    """
    Convert an encoded polyline to GeoJSON LineString.
    
    Args:
        encoded: Encoded polyline string
        
    Returns:
        GeoJSON LineString feature
    """
    coordinates = decode_polyline(encoded)
    
    # GeoJSON uses [longitude, latitude] order
    geojson_coords = [[lng, lat] for lat, lng in coordinates]
    
    return {
        "type": "Feature",
        "geometry": {
            "type": "LineString",
            "coordinates": geojson_coords,
        },
        "properties": {},
    }
