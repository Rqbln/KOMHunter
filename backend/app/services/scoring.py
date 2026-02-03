"""
Segment difficulty scoring service.

Implements the unified difficulty formula based on research:
D_reel = w1 × S_phys + w2 × I_prestige + w3 × F_comp

Where:
- S_phys: Physical difficulty (Strava category score + altitude factor)
- I_prestige: Prestige index based on Position Score (effort/athlete count)
- F_comp: Competitiveness factor (KOM speed relative to expected)
"""
import math
from enum import Enum
from typing import Optional, Dict, Any


class DifficultyCategory(str, Enum):
    """Difficulty category labels."""
    EASY = "easy"
    MODERATE = "moderate"
    HARD = "hard"
    EXPERT = "expert"


class ScoringService:
    """
    Service for calculating segment difficulty scores using the unified formula.
    
    The formula combines three main factors:
    1. Physical difficulty (terrain, distance, elevation)
    2. Prestige/popularity (number of attempts, unique athletes)
    3. Competitiveness (how fast the current KOM is)
    """
    
    # Default weights for the unified formula
    WEIGHT_PHYSICAL = 0.40      # w1: Physical difficulty
    WEIGHT_PRESTIGE = 0.35      # w2: Prestige/popularity
    WEIGHT_COMPETITIVENESS = 0.25  # w3: Competitiveness
    
    # Category thresholds (normalized score 0-100)
    EASY_THRESHOLD = 25
    MODERATE_THRESHOLD = 50
    HARD_THRESHOLD = 75
    
    # Strava category score thresholds (length_m × grade_%)
    STRAVA_CAT_4_THRESHOLD = 8000
    STRAVA_CAT_3_THRESHOLD = 16000
    STRAVA_CAT_2_THRESHOLD = 32000
    STRAVA_CAT_1_THRESHOLD = 64000
    STRAVA_HC_THRESHOLD = 80000
    
    # Reference values for normalization
    REFERENCE_SPEED_KMH = 30  # Typical cycling speed
    MAX_EFFORT_COUNT = 50000  # For normalization
    MAX_ATHLETE_COUNT = 20000
    
    def compute_strava_category_score(
        self,
        distance_m: float,
        avg_grade: float,
    ) -> int:
        """
        Calculate the Strava category score (length × grade).
        
        This is the basic Strava formula for climb categorization.
        Only valid for grades > 3%.
        
        Args:
            distance_m: Segment distance in meters
            avg_grade: Average grade in percent
            
        Returns:
            Category score (distance_m × grade_percent)
        """
        if avg_grade < 3:
            return 0  # Not categorized (flat or too gentle)
        return int(distance_m * avg_grade)
    
    def get_strava_climb_category(self, category_score: int) -> int:
        """
        Get Strava climb category from category score.
        
        Args:
            category_score: Result of length × grade
            
        Returns:
            Category (0=NC, 1-4=Cat 4-1, 5=HC)
        """
        if category_score >= self.STRAVA_HC_THRESHOLD:
            return 5  # HC
        elif category_score >= self.STRAVA_CAT_1_THRESHOLD:
            return 1  # Cat 1
        elif category_score >= self.STRAVA_CAT_2_THRESHOLD:
            return 2  # Cat 2
        elif category_score >= self.STRAVA_CAT_3_THRESHOLD:
            return 3  # Cat 3
        elif category_score >= self.STRAVA_CAT_4_THRESHOLD:
            return 4  # Cat 4
        return 0  # Not categorized
    
    def compute_physical_score(
        self,
        distance_m: float,
        elevation_gain: float,
        avg_grade: float,
        max_grade: Optional[float] = None,
        elev_high: Optional[float] = None,
    ) -> float:
        """
        Calculate the physical difficulty score (S_phys).
        
        Factors:
        - Strava category score (length × grade)
        - Maximum grade penalty (steep sections are harder)
        - Altitude factor (higher = harder due to hypoxia)
        - Distance factor (longer = more sustained effort)
        
        Args:
            distance_m: Segment distance in meters
            elevation_gain: Total elevation gain in meters
            avg_grade: Average grade in percent
            max_grade: Maximum grade in percent (optional)
            elev_high: Highest elevation in meters (optional)
            
        Returns:
            Physical score (0-100 scale)
        """
        if distance_m <= 0:
            return 0
        
        # Base: Strava category score normalized
        category_score = self.compute_strava_category_score(distance_m, abs(avg_grade))
        
        # Normalize to 0-60 range (HC = 80000 -> 60)
        base_score = min(60, (category_score / self.STRAVA_HC_THRESHOLD) * 60)
        
        # If flat segment, use distance-based scoring
        if category_score == 0:
            # For flat/sprint segments, difficulty is based on distance and speed
            distance_km = distance_m / 1000
            base_score = min(30, distance_km * 5)  # Up to 30 points for 6km+
        
        # Max grade penalty (up to +15 points)
        max_grade_penalty = 0
        if max_grade and max_grade > 10:
            # Steep sections (>10%) add difficulty
            max_grade_penalty = min(15, (max_grade - 10) * 1.5)
        
        # Altitude factor (up to +15 points)
        altitude_factor = 0
        if elev_high and elev_high > 1500:
            # Above 1500m, hypoxia starts affecting performance
            altitude_factor = min(15, (elev_high - 1500) / 100)
        
        # Distance endurance factor (up to +10 points for very long segments)
        distance_km = distance_m / 1000
        endurance_factor = min(10, distance_km / 2) if distance_km > 5 else 0
        
        total = base_score + max_grade_penalty + altitude_factor + endurance_factor
        return min(100, round(total, 1))
    
    def compute_prestige_score(
        self,
        effort_count: Optional[int] = None,
        athlete_count: Optional[int] = None,
    ) -> float:
        """
        Calculate the prestige/popularity score (I_prestige).
        
        Based on the Position Score concept from VeloViewer:
        - More attempts = harder to get KOM (more competition)
        - More unique athletes = more diverse talent pool
        
        Args:
            effort_count: Total number of attempts on segment
            athlete_count: Number of unique athletes who attempted
            
        Returns:
            Prestige score (0-100 scale)
        """
        if not effort_count or effort_count <= 0:
            return 25  # Default for unknown
        
        # Effort-based difficulty (logarithmic scaling)
        # 100 efforts = ~30, 1000 = ~45, 10000 = ~60, 50000 = ~70
        effort_score = min(70, math.log10(effort_count + 1) * 15)
        
        # Athlete diversity factor (up to +30)
        athlete_factor = 0
        if athlete_count and athlete_count > 0:
            # More unique athletes = more competitive
            athlete_factor = min(30, math.log10(athlete_count + 1) * 8)
        
        # Effort/athlete ratio bonus
        # High ratio = people retry often = competitive segment
        ratio_bonus = 0
        if athlete_count and athlete_count > 0:
            ratio = effort_count / athlete_count
            if ratio > 3:  # People attempt more than 3x on average
                ratio_bonus = min(10, (ratio - 3) * 2)
        
        total = effort_score + athlete_factor + ratio_bonus
        return min(100, round(total, 1))
    
    def compute_competitiveness_score(
        self,
        distance_m: float,
        kom_time_seconds: Optional[int] = None,
        avg_grade: float = 0,
    ) -> float:
        """
        Calculate the competitiveness score (F_comp).
        
        Based on how fast the current KOM is relative to expected performance.
        A very fast KOM indicates strong competition.
        
        Args:
            distance_m: Segment distance in meters
            kom_time_seconds: KOM time in seconds (optional)
            avg_grade: Average grade for speed estimation
            
        Returns:
            Competitiveness score (0-100 scale)
        """
        if not kom_time_seconds or kom_time_seconds <= 0 or distance_m <= 0:
            return 40  # Default for unknown
        
        # Calculate KOM speed
        kom_speed_kmh = (distance_m / 1000) / (kom_time_seconds / 3600)
        
        # Estimate expected amateur speed based on grade
        # Flat: ~25 km/h, 5% grade: ~15 km/h, 10% grade: ~10 km/h
        if avg_grade > 0:
            expected_speed = max(8, 25 - (abs(avg_grade) * 1.5))
        else:
            # Downhill or flat
            expected_speed = 30 + abs(avg_grade) * 0.5
        
        # How much faster is KOM vs expected?
        speed_ratio = kom_speed_kmh / expected_speed
        
        # Convert to score
        # Ratio of 1.0 = 40 points (average)
        # Ratio of 1.5 = 70 points (50% faster than expected)
        # Ratio of 2.0 = 100 points (pro level)
        if speed_ratio <= 1.0:
            score = speed_ratio * 40
        else:
            score = 40 + (speed_ratio - 1.0) * 60
        
        return min(100, round(score, 1))
    
    def compute_unified_difficulty(
        self,
        distance_m: float,
        elevation_gain: float,
        avg_grade: float = 0,
        max_grade: Optional[float] = None,
        elev_high: Optional[float] = None,
        effort_count: Optional[int] = None,
        athlete_count: Optional[int] = None,
        kom_time_seconds: Optional[int] = None,
        weights: Optional[Dict[str, float]] = None,
    ) -> Dict[str, Any]:
        """
        Calculate the unified difficulty score using the research formula:
        D_reel = w1 × S_phys + w2 × I_prestige + w3 × F_comp
        
        Args:
            distance_m: Segment distance in meters
            elevation_gain: Total elevation gain in meters
            avg_grade: Average grade in percent
            max_grade: Maximum grade in percent (optional)
            elev_high: Highest elevation in meters (optional)
            effort_count: Total number of attempts (optional)
            athlete_count: Number of unique athletes (optional)
            kom_time_seconds: KOM time in seconds (optional)
            weights: Custom weights dict with 'physical', 'prestige', 'competitiveness'
            
        Returns:
            Dict with full breakdown of difficulty scores
        """
        # Use custom weights or defaults
        w1 = weights.get('physical', self.WEIGHT_PHYSICAL) if weights else self.WEIGHT_PHYSICAL
        w2 = weights.get('prestige', self.WEIGHT_PRESTIGE) if weights else self.WEIGHT_PRESTIGE
        w3 = weights.get('competitiveness', self.WEIGHT_COMPETITIVENESS) if weights else self.WEIGHT_COMPETITIVENESS
        
        # Calculate component scores
        s_phys = self.compute_physical_score(
            distance_m=distance_m,
            elevation_gain=elevation_gain,
            avg_grade=avg_grade,
            max_grade=max_grade,
            elev_high=elev_high,
        )
        
        i_prestige = self.compute_prestige_score(
            effort_count=effort_count,
            athlete_count=athlete_count,
        )
        
        f_comp = self.compute_competitiveness_score(
            distance_m=distance_m,
            kom_time_seconds=kom_time_seconds,
            avg_grade=avg_grade,
        )
        
        # Unified formula
        normalized_score = (w1 * s_phys) + (w2 * i_prestige) + (w3 * f_comp)
        normalized_score = min(100, round(normalized_score, 1))
        
        # Get category
        category = self.get_category(normalized_score)
        
        # Calculate Strava category score for reference
        strava_cat_score = self.compute_strava_category_score(distance_m, abs(avg_grade))
        
        return {
            "raw_score": normalized_score,  # Already normalized in unified formula
            "normalized_score": normalized_score,
            "category": category.value,
            "physical_score": s_phys,
            "prestige_score": i_prestige,
            "competitiveness_score": f_comp,
            "strava_category_points": strava_cat_score,
            "weights_used": {
                "physical": w1,
                "prestige": w2,
                "competitiveness": w3,
            }
        }
    
    # Legacy methods for backward compatibility
    def compute_difficulty(
        self,
        distance_m: float,
        elevation_gain: float,
        avg_grade: float = 0,
        effort_count: Optional[int] = None,
        kom_speed_kmh: Optional[float] = None,
    ) -> float:
        """
        Legacy method - calculates a simple difficulty score.
        Use compute_unified_difficulty() for the full formula.
        """
        # Convert kom_speed to time for unified formula
        kom_time_seconds = None
        if kom_speed_kmh and kom_speed_kmh > 0 and distance_m > 0:
            kom_time_seconds = int((distance_m / 1000) / kom_speed_kmh * 3600)
        
        result = self.compute_unified_difficulty(
            distance_m=distance_m,
            elevation_gain=elevation_gain,
            avg_grade=avg_grade,
            effort_count=effort_count,
            kom_time_seconds=kom_time_seconds,
        )
        return result["normalized_score"]
    
    def normalize_score(self, score: float, max_score: float = 100) -> float:
        """Normalize a difficulty score to 0-100 scale."""
        if score <= 0:
            return 0
        normalized = (math.log(score + 1) / math.log(max_score + 1)) * 100
        return min(100, max(0, round(normalized, 1)))
    
    def get_category(self, normalized_score: float) -> DifficultyCategory:
        """Get difficulty category from normalized score."""
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
        max_grade: Optional[float] = None,
        elev_high: Optional[float] = None,
        athlete_count: Optional[int] = None,
        kom_time_seconds: Optional[int] = None,
    ) -> dict:
        """
        Compute full scoring info including category and breakdown.
        
        Returns:
            Dict with normalized_score, category, and component breakdown
        """
        # If only kom_speed_kmh provided, convert to time
        if kom_time_seconds is None and kom_speed_kmh and kom_speed_kmh > 0 and distance_m > 0:
            kom_time_seconds = int((distance_m / 1000) / kom_speed_kmh * 3600)
        
        return self.compute_unified_difficulty(
            distance_m=distance_m,
            elevation_gain=elevation_gain,
            avg_grade=avg_grade,
            max_grade=max_grade,
            elev_high=elev_high,
            effort_count=effort_count,
            athlete_count=athlete_count,
            kom_time_seconds=kom_time_seconds,
        )
