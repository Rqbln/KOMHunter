"""
Segment difficulty scoring service.

The headline **difficulty** score (0-100) measures *terrain only* and is
sport-aware (climbing-oriented for riding, grade-adjusted effort for running).
It deliberately does NOT fold in popularity or KOM speed — those are exposed
separately as ``prestige`` and ``competitiveness`` so a short but popular urban
ramp is no longer mislabelled "hard".

Grounded in ``docs/Évaluation Difficulté KOM_QOM Strava.md``:
- Riding: Strava climb categorization (length_m × grade_%) + max-grade and
  altitude penalties.
- Running: grade-adjusted effort (GAP-inspired) + vertical gain + distance.
- Prestige: Position-Score-style popularity (efforts / unique athletes).
- Competitiveness: KOM speed relative to a sport- and grade-adjusted norm.
"""
import math
from enum import Enum
from typing import Optional, Dict, Any, Union


class DifficultyCategory(str, Enum):
    """Difficulty category labels."""
    EASY = "easy"
    MODERATE = "moderate"
    HARD = "hard"
    EXPERT = "expert"


def _is_running(activity_type: Union[str, Enum, None]) -> bool:
    """True when the activity is running (vs riding). Accepts str or enum."""
    if activity_type is None:
        return False
    value = getattr(activity_type, "value", activity_type)
    return str(value).lower().startswith("run")


# KOM/QOM speed ceilings above which an effort is physically implausible and
# almost certainly a GPS glitch (e.g. a 490 m run with a 20 s "KOM" ~= 88 km/h).
# Running suspicious above 24 km/h (pace faster than 2:30/km). Riding above
# 90 km/h — high enough to leave legitimate fast alpine descents (which routinely
# average 60-80 km/h) untouched, while still catching GPS-glitch KOMs (120+ km/h).
# Kept module-level so both scoring and the API can flag such segments.
_SUSPICIOUS_RUN_KMH = 24.0
_SUSPICIOUS_RIDE_KMH = 90.0


def is_kom_suspicious(
    distance_m: Optional[float],
    kom_time_seconds: Optional[int],
    activity_type: Union[str, Enum, None] = "riding",
) -> bool:
    """
    Return True when the KOM/QOM speed is physically implausible (likely a GPS
    error) and the segment should be flagged and sorted last.

    Running is suspicious above 24 km/h (pace faster than 2:30/km); riding above
    70 km/h. Missing distance or KOM time returns False (nothing to judge).
    Reuses the KOM-speed computation shape from ``compute_competitiveness_score``.
    """
    if not kom_time_seconds or kom_time_seconds <= 0 or not distance_m or distance_m <= 0:
        return False

    kom_speed_kmh = (distance_m / 1000.0) / (kom_time_seconds / 3600.0)
    threshold = _SUSPICIOUS_RUN_KMH if _is_running(activity_type) else _SUSPICIOUS_RIDE_KMH
    return kom_speed_kmh > threshold


