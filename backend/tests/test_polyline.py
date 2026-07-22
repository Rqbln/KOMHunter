"""
Tests for polyline encoding/decoding utilities.
"""
import pytest
from app.utils.polyline import (
    decode_polyline,
    encode_polyline,
    polyline_to_geojson,
)


class TestPolylineDecoding:
    """Tests for polyline decoding."""
    
    def test_decode_simple_polyline(self):
        """Test decoding a simple polyline."""
        # This is a simple encoded polyline for testing
        encoded = "_p~iF~ps|U_ulLnnqC_mqNvxq`@"
        points = decode_polyline(encoded)
        
        assert len(points) > 0
        assert all(len(p) == 2 for p in points)
    
    def test_decode_empty_polyline(self):
        """Test decoding an empty string."""
        points = decode_polyline("")
        assert points == []
    
    def test_decode_returns_coordinates(self):
        """Test that decoded points are valid coordinates."""
        encoded = "_p~iF~ps|U_ulLnnqC"
        points = decode_polyline(encoded)
        
        for lat, lng in points:
            assert -90 <= lat <= 90
            assert -180 <= lng <= 180


class TestPolylineEncoding:
    """Tests for polyline encoding."""
    
    def test_encode_empty_list(self):
        """Test encoding an empty list."""
        encoded = encode_polyline([])
        assert encoded == ""
    
    def test_encode_single_point(self):
        """Test encoding a single point."""
        points = [(38.5, -120.2)]
        encoded = encode_polyline(points)
        assert len(encoded) > 0
    
    def test_encode_decode_roundtrip(self):
        """Test that encode/decode is reversible."""
        original = [(38.5, -120.2), (40.7, -120.95), (43.252, -126.453)]
        
        encoded = encode_polyline(original)
        decoded = decode_polyline(encoded)
        
        assert len(decoded) == len(original)
        
        # Allow for small floating point differences
        for orig, dec in zip(original, decoded):
            assert abs(orig[0] - dec[0]) < 0.0001
            assert abs(orig[1] - dec[1]) < 0.0001


class TestPolylineToGeoJSON:
    """Tests for GeoJSON conversion."""
    
    def test_geojson_structure(self):
        """Test that GeoJSON has correct structure."""
        encoded = "_p~iF~ps|U_ulLnnqC"
        geojson = polyline_to_geojson(encoded)
        
        assert geojson["type"] == "Feature"
        assert geojson["geometry"]["type"] == "LineString"
        assert "coordinates" in geojson["geometry"]
        assert "properties" in geojson
    
    def test_geojson_coordinate_order(self):
        """Test that GeoJSON uses [lng, lat] order."""
        # Create a simple polyline and verify coordinate order
        encoded = "_p~iF~ps|U"  # Single point at approximately (38.5, -120.2)
        geojson = polyline_to_geojson(encoded)
        
        coords = geojson["geometry"]["coordinates"]
        assert len(coords) > 0
        
        # GeoJSON uses [longitude, latitude]
        # Original point is around (38.5, -120.2)
        # So GeoJSON should be around [-120.2, 38.5]
        lng, lat = coords[0]
        assert -180 <= lng <= 180
        assert -90 <= lat <= 90
    
    def test_geojson_empty_polyline(self):
        """Test GeoJSON with empty polyline."""
        geojson = polyline_to_geojson("")
        
        assert geojson["geometry"]["coordinates"] == []
