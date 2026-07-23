"""
Tests for the terrain-first, sport-aware segment scoring service.
"""
import pytest
from app.services.scoring import ScoringService, DifficultyCategory, is_kom_suspicious


class TestKomSuspicious:
    """A physically implausible KOM speed (GPS error) must be flagged."""

    def test_bogus_short_run_kom_is_suspicious(self):
        # 490 m in 20 s = ~88 km/h running -> impossible.
        assert is_kom_suspicious(490, 20, "running") is True
        assert is_kom_suspicious(490, 20, "Run") is True

    def test_normal_run_kom_not_suspicious(self):
        # 3 km in 12 min = 15 km/h -> fine.
        assert is_kom_suspicious(3000, 720, "running") is False

    def test_fast_but_legit_flat_ride_not_suspicious(self):
        # 1 km flat sprint in 60 s = 60 km/h ride -> below the 90 km/h ceiling.
        assert is_kom_suspicious(1000, 60, "riding") is False

    def test_legit_alpine_descent_not_suspicious(self):
        # 5 km descent in 240 s = 75 km/h ride -> legit fast descent, not flagged.
        assert is_kom_suspicious(5000, 240, "riding") is False

    def test_bogus_ride_kom_is_suspicious(self):
        # 1 km in 30 s = 120 km/h ride -> impossible.
        assert is_kom_suspicious(1000, 30, "riding") is True

    def test_missing_data_not_suspicious(self):
        assert is_kom_suspicious(None, 20, "running") is False
        assert is_kom_suspicious(490, None, "running") is False
        assert is_kom_suspicious(490, 0, "running") is False

    def test_instance_wrapper(self, scoring_service: ScoringService):
        assert scoring_service.is_kom_suspicious(490, 20, "running") is True


class TestTerrainDifficulty:
    """The headline difficulty score measures terrain only."""

    def test_basic_positive(self, scoring_service: ScoringService):
        score = scoring_service.compute_difficulty(
            distance_m=5000, elevation_gain=200, avg_grade=4.0
        )
        assert score > 0
        assert isinstance(score, float)

    def test_flat_easier_than_steep(self, scoring_service: ScoringService):
        flat = scoring_service.compute_difficulty(
            distance_m=5000, elevation_gain=0, avg_grade=0
        )
        steep = scoring_service.compute_difficulty(
            distance_m=5000, elevation_gain=400, avg_grade=8.0
        )
        assert flat < steep

    def test_zero_distance_is_invalid(self, scoring_service: ScoringService):
        score = scoring_service.compute_difficulty(
            distance_m=0, elevation_gain=100, avg_grade=5.0
        )
        assert score == 0.0

    def test_short_popular_ramp_is_not_hard(self, scoring_service: ScoringService):
        """
        The old formula labelled the Côte de la Butte Montmartre (824 m, 6.1%)
        'hard' purely because it is popular. Terrain-only difficulty must class
        this uncategorized ramp as easy/moderate, regardless of popularity.
        """
        result = scoring_service.compute_full_score(
            distance_m=824,
            elevation_gain=50,
            avg_grade=6.1,
            activity_type="riding",
            max_grade=8.5,
            effort_count=7636,      # very popular
            athlete_count=3473,
            kom_time_seconds=91,    # fast KOM
        )
        assert result["normalized_score"] < 40
        assert result["category"] in ("easy", "moderate")

    def test_hors_categorie_climb_is_expert(self, scoring_service: ScoringService):
        """A long HC climb (e.g. Alpe d'Huez ~13.8 km @ 8.1%) must be expert."""
        score = scoring_service.compute_difficulty(
            distance_m=13800, elevation_gain=1120, avg_grade=8.1,
            activity_type="riding", max_grade=13.0,
        )
        assert score >= 75
        assert scoring_service.get_category(score) == DifficultyCategory.EXPERT

    def test_riding_vs_running_differ(self, scoring_service: ScoringService):
        """Same profile scores differently per sport."""
        ride = scoring_service.compute_difficulty(
            distance_m=3000, elevation_gain=150, avg_grade=5.0, activity_type="riding"
        )
        run = scoring_service.compute_difficulty(
            distance_m=3000, elevation_gain=150, avg_grade=5.0, activity_type="running"
        )
        assert ride != run

    def test_max_grade_increases_difficulty(self, scoring_service: ScoringService):
        base = scoring_service.compute_difficulty(
            distance_m=4000, elevation_gain=280, avg_grade=7.0, activity_type="riding"
        )
        with_ramp = scoring_service.compute_difficulty(
            distance_m=4000, elevation_gain=280, avg_grade=7.0,
            activity_type="riding", max_grade=18.0,
        )
        assert with_ramp > base

    def test_altitude_increases_difficulty(self, scoring_service: ScoringService):
        low = scoring_service.compute_difficulty(
            distance_m=6000, elevation_gain=420, avg_grade=7.0, activity_type="riding"
        )
        high = scoring_service.compute_difficulty(
            distance_m=6000, elevation_gain=420, avg_grade=7.0,
            activity_type="riding", elev_high=2400,
        )
        assert high > low

    def test_bounds(self, scoring_service: ScoringService):
        for grade in (-5, 0, 3, 8, 15):
            score = scoring_service.compute_difficulty(
                distance_m=10000, elevation_gain=500, avg_grade=grade,
            )
            assert 0 <= score <= 100


