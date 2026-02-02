"""
Segment difficulty scoring service.

Calculates difficulty scores for segments based on distance,
elevation, and grade to help identify attainable KOMs.
"""
from enum import Enum
from typing import Optional


class DifficultyCategory(str, Enum):
    """Difficulty category labels."""
    EASY = "easy"
    MODERATE = "moderate"
    HARD = "hard"
    EXPERT = "expert"


class ScoringService:
    """Service for calculating segment difficulty scores."""
    
    # Reference speed for scoring (adjustable)
    REFERENCE_SPEED_KMH = 30
    
    # Category thresholds (normalized score 0-100)
    EASY_THRESHOLD = 25
    MODERATE_THRESHOLD = 50
    HARD_THRESHOLD = 75
    
    def compute_difficulty(
        self,
        distance_m: float,
        elevation_gain: float,
        avg_grade: float = 0,
        effort_count: Optional[int] = None,
        kom_speed_kmh: Optional[float] = None,
    ) -> float:
        """
        Calculate a difficulty score for a segment.
        
        The score combines multiple factors:
        - Slope/grade (higher = harder)
        - Distance (longer = harder for climbing)
        - Effort count (fewer efforts = potentially easier KOM)
        - KOM speed (faster = harder to beat)
        
        Args:
            distance_m: Segment distance in meters
            elevation_gain: Total elevation gain in meters
            avg_grade: Average grade in percent
            effort_count: Number of recorded efforts (optional)
            kom_speed_kmh: Current KOM speed in km/h (optional)
            
        Returns:
            Difficulty score (lower = easier to get KOM)
        """
        if distance_m == 0:
            return 9999  # Invalid segment
        
        distance_km = distance_m / 1000
        
        # Calculate slope if not provided
        if avg_grade == 0 and elevation_gain > 0:
            slope = (elevation_gain / distance_m) * 100  # Convert to percent
        else:
            slope = abs(avg_grade)
        
        # Base difficulty from slope and speed
        if kom_speed_kmh and kom_speed_kmh > 0:
            speed_factor = self.REFERENCE_SPEED_KMH / kom_speed_kmh
        else:
            # Estimate speed factor from grade
            # Steeper grades = slower speeds = higher factor
            speed_factor = 1 + (slope / 10)
        
        # Base score
        base_score = (slope + 1) * speed_factor
        
        # Distance factor (longer segments are generally harder)
        distance_factor = 1 + (distance_km / 10)
        
        # Apply distance factor
        score = base_score * distance_factor
        
        # Effort count factor (fewer efforts = potentially easier)
        if effort_count is not None and effort_count > 0:
            # Segments with fewer efforts might be easier to KOM
            if effort_count < 100:
                score *= 0.9  # 10% easier
            elif effort_count > 10000:
                score *= 1.1  # 10% harder (more competition)
        
        return round(score, 2)
    
    def normalize_score(self, score: float, max_score: float = 100) -> float:
        """
        Normalize a difficulty score to 0-100 scale.
        
        Args:
            score: Raw difficulty score
            max_score: Maximum expected score for normalization
            
        Returns:
            Normalized score between 0 and 100
        """
        if score <= 0:
            return 0
        
        # Use logarithmic scaling for better distribution
        import math
        normalized = (math.log(score + 1) / math.log(max_score + 1)) * 100
        return min(100, max(0, round(normalized, 1)))
    
    def get_category(self, normalized_score: float) -> DifficultyCategory:
        """
        Get difficulty category from normalized score.
        
        Args:
            normalized_score: Score between 0-100
            
        Returns:
            DifficultyCategory enum value
        """
        if normalized_score < self.EASY_THRESHOLD:
            return DifficultyCategory.EASY
        elif normalized_score < self.MODERATE_THRESHOLD:
            return DifficultyCategory.MODERATE
        elif normalized_score < self.HARD_THRESHOLD:
            return DifficultyCategory.HARD
        else:
            return DifficultyCategory.EXPERT
    
    def compute_full_score(
        self,
        distance_m: float,
        elevation_gain: float,
        avg_grade: float = 0,
        effort_count: Optional[int] = None,
        kom_speed_kmh: Optional[float] = None,
    ) -> dict:
        """
        Compute full scoring info including category.
        
        Returns:
            Dict with raw_score, normalized_score, and category
        """
        raw = self.compute_difficulty(
            distance_m=distance_m,
            elevation_gain=elevation_gain,
            avg_grade=avg_grade,
            effort_count=effort_count,
            kom_speed_kmh=kom_speed_kmh,
        )
        normalized = self.normalize_score(raw)
        category = self.get_category(normalized)
        
        return {
            "raw_score": raw,
            "normalized_score": normalized,
            "category": category.value,
        }
