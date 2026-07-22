"""
Tests for segment scoring service.
"""
import pytest
from app.services.scoring import ScoringService, DifficultyCategory


class TestScoringService:
    """Tests for ScoringService."""
    
    def test_compute_difficulty_basic(self, scoring_service: ScoringService):
        """Test basic difficulty calculation."""
        score = scoring_service.compute_difficulty(
            distance_m=5000,
            elevation_gain=200,
            avg_grade=4.0,
        )
        assert score > 0
        assert isinstance(score, float)
    
    def test_compute_difficulty_flat(self, scoring_service: ScoringService):
        """Test difficulty for flat segment."""
        score = scoring_service.compute_difficulty(
            distance_m=5000,
            elevation_gain=0,
            avg_grade=0,
        )
        # Flat segments should have lower difficulty
        steep_score = scoring_service.compute_difficulty(
            distance_m=5000,
            elevation_gain=400,
            avg_grade=8.0,
        )
        assert score < steep_score
    
    def test_compute_difficulty_zero_distance(self, scoring_service: ScoringService):
        """Test handling of zero distance: invalid segment scores 0.0."""
        score = scoring_service.compute_difficulty(
            distance_m=0,
            elevation_gain=100,
            avg_grade=5.0,
        )
        assert score == 0.0  # Invalid segment (no distance) -> no difficulty

    def test_compute_difficulty_with_kom_speed(self, scoring_service: ScoringService):
        """Test difficulty with KOM speed factor (unified semantics)."""
        # Faster KOM = more competitive segment = HIGHER difficulty score
        fast_kom_score = scoring_service.compute_difficulty(
            distance_m=5000,
            elevation_gain=200,
            avg_grade=4.0,
            kom_speed_kmh=40,
        )
        slow_kom_score = scoring_service.compute_difficulty(
            distance_m=5000,
            elevation_gain=200,
            avg_grade=4.0,
            kom_speed_kmh=20,
        )
        assert fast_kom_score > slow_kom_score
    
    def test_compute_difficulty_with_effort_count(self, scoring_service: ScoringService):
        """Test difficulty with effort count factor."""
        # Few efforts = potentially easier KOM
        few_efforts_score = scoring_service.compute_difficulty(
            distance_m=5000,
            elevation_gain=200,
            avg_grade=4.0,
            effort_count=50,
        )
        many_efforts_score = scoring_service.compute_difficulty(
            distance_m=5000,
            elevation_gain=200,
            avg_grade=4.0,
            effort_count=15000,
        )
        assert few_efforts_score < many_efforts_score
    
    def test_normalize_score(self, scoring_service: ScoringService):
        """Test score normalization to 0-100."""
        normalized = scoring_service.normalize_score(50.0, max_score=100)
        assert 0 <= normalized <= 100
    
    def test_normalize_score_zero(self, scoring_service: ScoringService):
        """Test normalization of zero score."""
        normalized = scoring_service.normalize_score(0)
        assert normalized == 0
    
    def test_normalize_score_negative(self, scoring_service: ScoringService):
        """Test normalization of negative score."""
        normalized = scoring_service.normalize_score(-10)
        assert normalized == 0
    
    def test_get_category_easy(self, scoring_service: ScoringService):
        """Test easy category classification."""
        category = scoring_service.get_category(15)
        assert category == DifficultyCategory.EASY
    
    def test_get_category_moderate(self, scoring_service: ScoringService):
        """Test moderate category classification."""
        category = scoring_service.get_category(35)
        assert category == DifficultyCategory.MODERATE
    
    def test_get_category_hard(self, scoring_service: ScoringService):
        """Test hard category classification."""
        category = scoring_service.get_category(60)
        assert category == DifficultyCategory.HARD
    
    def test_get_category_expert(self, scoring_service: ScoringService):
        """Test expert category classification."""
        category = scoring_service.get_category(90)
        assert category == DifficultyCategory.EXPERT
    
    def test_compute_full_score(self, scoring_service: ScoringService):
        """Test full scoring with all components."""
        result = scoring_service.compute_full_score(
            distance_m=5000,
            elevation_gain=200,
            avg_grade=4.0,
        )
        
        assert "raw_score" in result
        assert "normalized_score" in result
        assert "category" in result
        assert result["category"] in ["easy", "moderate", "hard", "expert"]