class ScoringService:
    """
    Compute a terrain-based, sport-aware difficulty score (0-100) plus two
    independent context scores (prestige, competitiveness).
    """

    # Category thresholds (difficulty score 0-100)
    EASY_THRESHOLD = 25
    MODERATE_THRESHOLD = 50
    HARD_THRESHOLD = 75

    # Strava climb-category score thresholds (length_m × grade_%)
    STRAVA_CAT_4_THRESHOLD = 8000
    STRAVA_CAT_3_THRESHOLD = 16000
    STRAVA_CAT_2_THRESHOLD = 32000
    STRAVA_CAT_1_THRESHOLD = 64000
    STRAVA_HC_THRESHOLD = 80000

    # ------------------------------------------------------------------ #
    # Strava climb category helpers
    # ------------------------------------------------------------------ #
    def compute_strava_category_score(self, distance_m: float, avg_grade: float) -> int:
        """
        Strava climb-category score = length_m × grade_%.

        Only meaningful for grades > 3% (flatter climbs are "not categorized").
        """
        if avg_grade < 3:
            return 0
        return int(distance_m * avg_grade)

    def get_strava_climb_category(self, category_score: int) -> int:
        """Map a category score to a Strava climb category (0=NC, 1-4, 5=HC)."""
        if category_score >= self.STRAVA_HC_THRESHOLD:
            return 5
        elif category_score >= self.STRAVA_CAT_1_THRESHOLD:
            return 1
        elif category_score >= self.STRAVA_CAT_2_THRESHOLD:
            return 2
        elif category_score >= self.STRAVA_CAT_3_THRESHOLD:
            return 3
        elif category_score >= self.STRAVA_CAT_4_THRESHOLD:
            return 4
        return 0

    # ------------------------------------------------------------------ #
    # Terrain difficulty (the headline score) — sport-aware
    # ------------------------------------------------------------------ #
    def compute_terrain_difficulty(
        self,
        activity_type: Union[str, Enum, None] = "riding",
        distance_m: float = 0,
        avg_grade: float = 0,
        elevation_gain: Optional[float] = None,
        max_grade: Optional[float] = None,
        elev_high: Optional[float] = None,
    ) -> float:
        """
        Terrain-only difficulty, 0-100. Higher = physically harder ground.

        A non-positive distance denotes an invalid segment and returns 0.0.
        """
        # Strava may send an explicit JSON null for a grade/distance field.
        distance_m = distance_m or 0
        avg_grade = avg_grade or 0.0

        if distance_m <= 0:
            return 0.0

        if _is_running(activity_type):
            return self._running_difficulty(
                distance_m, avg_grade, elevation_gain, max_grade
            )
        return self._riding_difficulty(
            distance_m, avg_grade, max_grade, elev_high
        )

    def _riding_difficulty(
        self,
        distance_m: float,
        avg_grade: float,
        max_grade: Optional[float],
        elev_high: Optional[float],
    ) -> float:
        """Climb-centric difficulty for cycling segments."""
        # Strava-style climb points, mapped to a well-distributed 0-90 curve.
        # HC (80000) -> ~90; Cat1 (64000) -> ~78; Cat2 (32000) -> ~52.
        cat_points = distance_m * max(avg_grade, 0.0)
        climb = min(100.0, (cat_points / self.STRAVA_HC_THRESHOLD) ** 0.6 * 90) if cat_points > 0 else 0.0

        # Steep ramps beyond 10% add punch.
        max_grade_pen = min(12.0, max(0.0, (max_grade or 0.0) - 10.0) * 1.2)
        # Thin air above 1500 m.
        altitude_pen = min(8.0, max(0.0, (elev_high or 0.0) - 1500.0) / 150.0)
        # Small endurance term so long, near-flat segments are not a flat zero.
        flat_endur = min(5.0, (distance_m / 1000.0) / 8.0)

        total = climb + max_grade_pen + altitude_pen + flat_endur
        return min(100.0, round(total, 1))

    def _running_difficulty(
        self,
        distance_m: float,
        avg_grade: float,
        elevation_gain: Optional[float],
        max_grade: Optional[float],
    ) -> float:
        """Grade-adjusted-effort difficulty for running segments."""
        # Vertical gain dominates running difficulty; fall back to length×grade.
        gain = elevation_gain
        if gain is None or gain <= 0:
            gain = distance_m * max(avg_grade, 0.0) / 100.0
        elev = min(55.0, gain / 12.0)  # ~660 m of D+ -> 55

        up = min(22.0, max(0.0, avg_grade) * 2.5)
        # Steep descents (< -10%) are hard on the legs when running.
        down = min(10.0, max(0.0, (-avg_grade) - 10.0) * 1.5)
        dist = min(18.0, (distance_m / 1000.0) * 1.8)  # 10 km -> 18
        mgp = min(8.0, max(0.0, (max_grade or 0.0) - 15.0) * 0.8)

        total = elev + up + down + dist + mgp
        return min(100.0, round(total, 1))

    # ------------------------------------------------------------------ #
    # Context scores (kept separate from difficulty on purpose)
    # ------------------------------------------------------------------ #
    def compute_prestige_score(
        self,
        effort_count: Optional[int] = None,
        athlete_count: Optional[int] = None,
    ) -> float:
        """
        Popularity/prestige, 0-100 (Position-Score inspired). Independent of
        terrain difficulty — a busy segment is prestigious, not necessarily hard.
        """
        if not effort_count or effort_count <= 0:
            return 25.0  # Unknown popularity

        effort_score = min(70.0, math.log10(effort_count + 1) * 16.0)

        athlete_factor = 0.0
        if athlete_count and athlete_count > 0:
            athlete_factor = min(30.0, math.log10(athlete_count + 1) * 8.0)

        return min(100.0, round(effort_score + athlete_factor, 1))

    def compute_competitiveness_score(
        self,
        distance_m: float,
        kom_time_seconds: Optional[int] = None,
        avg_grade: float = 0,
        activity_type: Union[str, Enum, None] = "riding",
    ) -> float:
        """
        How fast the KOM/QOM is versus a sport- and grade-adjusted norm, 0-100.
        Independent of terrain difficulty.
        """
        if not kom_time_seconds or kom_time_seconds <= 0 or distance_m <= 0:
            return 40.0  # Unknown

        kom_speed_kmh = (distance_m / 1000.0) / (kom_time_seconds / 3600.0)
        running = _is_running(activity_type)

        if running:
            # Running norms are much slower than cycling.
            if avg_grade > 0:
                expected_speed = max(6.0, 14.0 - abs(avg_grade) * 0.8)
            else:
                expected_speed = 14.0 + abs(avg_grade) * 0.3
        else:
            if avg_grade > 0:
                expected_speed = max(8.0, 25.0 - abs(avg_grade) * 1.5)
            else:
                expected_speed = 30.0 + abs(avg_grade) * 0.5

        speed_ratio = kom_speed_kmh / expected_speed
        if speed_ratio <= 1.0:
            score = speed_ratio * 40.0
        else:
            score = 40.0 + (speed_ratio - 1.0) * 60.0
        return min(100.0, round(score, 1))

    def is_kom_suspicious(
        self,
        distance_m: Optional[float],
        kom_time_seconds: Optional[int],
        activity_type: Union[str, Enum, None] = "riding",
    ) -> bool:
        """
        Instance wrapper around the module-level :func:`is_kom_suspicious` so
        callers holding a ``ScoringService`` can flag GPS-glitched KOMs directly.
        """
        return is_kom_suspicious(distance_m, kom_time_seconds, activity_type)

    # ------------------------------------------------------------------ #
    # Category + aggregate helpers
    # ------------------------------------------------------------------ #
    def get_category(self, difficulty_score: float) -> DifficultyCategory:
        """Map a 0-100 difficulty score to a category."""
        if difficulty_score < self.EASY_THRESHOLD:
            return DifficultyCategory.EASY
        elif difficulty_score < self.MODERATE_THRESHOLD:
            return DifficultyCategory.MODERATE
        elif difficulty_score < self.HARD_THRESHOLD:
            return DifficultyCategory.HARD
        return DifficultyCategory.EXPERT

    def normalize_score(self, score: float, max_score: float = 100) -> float:
        """Log-normalize an arbitrary score into 0-100 (utility helper)."""
        if score <= 0:
            return 0
        normalized = (math.log(score + 1) / math.log(max_score + 1)) * 100
        return min(100, max(0, round(normalized, 1)))

    def compute_difficulty(
        self,
        distance_m: float,
        elevation_gain: float = 0,
        avg_grade: float = 0,
        activity_type: Union[str, Enum, None] = "riding",
        max_grade: Optional[float] = None,
        elev_high: Optional[float] = None,
    ) -> float:
        """
        Terrain difficulty (0-100) for the given segment. Used by /explore.

        A non-positive distance denotes an invalid segment and returns 0.0.
        """
        return self.compute_terrain_difficulty(
            activity_type=activity_type,
            distance_m=distance_m,
            avg_grade=avg_grade,
            elevation_gain=elevation_gain,
            max_grade=max_grade,
            elev_high=elev_high,
        )

    def compute_full_score(
        self,
        distance_m: float,
        elevation_gain: float = 0,
        avg_grade: float = 0,
        activity_type: Union[str, Enum, None] = "riding",
        max_grade: Optional[float] = None,
        elev_high: Optional[float] = None,
        effort_count: Optional[int] = None,
        athlete_count: Optional[int] = None,
        kom_time_seconds: Optional[int] = None,
        kom_speed_kmh: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Full breakdown: terrain difficulty (headline) plus the independent
        prestige and competitiveness context scores.

        ``normalized_score``/``physical_score`` are the terrain difficulty;
        ``prestige_score`` and ``competitiveness_score`` are standalone and are
        NOT summed into the difficulty.
        """
        avg_grade = avg_grade or 0.0
        distance_m = distance_m or 0

        if kom_time_seconds is None and kom_speed_kmh and kom_speed_kmh > 0 and distance_m > 0:
            kom_time_seconds = int((distance_m / 1000) / kom_speed_kmh * 3600)

        difficulty = self.compute_terrain_difficulty(
            activity_type=activity_type,
            distance_m=distance_m,
            avg_grade=avg_grade,
            elevation_gain=elevation_gain,
            max_grade=max_grade,
            elev_high=elev_high,
        )
        prestige = self.compute_prestige_score(
            effort_count=effort_count,
            athlete_count=athlete_count,
        )
        competitiveness = self.compute_competitiveness_score(
            distance_m=distance_m,
            kom_time_seconds=kom_time_seconds,
            avg_grade=avg_grade,
            activity_type=activity_type,
        )
        category = self.get_category(difficulty)
        cat_points = self.compute_strava_category_score(distance_m, abs(avg_grade))

        return {
            "raw_score": difficulty,
            "normalized_score": difficulty,
            "category": category.value,
            "physical_score": difficulty,
            "prestige_score": prestige,
            "competitiveness_score": competitiveness,
            "strava_category_points": cat_points,
            "activity_type": "running" if _is_running(activity_type) else "riding",
            "weights_used": None,  # No longer a weighted blend
        }
