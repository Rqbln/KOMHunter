"""
Tests for the athletes API routes with the Strava upstream mocked via respx.
"""
import httpx
import pytest
import respx
from fastapi.testclient import TestClient

from app.api.routes import athletes as athletes_route
from app.models.athlete import HeatmapResponse

STRAVA_ATHLETE_URL = "https://www.strava.com/api/v3/athlete"
STRAVA_STATS_URL = "https://www.strava.com/api/v3/athletes/12345/stats"
STRAVA_KOMS_URL = "https://www.strava.com/api/v3/athletes/12345/koms"
STRAVA_ACTIVITIES_URL = "https://www.strava.com/api/v3/athlete/activities"

# Known-good encoded polylines (verified against the polyline util):
#   RIDE_POLYLINE -> [(38.5, -120.2), (40.7, -120.95)]
#   RUN_POLYLINE  -> [(50.0, 4.0), (50.1, 4.1)]
RIDE_POLYLINE = "_p~iF~ps|U_ulLnnqC"
RIDE_POINTS = [[38.5, -120.2], [40.7, -120.95]]
RUN_POLYLINE = "_sdpH_glW_pR_pR"
RUN_POINTS = [[50.0, 4.0], [50.1, 4.1]]

ACTIVITIES_RESPONSE = [
    {
        "id": 1001,
        "type": "Ride",
        "map": {"id": "a1001", "summary_polyline": RIDE_POLYLINE},
    },
    {
        "id": 1002,
        "type": "Run",
        "map": {"id": "a1002", "summary_polyline": RUN_POLYLINE},
    },
]

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

    @respx.mock
    def test_koms_activity_type_normalized(
        self, client: TestClient, auth_headers: dict
    ):
        # The nested segment carries Strava's activity_type ("Run"/"Ride" for
        # segments); it must be normalized to "running" (starts with "run") or
        # "riding" (everything else), defaulting to "riding" when absent.
        koms_response = [
            {
                "segment": {"id": 1, "name": "Run seg", "activity_type": "Run"},
                "activity_id": 10,
                "elapsed_time": 100,
            },
            {
                "segment": {"id": 2, "name": "Ride seg", "activity_type": "Ride"},
                "activity_id": 20,
                "elapsed_time": 200,
            },
            {
                # activity_type absent -> defaults to "riding"
                "segment": {"id": 3, "name": "No type seg"},
                "activity_id": 30,
                "elapsed_time": 300,
            },
        ]
        respx.get(STRAVA_ATHLETE_URL).mock(
            return_value=httpx.Response(200, json=ATHLETE_RESPONSE)
        )
        respx.get(STRAVA_KOMS_URL).mock(
            return_value=httpx.Response(200, json=koms_response)
        )
        response = client.get("/api/athletes/me/koms", headers=auth_headers)

        assert response.status_code == 200
        koms = response.json()["koms"]
        assert [k["activity_type"] for k in koms] == [
            "running",
            "riding",
            "riding",
        ]


