"""
Tests for the rate-limit awareness feature:
- GET /api/strava/rate-limit shape + reflecting captured X-RateLimit headers
- athlete/response caching that collapses redundant Strava calls
- segment-detail route caching
- the max_segments hard cap (le=50)

Strava upstream is mocked via respx. The process-wide caches and rate-limit
snapshot are reset before each test by the autouse fixture in conftest.
"""
import httpx
import pytest
import respx
from fastapi.testclient import TestClient

STRAVA_ATHLETE_URL = "https://www.strava.com/api/v3/athlete"
STRAVA_STATS_URL = "https://www.strava.com/api/v3/athletes/12345/stats"
STRAVA_KOMS_URL = "https://www.strava.com/api/v3/athletes/12345/koms"
STRAVA_STARRED_URL = "https://www.strava.com/api/v3/segments/starred"
STRAVA_SEGMENT_URL = "https://www.strava.com/api/v3/segments/12345678"

ATHLETE_RESPONSE = {
    "id": 12345,
    "firstname": "Test",
    "lastname": "User",
    "profile": "https://example.com/profile.jpg",
    "profile_medium": "https://example.com/profile_medium.jpg",
    "city": "Boulder",
    "state": "Colorado",
    "country": "United States",
    "sex": "M",
    "premium": True,
    "created_at": "2020-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z",
}

STATS_RESPONSE = {
    "biggest_ride_distance": 150000.0,
    "biggest_climb_elevation_gain": 1200.0,
    "recent_ride_totals": {
        "count": 10,
        "distance": 500000.0,
        "moving_time": 72000,
        "elapsed_time": 76000,
        "elevation_gain": 5000.0,
    },
}

KOMS_RESPONSE = [
    {
        "segment": {"id": 111, "name": "Seg", "distance": 1500.0, "average_grade": 5.5},
        "activity_id": 999,
        "elapsed_time": 862,
    }
]

STARRED_RESPONSE = [
    {
        "id": 555,
        "name": "Starred Seg",
        "distance": 2000.0,
        "average_grade": 4.0,
        "elevation_high": 100.0,
        "elevation_low": 20.0,
        "climb_category": 1,
        "activity_type": "Ride",
    }
]

SEGMENT_DETAILS_RESPONSE = {
    "id": 12345678,
    "name": "Test Climb",
    "distance": 5200.0,
    "average_grade": 8.1,
    "maximum_grade": 15.2,
    "elevation_high": 2100.0,
    "elevation_low": 1760.0,
    "total_elevation_gain": 340.0,
    "start_latlng": [40.0150, -105.2705],
    "end_latlng": [40.0089, -105.2890],
    "climb_category": 3,
    "effort_count": 15234,
    "athlete_count": 4521,
    "star_count": 892,
    "activity_type": "Ride",
    "map": {"polyline": "_p~iF~ps|U_ulLnnqC"},
    "xoms": {"kom": "14:22", "qom": "16:45", "overall": "14:22"},
}


class TestRateLimitEndpoint:
    """GET /api/strava/rate-limit — no auth, no Strava call."""

    def test_shape_before_any_capture(self, client: TestClient):
        response = client.get("/api/strava/rate-limit")
        assert response.status_code == 200
        data = response.json()
        assert set(data) == {"short_term", "daily", "seconds_until_reset", "updated_at"}
        assert data["short_term"] == {"usage": None, "limit": None}
        assert data["daily"] == {"usage": None, "limit": None}
        assert data["updated_at"] is None
        # 15-min wall-clock window: strictly positive, never more than 900.
        assert 1 <= data["seconds_until_reset"] <= 900

    def test_requires_no_auth(self, client: TestClient):
        # No Authorization header at all still returns 200.
        response = client.get("/api/strava/rate-limit")
        assert response.status_code == 200

    @respx.mock
    def test_reflects_captured_general_headers(
        self, client: TestClient, auth_headers: dict
    ):
        respx.get(STRAVA_ATHLETE_URL).mock(
            return_value=httpx.Response(
                200,
                json=ATHLETE_RESPONSE,
                headers={
                    "X-RateLimit-Limit": "100,1000",
                    "X-RateLimit-Usage": "42,315",
                },
            )
        )
        # Any Strava call captures the headers as a side effect.
        assert client.get("/api/athletes/me", headers=auth_headers).status_code == 200

        data = client.get("/api/strava/rate-limit").json()
        assert data["short_term"] == {"usage": 42, "limit": 100}
        assert data["daily"] == {"usage": 315, "limit": 1000}
        assert data["updated_at"] is not None

    @respx.mock
    def test_prefers_read_specific_headers(
        self, client: TestClient, auth_headers: dict
    ):
        respx.get(STRAVA_ATHLETE_URL).mock(
            return_value=httpx.Response(
                200,
                json=ATHLETE_RESPONSE,
                headers={
                    "X-RateLimit-Limit": "100,1000",
                    "X-RateLimit-Usage": "90,900",
                    # Read-specific values must win (our calls are reads).
                    "X-ReadRateLimit-Limit": "300,3000",
                    "X-ReadRateLimit-Usage": "10,50",
                },
            )
        )
        assert client.get("/api/athletes/me", headers=auth_headers).status_code == 200

        data = client.get("/api/strava/rate-limit").json()
        assert data["short_term"] == {"usage": 10, "limit": 300}
        assert data["daily"] == {"usage": 50, "limit": 3000}

    @respx.mock
    def test_captured_on_429_too(self, client: TestClient, auth_headers: dict):
        respx.get(STRAVA_ATHLETE_URL).mock(
            return_value=httpx.Response(
                429,
                json={"message": "Rate Limit Exceeded"},
                headers={
                    "X-RateLimit-Limit": "100,1000",
                    "X-RateLimit-Usage": "100,420",
                },
            )
        )
        # The call fails (429) but usage must still be captured.
        assert client.get("/api/athletes/me", headers=auth_headers).status_code == 429

        data = client.get("/api/strava/rate-limit").json()
        assert data["short_term"] == {"usage": 100, "limit": 100}
        assert data["daily"] == {"usage": 420, "limit": 1000}


