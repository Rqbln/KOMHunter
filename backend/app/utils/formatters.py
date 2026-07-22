"""
Formatting utilities for display values.

Provides consistent formatting for times, distances, speeds,
and other values used throughout the application.
"""
from typing import Optional


def format_seconds_to_time(seconds: int) -> str:
    """
    Format seconds to human-readable time string.
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        Formatted string (mm:ss or hh:mm:ss)
    """
    if seconds < 0:
        return "0:00"
    
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    
    if hours > 0:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    else:
        return f"{minutes}:{secs:02d}"


def format_time_to_seconds(time_str: str) -> int:
    """
    Parse a time string to seconds.
    
    Args:
        time_str: Time string (mm:ss or hh:mm:ss)
        
    Returns:
        Duration in seconds
    """
    parts = time_str.split(":")
    
    if len(parts) == 2:
        # mm:ss format
        minutes, seconds = int(parts[0]), int(parts[1])
        return minutes * 60 + seconds
    elif len(parts) == 3:
        # hh:mm:ss format
        hours, minutes, seconds = int(parts[0]), int(parts[1]), int(parts[2])
        return hours * 3600 + minutes * 60 + seconds
    else:
        raise ValueError(f"Invalid time format: {time_str}")


def parse_time_to_seconds(time_str: Optional[str]) -> Optional[int]:
    """
    Parse a time string (mm:ss or hh:mm:ss) to seconds, tolerantly.

    Unlike :func:`format_time_to_seconds` (which raises on bad input), this
    returns ``None`` for missing or unparseable values so callers enriching
    best-effort segment data never fail on a malformed KOM time.

    Args:
        time_str: Time string like "14:22" or "1:14:22"

    Returns:
        Time in seconds, or None if parsing fails
    """
    if not time_str:
        return None

    try:
        parts = time_str.strip().split(":")
        if len(parts) == 2:
            minutes, seconds = int(parts[0]), int(parts[1])
            return minutes * 60 + seconds
        elif len(parts) == 3:
            hours, minutes, seconds = int(parts[0]), int(parts[1]), int(parts[2])
            return hours * 3600 + minutes * 60 + seconds
        return None
    except (ValueError, IndexError):
        return None


def format_distance(meters: float, unit: str = "km") -> str:
    """
    Format distance in meters to readable string.
    
    Args:
        meters: Distance in meters
        unit: Target unit ('km', 'm', 'mi')
        
    Returns:
        Formatted distance string with unit
    """
    if unit == "km":
        if meters >= 1000:
            return f"{meters / 1000:.2f} km"
        else:
            return f"{meters:.0f} m"
    elif unit == "m":
        return f"{meters:.0f} m"
    elif unit == "mi":
        miles = meters / 1609.344
        return f"{miles:.2f} mi"
    else:
        return f"{meters:.0f} m"


def format_elevation(meters: float, unit: str = "m") -> str:
    """
    Format elevation in meters to readable string.
    
    Args:
        meters: Elevation in meters
        unit: Target unit ('m', 'ft')
        
    Returns:
        Formatted elevation string with unit
    """
    if unit == "ft":
        feet = meters * 3.28084
        return f"{feet:.0f} ft"
    else:
        return f"{meters:.0f} m"


def format_grade(grade: float) -> str:
    """
    Format grade/slope as percentage.
    
    Args:
        grade: Grade in percent
        
    Returns:
        Formatted grade string
    """
    return f"{grade:.1f}%"


def format_speed(speed_ms: float, unit: str = "km/h") -> str:
    """
    Format speed from m/s to readable string.
    
    Args:
        speed_ms: Speed in meters per second
        unit: Target unit ('km/h', 'mph', 'min/km')
        
    Returns:
        Formatted speed string with unit
    """
    if unit == "km/h":
        kmh = speed_ms * 3.6
        return f"{kmh:.1f} km/h"
    elif unit == "mph":
        mph = speed_ms * 2.23694
        return f"{mph:.1f} mph"
    elif unit == "min/km":
        if speed_ms <= 0:
            return "--:--/km"
        pace_sec = 1000 / speed_ms
        minutes = int(pace_sec // 60)
        seconds = int(pace_sec % 60)
        return f"{minutes}:{seconds:02d}/km"
    else:
        return f"{speed_ms:.1f} m/s"


def format_number(value: int, locale: str = "en") -> str:
    """
    Format a number with thousands separator.
    
    Args:
        value: Number to format
        locale: Locale for formatting ('en' or 'fr')
        
    Returns:
        Formatted number string
    """
    if locale == "fr":
        # French uses space as thousands separator
        return f"{value:,}".replace(",", " ")
    else:
        # English uses comma
        return f"{value:,}"
