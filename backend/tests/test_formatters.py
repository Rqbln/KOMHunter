"""
Tests for formatting utilities.
"""
import pytest
from app.utils.formatters import (
    format_seconds_to_time,
    format_time_to_seconds,
    parse_time_to_seconds,
    format_distance,
    format_elevation,
    format_grade,
    format_speed,
    format_number,
)


class TestParseTimeToSeconds:
    """Tolerant Strava xoms time parser (must handle the bare-seconds "25s" form)."""

    def test_bare_seconds_with_s_suffix(self):
        # Strava's sub-minute KOM format — the case that broke the gap comparison.
        assert parse_time_to_seconds("25s") == 25
        assert parse_time_to_seconds("45s") == 45
        assert parse_time_to_seconds("9s") == 9

    def test_bare_number(self):
        assert parse_time_to_seconds("90") == 90

    def test_mm_ss(self):
        assert parse_time_to_seconds("1:31") == 91
        assert parse_time_to_seconds("14:22") == 862

    def test_hh_mm_ss(self):
        assert parse_time_to_seconds("1:05:22") == 3922

    def test_missing_or_invalid(self):
        assert parse_time_to_seconds(None) is None
        assert parse_time_to_seconds("") is None
        assert parse_time_to_seconds("invalid") is None


class TestTimeFormatting:
    """Tests for time formatting functions."""
    
    def test_format_seconds_minutes_only(self):
        """Test formatting seconds less than an hour."""
        assert format_seconds_to_time(125) == "2:05"
        assert format_seconds_to_time(60) == "1:00"
        assert format_seconds_to_time(59) == "0:59"
    
    def test_format_seconds_with_hours(self):
        """Test formatting with hours."""
        assert format_seconds_to_time(3661) == "1:01:01"
        assert format_seconds_to_time(3600) == "1:00:00"
        assert format_seconds_to_time(7325) == "2:02:05"
    
    def test_format_seconds_zero(self):
        """Test formatting zero seconds."""
        assert format_seconds_to_time(0) == "0:00"
    
    def test_format_seconds_negative(self):
        """Test formatting negative seconds."""
        assert format_seconds_to_time(-5) == "0:00"
    
    def test_parse_time_minutes_seconds(self):
        """Test parsing mm:ss format."""
        assert format_time_to_seconds("2:05") == 125
        assert format_time_to_seconds("1:00") == 60
    
    def test_parse_time_hours_minutes_seconds(self):
        """Test parsing hh:mm:ss format."""
        assert format_time_to_seconds("1:01:01") == 3661
        assert format_time_to_seconds("2:02:05") == 7325
    
    def test_parse_invalid_time(self):
        """Test parsing invalid time format."""
        with pytest.raises(ValueError):
            format_time_to_seconds("invalid")


class TestDistanceFormatting:
    """Tests for distance formatting functions."""
    
    def test_format_distance_km(self):
        """Test formatting to kilometers."""
        assert format_distance(5200) == "5.20 km"
        assert format_distance(500) == "500 m"
    
    def test_format_distance_meters(self):
        """Test formatting to meters."""
        assert format_distance(5200, unit="m") == "5200 m"
    
    def test_format_distance_miles(self):
        """Test formatting to miles."""
        result = format_distance(1609.344, unit="mi")
        assert "1.00 mi" in result


class TestElevationFormatting:
    """Tests for elevation formatting functions."""
    
    def test_format_elevation_meters(self):
        """Test formatting to meters."""
        assert format_elevation(340) == "340 m"
    
    def test_format_elevation_feet(self):
        """Test formatting to feet."""
        result = format_elevation(100, unit="ft")
        assert "328 ft" in result


class TestGradeFormatting:
    """Tests for grade formatting functions."""
    
    def test_format_grade(self):
        """Test grade formatting."""
        assert format_grade(8.1) == "8.1%"
        assert format_grade(0) == "0.0%"
        assert format_grade(-5.5) == "-5.5%"


class TestSpeedFormatting:
    """Tests for speed formatting functions."""
    
    def test_format_speed_kmh(self):
        """Test formatting to km/h."""
        assert format_speed(10, unit="km/h") == "36.0 km/h"
    
    def test_format_speed_mph(self):
        """Test formatting to mph."""
        result = format_speed(10, unit="mph")
        assert "22.4 mph" in result
    
    def test_format_speed_pace(self):
        """Test formatting to pace (min/km)."""
        result = format_speed(3.33, unit="min/km")
        assert "/km" in result
    
    def test_format_speed_zero_pace(self):
        """Test pace formatting with zero speed."""
        assert format_speed(0, unit="min/km") == "--:--/km"


class TestNumberFormatting:
    """Tests for number formatting functions."""
    
    def test_format_number_english(self):
        """Test English number formatting."""
        assert format_number(1000) == "1,000"
        assert format_number(1000000) == "1,000,000"
    
    def test_format_number_french(self):
        """Test French number formatting."""
        assert format_number(1000, locale="fr") == "1 000"
        assert format_number(1000000, locale="fr") == "1 000 000"
