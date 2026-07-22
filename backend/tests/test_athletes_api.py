"""
Tests for the athletes API routes with the Strava upstream mocked via respx.
"""
import httpx
import respx
from fastapi.testclient import TestClient

STRAVA_ATHLETE_URL = "https://www.strava.com/api/v3/athlete"
STRAVA_STATS_URL = "https://www.strava.com/api/v3/athletes/12345/stats"
STRAVA_KOMS_URL = "https://www.strava.com/api/v3/athletes/12345/koms"

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
        "achievement_count": 3,
    },
    "ytd_ride_totals": {
        "count": 50,
        "distance": 2500000.0,
        "moving_time": 360000,
        "elapsed_time": 380000,
        "elevation_gain": 25000.0,
    },
    "all_ride_totals": {
        "count": 200,
        "distance": 10000000.0,
        "moving_time": 1440000,
        "elapsed_time": 1520000,
        "elevation_gain": 100000.0,
    },
}

KOMS_RESPONSE = [
    {
        "segment": {
            "id": 111,
            "name": "Test KOM Segment",
            "distance": 1500.0,
            "average_grade": 5.5,
        },
        "activity_id": 999,
        "elapsed_time": 862,
        "distance": 1500.0,
        "start_date": "2024-06-01T10:00:00Z",
        "start_date_local": "2024-06-01T12:00:00Z",
        "kom_rank": 1,
    },
    {
        "segment": {
            "id": 222,
            "name": "Long KOM Segment",
            "distance": 42000.0,
            "average_grade": 1.2,
        },
        "activity_id": 998,
        "elapsed_time": 3725,  # 1:02:05
        "distance": 42000.0,
        "start_date": "2024-05-01T10:00:00Z",
        "start_date_local": "2024-05-01T12:00:00Z",
        "kom_rank": 1,
    },
]


class TestGetMyProfile:
    """GET /api/athletes/me"""

    @respx.mock
    def test_profile_mapping(self, client: TestClient, auth_headers: dict):
        respx.get(STRAVA_ATHLETE_URL).mock(
            return_value=httpx.Response(200, json=ATHLETE_RESPONSE)
        )
        response = client.get("/api/athletes/me", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 12345
        assert data["firstname"] == "Test"
        assert data["lastname"] == "User"
        assert data["profile"] == "https://example.com/profile.jpg"
        assert data["city"] == "Boulder"
        assert data["state"] == "Colorado"
        assert data["country"] == "United States"
        assert data["premium"] is True

    @respx.mock
    def test_profile_strava_403_maps_to_401(
        self, client: TestClient, auth_headers: dict
    ):
        respx.get(STRAVA_ATHLETE_URL).mock(
            return_value=httpx.Response(403, json={"message": "Forbidden"})
        )
        response = client.get("/api/athletes/me", headers=auth_headers)
        assert response.status_code == 401
        assert (
            response.json()["detail"]
            == "Strava authorization failed - please log in again"
        )


class TestGetMyStats:
    """GET /api/athletes/me/stats — two-call sequence (/athlete then /stats)."""

    @respx.mock
    def test_stats_mapping(self, client: TestClient, auth_headers: dict):
        athlete_route = respx.get(STRAVA_ATHLETE_URL).mock(
            return_value=httpx.Response(200, json=ATHLETE_RESPONSE)
        )
        stats_route = respx.get(STRAVA_STATS_URL).mock(
            return_value=httpx.Response(200, json=STATS_RESPONSE)
        )
        response = client.get("/api/athletes/me/stats", headers=auth_headers)

        assert response.status_code == 200
        assert athlete_route.called
        assert stats_route.called

        data = response.json()
        assert data["biggest_ride_distance"] == 150000.0
        assert data["biggest_climb_elevation_gain"] == 1200.0
        assert data["recent_ride_totals"]["count"] == 10
        assert data["recent_ride_totals"]["achievement_count"] == 3
        assert data["ytd_ride_totals"]["distance"] == 2500000.0
        assert data["all_ride_totals"]["count"] == 200
        # Absent totals map to None
        assert data["recent_run_totals"] is None


class TestGetMyKOMs:
    """GET /api/athletes/me/koms"""

    @respx.mock
    def test_koms_elapsed_time_formatted(
        self, client: TestClient, auth_headers: dict
    ):
        respx.get(STRAVA_ATHLETE_URL).mock(
            return_value=httpx.Response(200, json=ATHLETE_RESPONSE)
        )
        respx.get(STRAVA_KOMS_URL).mock(
            return_value=httpx.Response(200, json=KOMS_RESPONSE)
        )
        response = client.get("/api/athletes/me/koms", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 2

        koms = data["koms"]
        assert koms[0]["segment_id"] == 111
        assert koms[0]["segment_name"] == "Test KOM Segment"
        assert koms[0]["elapsed_time"] == 862
        assert koms[0]["elapsed_time_formatted"] == "14:22"
        assert koms[0]["kom_rank"] == 1

        assert koms[1]["elapsed_time"] == 3725
        assert koms[1]["elapsed_time_formatted"] == "1:02:05"
