def compute_difficulty(distance_m, elevation_gain, kom_speed_kmh):
    """
    Simple difficulty score for a segment.
    Lower is easier.
    """
    if distance_m == 0 or kom_speed_kmh == 0:
        return 9999  # avoid division by zero

    distance_km = distance_m / 1000
    slope = elevation_gain / distance_km if distance_km != 0 else 0
    score = (slope + 1) * (30 / kom_speed_kmh)  # adjustable formula
    return round(score, 2)