class TestPrestigeAndCompetitiveness:
    """Context scores are computed independently of terrain difficulty."""

    def test_prestige_rises_with_popularity(self, scoring_service: ScoringService):
        low = scoring_service.compute_prestige_score(effort_count=50, athlete_count=30)
        high = scoring_service.compute_prestige_score(effort_count=15000, athlete_count=5000)
        assert high > low
        assert 0 <= low <= 100 and 0 <= high <= 100

    def test_prestige_default_when_unknown(self, scoring_service: ScoringService):
        assert scoring_service.compute_prestige_score() == 25.0

    def test_competitiveness_rises_with_kom_speed(self, scoring_service: ScoringService):
        # Faster KOM (shorter time over same distance) = more competitive.
        fast = scoring_service.compute_competitiveness_score(
            distance_m=5000, kom_time_seconds=450, avg_grade=4.0  # 40 km/h
        )
        slow = scoring_service.compute_competitiveness_score(
            distance_m=5000, kom_time_seconds=900, avg_grade=4.0  # 20 km/h
        )
        assert fast > slow

    def test_competitiveness_default_when_unknown(self, scoring_service: ScoringService):
        assert scoring_service.compute_competitiveness_score(distance_m=5000) == 40.0

    def test_prestige_does_not_change_difficulty(self, scoring_service: ScoringService):
        """The headline difficulty must be identical regardless of popularity."""
        unpopular = scoring_service.compute_full_score(
            distance_m=5000, elevation_gain=350, avg_grade=7.0, activity_type="riding",
            effort_count=10, athlete_count=5, kom_time_seconds=900,
        )
        popular = scoring_service.compute_full_score(
            distance_m=5000, elevation_gain=350, avg_grade=7.0, activity_type="riding",
            effort_count=50000, athlete_count=20000, kom_time_seconds=450,
        )
        assert unpopular["normalized_score"] == popular["normalized_score"]
        assert popular["prestige_score"] > unpopular["prestige_score"]
        assert popular["competitiveness_score"] > unpopular["competitiveness_score"]


class TestCategories:
    def test_easy(self, scoring_service: ScoringService):
        assert scoring_service.get_category(15) == DifficultyCategory.EASY

    def test_moderate(self, scoring_service: ScoringService):
        assert scoring_service.get_category(35) == DifficultyCategory.MODERATE

    def test_hard(self, scoring_service: ScoringService):
        assert scoring_service.get_category(60) == DifficultyCategory.HARD

    def test_expert(self, scoring_service: ScoringService):
        assert scoring_service.get_category(90) == DifficultyCategory.EXPERT


class TestFullScoreShape:
    def test_full_score_keys(self, scoring_service: ScoringService):
        result = scoring_service.compute_full_score(
            distance_m=5000, elevation_gain=200, avg_grade=4.0, activity_type="riding"
        )
        for key in (
            "raw_score", "normalized_score", "category", "physical_score",
            "prestige_score", "competitiveness_score", "strava_category_points",
            "activity_type",
        ):
            assert key in result
        assert result["category"] in ["easy", "moderate", "hard", "expert"]
        # physical_score is the terrain difficulty (headline), by design
        assert result["physical_score"] == result["normalized_score"]
        assert result["activity_type"] == "riding"

    def test_normalize_score_helper(self, scoring_service: ScoringService):
        assert 0 <= scoring_service.normalize_score(50.0) <= 100
        assert scoring_service.normalize_score(0) == 0
        assert scoring_service.normalize_score(-10) == 0