class TestGetMyHeatmap:
    """GET /api/athletes/me/heatmap"""

    @pytest.fixture(autouse=True)
    def _clear_cache(self):
        """Isolate tests from the in-memory heatmap TTL cache."""
        athletes_route._HEATMAP_CACHE.clear()
        yield
        athletes_route._HEATMAP_CACHE.clear()

    @respx.mock
    def test_heatmap_all_sports(self, client: TestClient, auth_headers: dict):
        respx.get(STRAVA_ACTIVITIES_URL).mock(
            return_value=httpx.Response(200, json=ACTIVITIES_RESPONSE)
        )
        response = client.get("/api/athletes/me/heatmap", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["activity_count"] == 2
        assert data["sport"] is None
        # Both tracks contribute their decoded points, ride first then run.
        assert data["points"] == RIDE_POINTS + RUN_POINTS

    @respx.mock
    def test_heatmap_sport_ride_filters(
        self, client: TestClient, auth_headers: dict
    ):
        respx.get(STRAVA_ACTIVITIES_URL).mock(
            return_value=httpx.Response(200, json=ACTIVITIES_RESPONSE)
        )
        response = client.get(
            "/api/athletes/me/heatmap?sport=ride", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["activity_count"] == 1
        assert data["sport"] == "ride"
        assert data["points"] == RIDE_POINTS

    @respx.mock
    def test_heatmap_skips_empty_polyline(
        self, client: TestClient, auth_headers: dict
    ):
        activities = [
            {
                "id": 2001,
                "type": "Ride",
                "map": {"id": "a2001", "summary_polyline": RIDE_POLYLINE},
            },
            # Empty summary_polyline -> skipped, contributes no points.
            {"id": 2002, "type": "Ride", "map": {"summary_polyline": ""}},
            # Missing map entirely -> also skipped.
            {"id": 2003, "type": "Ride"},
        ]
        respx.get(STRAVA_ACTIVITIES_URL).mock(
            return_value=httpx.Response(200, json=activities)
        )
        response = client.get("/api/athletes/me/heatmap", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["activity_count"] == 1
        assert data["points"] == RIDE_POINTS

    @respx.mock
    def test_heatmap_pagination_stops_on_short_page(
        self, client: TestClient, auth_headers: dict
    ):
        activities_route = respx.get(STRAVA_ACTIVITIES_URL).mock(
            return_value=httpx.Response(200, json=ACTIVITIES_RESPONSE)
        )
        # max_activities=500 would allow up to 3 pages, but the first page is
        # short (2 < per_page) so pagination stops after a single Strava call.
        response = client.get(
            "/api/athletes/me/heatmap?max_activities=500", headers=auth_headers
        )

        assert response.status_code == 200
        assert activities_route.call_count == 1
        assert response.json()["activity_count"] == 2

    @respx.mock
    def test_heatmap_uses_cache_on_repeat(
        self, client: TestClient, auth_headers: dict
    ):
        activities_route = respx.get(STRAVA_ACTIVITIES_URL).mock(
            return_value=httpx.Response(200, json=ACTIVITIES_RESPONSE)
        )
        first = client.get("/api/athletes/me/heatmap", headers=auth_headers)
        second = client.get("/api/athletes/me/heatmap", headers=auth_headers)

        assert first.status_code == 200
        assert second.status_code == 200
        assert first.json() == second.json()
        # Second identical request is served from cache: no extra Strava call.
        assert activities_route.call_count == 1

    @respx.mock
    def test_heatmap_strava_429_maps_to_429(
        self, client: TestClient, auth_headers: dict
    ):
        respx.get(STRAVA_ACTIVITIES_URL).mock(
            return_value=httpx.Response(429, json={"message": "Rate Limit Exceeded"})
        )
        response = client.get("/api/athletes/me/heatmap", headers=auth_headers)

        assert response.status_code == 429
        assert (
            response.json()["detail"]
            == "Strava rate limit exceeded - try again later"
        )

    def test_heatmap_negative_after_rejected(
        self, client: TestClient, auth_headers: dict
    ):
        # after/before are epoch timestamps: negative values are invalid input
        # and must be rejected before they can seed a distinct cache key.
        response = client.get(
            "/api/athletes/me/heatmap?after=-1", headers=auth_headers
        )
        assert response.status_code == 422


class TestHeatmapCacheBounding:
    """The in-memory heatmap cache must stay bounded regardless of how many
    distinct (user-controlled) cache keys are generated."""

    @pytest.fixture(autouse=True)
    def _clear_cache(self):
        athletes_route._HEATMAP_CACHE.clear()
        yield
        athletes_route._HEATMAP_CACHE.clear()

    @staticmethod
    def _resp(n: int) -> HeatmapResponse:
        return HeatmapResponse(points=[[0.0, 0.0]], activity_count=n, sport=None)

    def test_cache_evicts_lru_over_capacity(self, monkeypatch):
        monkeypatch.setattr(athletes_route, "_HEATMAP_CACHE_MAX_ENTRIES", 3)
        for i in range(5):
            athletes_route._heatmap_cache_set((i,), self._resp(i))
        cache = athletes_route._HEATMAP_CACHE
        # Never exceeds the cap; the two oldest keys were evicted.
        assert len(cache) == 3
        assert set(cache.keys()) == {(2,), (3,), (4,)}

    def test_cache_get_refreshes_lru_recency(self, monkeypatch):
        monkeypatch.setattr(athletes_route, "_HEATMAP_CACHE_MAX_ENTRIES", 3)
        for i in range(3):
            athletes_route._heatmap_cache_set((i,), self._resp(i))
        # Touch the oldest key so it becomes most-recently-used.
        assert athletes_route._heatmap_cache_get((0,)) is not None
        # Inserting a 4th entry now evicts key (1,) (the true LRU), not (0,).
        athletes_route._heatmap_cache_set((3,), self._resp(3))
        cache = athletes_route._HEATMAP_CACHE
        assert len(cache) == 3
        assert (0,) in cache
        assert (1,) not in cache

    def test_cache_sweeps_expired_entries_on_write(self, monkeypatch):
        # TTL < 0 makes every previously stored entry expired on the next write.
        monkeypatch.setattr(athletes_route, "_HEATMAP_CACHE_TTL", -1.0)
        athletes_route._heatmap_cache_set((0,), self._resp(0))
        athletes_route._heatmap_cache_set((1,), self._resp(1))
        cache = athletes_route._HEATMAP_CACHE
        # (0,) was expired and swept when (1,) was written; it is not just
        # left dangling until its own key is re-read.
        assert (0,) not in cache
        assert (1,) in cache

    @respx.mock
    def test_heatmap_endpoint_cache_bounded_across_distinct_filters(
        self, client: TestClient, auth_headers: dict, monkeypatch
    ):
        monkeypatch.setattr(athletes_route, "_HEATMAP_CACHE_MAX_ENTRIES", 2)
        respx.get(STRAVA_ACTIVITIES_URL).mock(
            return_value=httpx.Response(200, json=ACTIVITIES_RESPONSE)
        )
        # Each distinct `after` is a distinct cache key (a miss), yet the cache
        # must not grow past the cap.
        for after in range(5):
            resp = client.get(
                f"/api/athletes/me/heatmap?after={after}", headers=auth_headers
            )
            assert resp.status_code == 200
        assert len(athletes_route._HEATMAP_CACHE) == 2