class TestAthleteCaching:
    """Redundant Strava calls are collapsed by the athlete/response caches."""

    @respx.mock
    def test_stats_cached_across_two_calls(
        self, client: TestClient, auth_headers: dict
    ):
        athlete_route = respx.get(STRAVA_ATHLETE_URL).mock(
            return_value=httpx.Response(200, json=ATHLETE_RESPONSE)
        )
        stats_route = respx.get(STRAVA_STATS_URL).mock(
            return_value=httpx.Response(200, json=STATS_RESPONSE)
        )
        first = client.get("/api/athletes/me/stats", headers=auth_headers)
        second = client.get("/api/athletes/me/stats", headers=auth_headers)

        assert first.status_code == 200
        assert second.status_code == 200
        assert first.json() == second.json()
        # Second call is fully served from cache: one athlete + one stats call.
        assert athlete_route.call_count == 1
        assert stats_route.call_count == 1

    @respx.mock
    def test_koms_cached_across_two_calls(
        self, client: TestClient, auth_headers: dict
    ):
        athlete_route = respx.get(STRAVA_ATHLETE_URL).mock(
            return_value=httpx.Response(200, json=ATHLETE_RESPONSE)
        )
        koms_route = respx.get(STRAVA_KOMS_URL).mock(
            return_value=httpx.Response(200, json=KOMS_RESPONSE)
        )
        client.get("/api/athletes/me/koms", headers=auth_headers)
        client.get("/api/athletes/me/koms", headers=auth_headers)

        assert athlete_route.call_count == 1
        assert koms_route.call_count == 1

    @respx.mock
    def test_starred_cached_across_two_calls(
        self, client: TestClient, auth_headers: dict
    ):
        starred_route = respx.get(STRAVA_STARRED_URL).mock(
            return_value=httpx.Response(200, json=STARRED_RESPONSE)
        )
        client.get("/api/athletes/me/starred", headers=auth_headers)
        client.get("/api/athletes/me/starred", headers=auth_headers)

        assert starred_route.call_count == 1

    @respx.mock
    def test_dashboard_open_fetches_athlete_once(
        self, client: TestClient, auth_headers: dict
    ):
        """A dashboard open (/me + /me/stats + /me/koms) shares one athlete call."""
        athlete_route = respx.get(STRAVA_ATHLETE_URL).mock(
            return_value=httpx.Response(200, json=ATHLETE_RESPONSE)
        )
        respx.get(STRAVA_STATS_URL).mock(
            return_value=httpx.Response(200, json=STATS_RESPONSE)
        )
        respx.get(STRAVA_KOMS_URL).mock(
            return_value=httpx.Response(200, json=KOMS_RESPONSE)
        )
        assert client.get("/api/athletes/me", headers=auth_headers).status_code == 200
        assert client.get("/api/athletes/me/stats", headers=auth_headers).status_code == 200
        assert client.get("/api/athletes/me/koms", headers=auth_headers).status_code == 200

        # Previously 3 independent /athlete fetches; now a single shared one.
        assert athlete_route.call_count == 1


class TestSegmentDetailCaching:
    """GET /api/segments/{id} is cached so repeat opens don't re-hit Strava."""

    @respx.mock
    def test_detail_cached_across_two_calls(
        self, client: TestClient, auth_headers: dict
    ):
        detail_route = respx.get(STRAVA_SEGMENT_URL).mock(
            return_value=httpx.Response(200, json=SEGMENT_DETAILS_RESPONSE)
        )
        first = client.get("/api/segments/12345678", headers=auth_headers)
        second = client.get("/api/segments/12345678", headers=auth_headers)

        assert first.status_code == 200
        assert second.status_code == 200
        assert first.json() == second.json()
        assert detail_route.call_count == 1


class TestMaxSegmentsCap:
    """max_segments hard cap is 50 (model le=50)."""

    def test_max_segments_51_rejected(self, client: TestClient, auth_headers: dict):
        payload = {
            "latitude": 40.015,
            "longitude": -105.270,
            "radius_km": 25,
            "max_segments": 51,
        }
        response = client.post(
            "/api/segments/explore", json=payload, headers=auth_headers
        )
        assert response.status_code == 422

    @respx.mock
    def test_max_segments_50_accepted(self, client: TestClient, auth_headers: dict):
        respx.get("https://www.strava.com/api/v3/segments/explore").mock(
            return_value=httpx.Response(200, json={"segments": []})
        )
        payload = {
            "latitude": 40.015,
            "longitude": -105.270,
            "radius_km": 25,
            "max_segments": 50,
        }
        response = client.post(
            "/api/segments/explore", json=payload, headers=auth_headers
        )
        assert response.status_code == 200
