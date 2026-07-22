"""
Tests for Settings validation — in particular the JWT secret guard that
must fail fast on missing/placeholder signing keys (a weak/known key lets
anyone forge session JWTs and the Strava tokens embedded in them).

The required Strava credentials are supplied from the environment by
conftest.py, so constructing Settings only needs a jwt_secret_key override.
"""
import pytest
from pydantic import ValidationError

from app.config import Settings


class TestJWTSecretValidation:
    def test_default_placeholder_rejected(self):
        # The field default itself is a placeholder and must not be usable.
        with pytest.raises(ValidationError):
            Settings(jwt_secret_key="your-secret-key-change-in-production")

    @pytest.mark.parametrize(
        "placeholder",
        [
            "please-CHANGE-me",
            "change-this-now",
            "your-secret-value",
            "YOUR-SECRET-KEY",
        ],
    )
    def test_placeholder_variants_rejected(self, placeholder: str):
        with pytest.raises(ValidationError):
            Settings(jwt_secret_key=placeholder)

    @pytest.mark.parametrize("blank", ["", "   "])
    def test_empty_or_blank_rejected(self, blank: str):
        with pytest.raises(ValidationError):
            Settings(jwt_secret_key=blank)

    def test_real_secret_accepted(self):
        secret = "a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2"
        settings = Settings(jwt_secret_key=secret)
        assert settings.jwt_secret_key == secret
