"""
Tests for the segments API routes with the Strava upstream mocked via respx.
"""
import httpx
import pytest
import respx
from fastapi.testclient import TestClient

from app.services import enrichment as enrichment_service

STRAVA_EXPLORE_URL = "https://www.strava.com/api/v3/segments/explore"
STRAVA_SEGMENT_URL = "https://www.strava.com/api/v3/segments/12345678"
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"


def _detail_url(segment_id: int) -> str:
    return f"https://www.strava.com/api/v3/segments/{segment_id}"


def _detail_body(
    segment_id: int,
    *,
    effort_count: int,
    athlete_count: int,
    kom: str,
    distance: float = 5000.0,
    average_grade: float = 5.0,
    activity_type: str = "Ride",
    athlete_pr_seconds: int | None = None,
) -> dict:
    """Minimal Strava segment-detail body sufficient for enrichment scoring."""
    body = {
        "id": segment_id,
        "name": f"Segment {segment_id}",
        "distance": distance,
        "average_grade": average_grade,
        "effort_count": effort_count,
        "athlete_count": athlete_count,
        "activity_type": activity_type,
        "xoms": {"kom": kom, "qom": kom, "overall": kom},
    }
    if athlete_pr_seconds is not None:
        body["athlete_segment_stats"] = {"pr_elapsed_time": athlete_pr_seconds}
    return body

EXPLORE_REQUEST = {
    "latitude": 48.8566,
    "longitude": 2.3522,
    "radius_km": 10,
    "activity_type": "riding",
    "max_segments": 50,
}

EXPLORE_RESPONSE = {
    "segments": [
        {
            "id": 1,
            "name": "Hard Climb",
            "distance": 5200.0,
            "avg_grade": 8.1,
            "elev_difference": 340.0,
            "start_latlng": [48.85, 2.35],
            "end_latlng": [48.86, 2.36],
            "climb_category": 3,
        },
        {
            "id": 2,
            "name": "Flat Sprint",
            "distance": 800.0,
            "avg_grade": 0.5,
            "elev_difference": 4.0,
            "start_latlng": [48.84, 2.34],
            "end_latlng": [48.85, 2.35],
            "climb_category": 0,
        },
    ]
}

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
    "city": "Boulder",
    "state": "Colorado",
    "country": "United States",
    "effort_count": 15234,
    "athlete_count": 4521,
    "star_count": 892,
    "map": {"polyline": "_p~iF~ps|U_ulLnnqC"},
    "xoms": {
        "kom": "14:22",
        "qom": "16:45",
        "overall": "14:22",
    },
    "local_legend": {
        "title": "Local Hero",
        "effort_description": "52 efforts in the last 90 days",
    },
}


class TestExploreSegments:
    """POST /api/segments/explore"""

    @respx.mock
    def test_explore_returns_schema_and_sorted_difficulty(
        self, client: TestClient, auth_headers: dict
    ):
        respx.get(STRAVA_EXPLORE_URL).mock(
            return_value=httpx.Response(200, json=EXPLORE_RESPONSE)
        )
        response = client.post(
            "/api/segments/explore", json=EXPLORE_REQUEST, headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 2
        assert data["center_lat"] == EXPLORE_REQUEST["latitude"]
        assert data["center_lon"] == EXPLORE_REQUEST["longitude"]
        assert data["radius_km"] == EXPLORE_REQUEST["radius_km"]
        assert len(data["segments"]) == 2

        for segment in data["segments"]:
            for field in (
                "id", "name", "distance", "avg_grade", "elev_difference",
                "start_latlng", "end_latlng", "climb_category", "difficulty_score",
            ):
                assert field in segment

        # Sorted by difficulty ascending (easiest first)
        scores = [s["difficulty_score"] for s in data["segments"]]
        assert scores == sorted(scores)

    @respx.mock
    def test_explore_forwards_cat_filters_to_strava(
        self, client: TestClient, auth_headers: dict
    ):
        route = respx.get(STRAVA_EXPLORE_URL).mock(
            return_value=httpx.Response(200, json=EXPLORE_RESPONSE)
        )
        payload = {**EXPLORE_REQUEST, "min_cat": 2, "max_cat": 4}
        response = client.post(
            "/api/segments/explore", json=payload, headers=auth_headers
        )

        assert response.status_code == 200
        # The outgoing Strava request must carry the requested category bounds.
        params = route.calls.last.request.url.params
        assert params["min_cat"] == "2"
        assert params["max_cat"] == "4"

    @respx.mock
    def test_explore_defaults_full_cat_range_to_strava(
        self, client: TestClient, auth_headers: dict
    ):
        route = respx.get(STRAVA_EXPLORE_URL).mock(
            return_value=httpx.Response(200, json=EXPLORE_RESPONSE)
        )
        response = client.post(
            "/api/segments/explore", json=EXPLORE_REQUEST, headers=auth_headers
        )

        assert response.status_code == 200
        params = route.calls.last.request.url.params
        assert params["min_cat"] == "0"
        assert params["max_cat"] == "5"

    @respx.mock
    def test_explore_grade_filter_drops_out_of_range(
        self, client: TestClient, auth_headers: dict
    ):
        respx.get(STRAVA_EXPLORE_URL).mock(
            return_value=httpx.Response(200, json=EXPLORE_RESPONSE)
        )
        # Segment 1 avg_grade=8.1 (kept), Segment 2 avg_grade=0.5 (dropped).
        payload = {**EXPLORE_REQUEST, "min_grade": 5.0}
        response = client.post(
            "/api/segments/explore", json=payload, headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 1
        assert [s["id"] for s in data["segments"]] == [1]

    @respx.mock
    def test_explore_distance_filter_drops_out_of_range(
        self, client: TestClient, auth_headers: dict
    ):
        respx.get(STRAVA_EXPLORE_URL).mock(
            return_value=httpx.Response(200, json=EXPLORE_RESPONSE)
        )
        # Segment 1 distance=5200 (dropped), Segment 2 distance=800 (kept).
        payload = {**EXPLORE_REQUEST, "max_distance_m": 1000}
        response = client.post(
            "/api/segments/explore", json=payload, headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 1
        assert [s["id"] for s in data["segments"]] == [2]

    @respx.mock
    def test_explore_combined_grade_and_distance_filters(
        self, client: TestClient, auth_headers: dict
    ):
        respx.get(STRAVA_EXPLORE_URL).mock(
            return_value=httpx.Response(200, json=EXPLORE_RESPONSE)
        )
        # Bounds that both stored segments satisfy -> nothing dropped.
        payload = {
            **EXPLORE_REQUEST,
            "min_grade": 0.0,
            "max_grade": 10.0,
            "min_distance_m": 500,
            "max_distance_m": 6000,
        }
        response = client.post(
            "/api/segments/explore", json=payload, headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 2
        assert sorted(s["id"] for s in data["segments"]) == [1, 2]

    def test_explore_requires_auth(self, client: TestClient):
        response = client.post("/api/segments/explore", json=EXPLORE_REQUEST)
        assert response.status_code == 401
        assert response.json()["detail"] == "Authorization header required"

    @respx.mock
    def test_strava_401_maps_to_api_401(self, client: TestClient, auth_headers: dict):
        respx.get(STRAVA_EXPLORE_URL).mock(
            return_value=httpx.Response(401, json={"message": "Unauthorized"})
        )
        response = client.post(
            "/api/segments/explore", json=EXPLORE_REQUEST, headers=auth_headers
        )
        assert response.status_code == 401
        assert (
            response.json()["detail"]
            == "Strava authorization failed - please log in again"
        )

    @respx.mock
    def test_strava_429_maps_to_api_429(self, client: TestClient, auth_headers: dict):
        respx.get(STRAVA_EXPLORE_URL).mock(
            return_value=httpx.Response(429, json={"message": "Rate Limit Exceeded"})
        )
        response = client.post(
            "/api/segments/explore", json=EXPLORE_REQUEST, headers=auth_headers
        )
        assert response.status_code == 429
        # map_strava_error now embeds the cooldown and sets Retry-After.
        assert response.json()["detail"].startswith("Strava rate limit exceeded - retry in")
        assert "Retry-After" in response.headers

    @respx.mock
    def test_strava_500_maps_to_api_502(self, client: TestClient, auth_headers: dict):
        respx.get(STRAVA_EXPLORE_URL).mock(
            return_value=httpx.Response(500, json={"message": "Server Error"})
        )
        response = client.post(
            "/api/segments/explore", json=EXPLORE_REQUEST, headers=auth_headers
        )
        assert response.status_code == 502


def _tile_segment(seg_id: int) -> dict:
    """A minimal explore-result segment carrying the fields the route needs."""
    return {
        "id": seg_id,
        "name": f"Segment {seg_id}",
        "distance": 4000.0,
        "avg_grade": 4.0,
        "elev_difference": 160.0,
        "start_latlng": [48.85, 2.35],
        "end_latlng": [48.86, 2.36],
        "climb_category": 1,
    }


def _tile_body(ids) -> dict:
    return {"segments": [_tile_segment(i) for i in ids]}


class TestExploreTiling:
    """POST /api/segments/explore tiles the area to exceed Strava's ~10/box cap."""

    @respx.mock
    def test_tiling_returns_deduped_union_truncated_to_max(
        self, client: TestClient, auth_headers: dict
    ):
        # max_segments=30 -> N = min(4, ceil(sqrt(30/10))) = 2 -> 2x2 = 4 tiles.
        # Each tile returns a DIFFERENT body (respx serves the side_effect list in
        # call order); bodies overlap so dedup-by-id is exercised. Union of unique
        # ids spans 1..32 (32 ids); truncation caps the response at 30.
        bodies = [
            httpx.Response(200, json=_tile_body(range(1, 11))),    # 1..10
            httpx.Response(200, json=_tile_body(range(11, 21))),   # 11..20
            httpx.Response(200, json=_tile_body(range(21, 31))),   # 21..30
            httpx.Response(200, json=_tile_body([5, 6, 25, 26, 31, 32])),  # overlaps + 31,32
        ]
        route = respx.get(STRAVA_EXPLORE_URL).mock(side_effect=bodies)

        payload = {**EXPLORE_REQUEST, "max_segments": 30}
        response = client.post(
            "/api/segments/explore", json=payload, headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        # Tiling happened (more than one explore call) but stayed within the cap.
        assert route.call_count == 4
        assert 1 < route.call_count <= 16

        ids = [s["id"] for s in data["segments"]]
        # Deduped: no repeats.
        assert len(ids) == len(set(ids))
        # More than a single box could ever yield.
        assert len(ids) > 10
        # Truncated to max_segments (32 unique ids available -> capped at 30).
        assert len(ids) == 30
        assert data["total_count"] == 30
        # Every returned id belongs to the union that was mocked.
        assert set(ids) <= set(range(1, 33))

    @respx.mock
    def test_small_max_segments_uses_single_call(
        self, client: TestClient, auth_headers: dict
    ):
        # max_segments <= 10 must not tile: exactly one explore call.
        route = respx.get(STRAVA_EXPLORE_URL).mock(
            return_value=httpx.Response(200, json=EXPLORE_RESPONSE)
        )
        payload = {**EXPLORE_REQUEST, "max_segments": 5}
        response = client.post(
            "/api/segments/explore", json=payload, headers=auth_headers
        )
        assert response.status_code == 200
        assert route.call_count == 1


# Three explore segments used by the enriched-sort tests. Geometry is uniform
# (distance 5000 m, grade 5%) so ordering is driven purely by the per-segment
# detail (effort/athlete counts + KOM time) mocked in each test.
EXPLORE_RESPONSE_3 = {
    "segments": [
        {
            "id": 10,
            "name": "Alpha",
            "distance": 5000.0,
            "avg_grade": 5.0,
            "elev_difference": 250.0,
            "start_latlng": [48.85, 2.35],
            "end_latlng": [48.86, 2.36],
            "climb_category": 2,
        },
        {
            "id": 11,
            "name": "Bravo",
            "distance": 5000.0,
            "avg_grade": 5.0,
            "elev_difference": 250.0,
            "start_latlng": [48.85, 2.35],
            "end_latlng": [48.86, 2.36],
            "climb_category": 2,
        },
        {
            "id": 12,
            "name": "Charlie",
            "distance": 5000.0,
            "avg_grade": 5.0,
            "elev_difference": 250.0,
            "start_latlng": [48.85, 2.35],
            "end_latlng": [48.86, 2.36],
            "climb_category": 2,
        },
    ]
}

# Per-segment detail chosen so each enriched sort yields a DISTINCT order:
#   prestige (effort/athlete): seg10 highest, seg12 mid,  seg11 lowest
#   competitiveness (KOM):     seg11 slowest (lowest), seg12 mid, seg10 fastest
#   -> popularity      DESC: [10, 12, 11]
#   -> competitiveness ASC : [11, 12, 10]
#   -> opportunity     DESC: [12, 11, 10]
_ENRICH_DETAILS = {
    10: dict(effort_count=100000, athlete_count=20000, kom="10:00"),
    11: dict(effort_count=100, athlete_count=50, kom="25:00"),
    12: dict(effort_count=5000, athlete_count=1500, kom="15:00"),
}


def _mock_enrich_details():
    """Mock the /segments/{id} detail endpoint for each enriched segment."""
    for seg_id, spec in _ENRICH_DETAILS.items():
        respx.get(_detail_url(seg_id)).mock(
            return_value=httpx.Response(200, json=_detail_body(seg_id, **spec))
        )


class TestExploreSortByEnrichment:
    """POST /api/segments/explore with enriched sort_by (popularity/etc.)."""

    @pytest.fixture(autouse=True)
    def _clear_cache(self):
        """Isolate tests from the module-level segment-detail TTL cache."""
        enrichment_service._DETAIL_CACHE.clear()
        yield
        enrichment_service._DETAIL_CACHE.clear()

    def _explore(self, client, auth_headers, sort_by):
        respx.get(STRAVA_EXPLORE_URL).mock(
            return_value=httpx.Response(200, json=EXPLORE_RESPONSE_3)
        )
        return client.post(
            "/api/segments/explore",
            json={**EXPLORE_REQUEST, "sort_by": sort_by},
            headers=auth_headers,
        )

    def test_invalid_sort_by_rejected_422(
        self, client: TestClient, auth_headers: dict
    ):
        response = client.post(
            "/api/segments/explore",
            json={**EXPLORE_REQUEST, "sort_by": "bogus"},
            headers=auth_headers,
        )
        assert response.status_code == 422

    @respx.mock
    def test_sort_by_popularity_orders_prestige_desc(
        self, client: TestClient, auth_headers: dict
    ):
        _mock_enrich_details()
        response = self._explore(client, auth_headers, "popularity")

        assert response.status_code == 200
        segments = response.json()["segments"]
        assert [s["id"] for s in segments] == [10, 12, 11]
        # prestige populated and strictly descending in returned order.
        prestiges = [s["prestige_score"] for s in segments]
        assert all(p is not None for p in prestiges)
        assert prestiges == sorted(prestiges, reverse=True)
        # Enrichment fields surfaced on the summary.
        assert segments[0]["effort_count"] == 100000
        assert segments[0]["athlete_count"] == 20000
        assert segments[0]["kom_time"] == "10:00"

    @respx.mock
    def test_sort_by_competitiveness_orders_asc_slowest_kom_first(
        self, client: TestClient, auth_headers: dict
    ):
        _mock_enrich_details()
        response = self._explore(client, auth_headers, "competitiveness")

        assert response.status_code == 200
        segments = response.json()["segments"]
        # Slowest KOM (seg 11, 25:00) => lowest competitiveness => first.
        assert [s["id"] for s in segments] == [11, 12, 10]
        comps = [s["competitiveness_score"] for s in segments]
        assert all(c is not None for c in comps)
        assert comps == sorted(comps)  # ascending

    @respx.mock
    def test_sort_by_opportunity_orders_combined_desc(
        self, client: TestClient, auth_headers: dict
    ):
        _mock_enrich_details()
        response = self._explore(client, auth_headers, "opportunity")

        assert response.status_code == 200
        segments = response.json()["segments"]
        # opportunity = prestige * (1 - competitiveness/100), highest first.
        assert [s["id"] for s in segments] == [12, 11, 10]
        opportunities = [
            s["prestige_score"] * (1 - s["competitiveness_score"] / 100.0)
            for s in segments
        ]
        assert opportunities == sorted(opportunities, reverse=True)

    @respx.mock
    def test_enrichment_caches_detail_across_calls(
        self, client: TestClient, auth_headers: dict
    ):
        detail_routes = {
            seg_id: respx.get(_detail_url(seg_id)).mock(
                return_value=httpx.Response(
                    200, json=_detail_body(seg_id, **spec)
                )
            )
            for seg_id, spec in _ENRICH_DETAILS.items()
        }
        first = self._explore(client, auth_headers, "popularity")
        second = self._explore(client, auth_headers, "popularity")

        assert first.status_code == 200
        assert second.status_code == 200
        assert first.json()["segments"] == second.json()["segments"]
        # Each segment's detail is fetched once and reused from cache thereafter.
        for route in detail_routes.values():
            assert route.call_count == 1

    @respx.mock
    def test_failing_detail_does_not_500_and_sorts_last(
        self, client: TestClient, auth_headers: dict
    ):
        # seg 10 & 11 succeed; seg 12's detail 500s -> null enrichment, sorts last.
        respx.get(_detail_url(10)).mock(
            return_value=httpx.Response(200, json=_detail_body(10, **_ENRICH_DETAILS[10]))
        )
        respx.get(_detail_url(11)).mock(
            return_value=httpx.Response(200, json=_detail_body(11, **_ENRICH_DETAILS[11]))
        )
        respx.get(_detail_url(12)).mock(
            return_value=httpx.Response(500, json={"message": "Server Error"})
        )
        response = self._explore(client, auth_headers, "popularity")

        assert response.status_code == 200
        segments = response.json()["segments"]
        assert len(segments) == 3
        # The un-enriched segment is last with null prestige.
        assert segments[-1]["id"] == 12
        assert segments[-1]["prestige_score"] is None
        assert segments[-1]["competitiveness_score"] is None
        # The enriched segments keep their prestige and lead the ordering.
        assert {s["id"] for s in segments[:2]} == {10, 11}
        assert all(s["prestige_score"] is not None for s in segments[:2])

    @respx.mock
    def test_default_sort_does_not_enrich(
        self, client: TestClient, auth_headers: dict
    ):
        respx.get(STRAVA_EXPLORE_URL).mock(
            return_value=httpx.Response(200, json=EXPLORE_RESPONSE)
        )
        # Detail routes registered but must never be called under the default sort.
        d1 = respx.get(_detail_url(1)).mock(
            return_value=httpx.Response(200, json=_detail_body(1, effort_count=1, athlete_count=1, kom="5:00"))
        )
        d2 = respx.get(_detail_url(2)).mock(
            return_value=httpx.Response(200, json=_detail_body(2, effort_count=1, athlete_count=1, kom="5:00"))
        )
        response = client.post(
            "/api/segments/explore", json=EXPLORE_REQUEST, headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        # Default difficulty sort, ascending, and no enrichment performed.
        scores = [s["difficulty_score"] for s in data["segments"]]
        assert scores == sorted(scores)
        assert all(s["prestige_score"] is None for s in data["segments"])
        assert d1.call_count == 0
        assert d2.call_count == 0


_SUSPICIOUS_EXPLORE = {
    "segments": [
        {  # legit run segment
            "id": 20, "name": "Legit Run", "distance": 3000.0, "avg_grade": 4.0,
            "elev_difference": 120.0, "start_latlng": [48.85, 2.35],
            "end_latlng": [48.86, 2.36], "climb_category": 0,
        },
        {  # bogus: 490 m "run" with a 20 s KOM (~88 km/h)
            "id": 21, "name": "Souvenir Seller Dodge", "distance": 490.0,
            "avg_grade": 1.9, "elev_difference": 12.0, "start_latlng": [48.84, 2.34],
            "end_latlng": [48.85, 2.35], "climb_category": 0,
        },
    ]
}


class TestKomPlausibilityAndReliable:
    """Suspicious-KOM flagging, sort-last behaviour, and reliable_only filter."""

    @pytest.fixture(autouse=True)
    def _clear_cache(self):
        enrichment_service._DETAIL_CACHE.clear()
        yield
        enrichment_service._DETAIL_CACHE.clear()

    def _mock(self):
        respx.get(STRAVA_EXPLORE_URL).mock(
            return_value=httpx.Response(200, json=_SUSPICIOUS_EXPLORE)
        )
        # seg 20: normal run KOM; seg 21: bogus 490 m / 20 s run KOM.
        respx.get(_detail_url(20)).mock(return_value=httpx.Response(
            200, json=_detail_body(20, effort_count=8000, athlete_count=3000,
                                    kom="12:00", distance=3000.0, activity_type="Run")))
        respx.get(_detail_url(21)).mock(return_value=httpx.Response(
            200, json=_detail_body(21, effort_count=9000, athlete_count=3500,
                                    kom="0:20", distance=490.0, activity_type="Run")))

    @respx.mock
    def test_suspicious_kom_sorts_last_even_with_high_prestige(
        self, client: TestClient, auth_headers: dict
    ):
        self._mock()
        response = client.post(
            "/api/segments/explore",
            json={**EXPLORE_REQUEST, "activity_type": "running", "sort_by": "popularity"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        segments = response.json()["segments"]
        # seg 21 has HIGHER prestige but a bogus KOM -> forced last.
        assert [s["id"] for s in segments] == [20, 21]
        assert segments[-1]["kom_suspicious"] is True
        assert segments[0]["kom_suspicious"] is False

    @respx.mock
    def test_reliable_only_drops_suspicious(
        self, client: TestClient, auth_headers: dict
    ):
        self._mock()
        response = client.post(
            "/api/segments/explore",
            json={**EXPLORE_REQUEST, "activity_type": "running",
                  "sort_by": "difficulty", "reliable_only": True},
            headers=auth_headers,
        )
        assert response.status_code == 200
        segments = response.json()["segments"]
        assert [s["id"] for s in segments] == [20]  # bogus seg 21 dropped
        assert all(not s["kom_suspicious"] for s in segments)


class TestSegmentDetails:
    """GET /api/segments/{segment_id}"""

    @respx.mock
    def test_details_parses_kom_from_xoms(
        self, client: TestClient, auth_headers: dict
    ):
        respx.get(STRAVA_SEGMENT_URL).mock(
            return_value=httpx.Response(200, json=SEGMENT_DETAILS_RESPONSE)
        )
        response = client.get("/api/segments/12345678", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 12345678
        assert data["name"] == "Test Climb"
        assert data["polyline"] == "_p~iF~ps|U_ulLnnqC"

        kom = data["kom"]
        assert kom is not None
        assert kom["kom_time"] == "14:22"
        assert kom["qom_time"] == "16:45"
        assert kom["overall_time"] == "14:22"
        assert kom["kom_time_seconds"] == 14 * 60 + 22  # 862
        assert kom["qom_time_seconds"] == 16 * 60 + 45  # 1005
        assert kom["local_legend_name"] == "Local Hero"

        breakdown = data["difficulty_breakdown"]
        assert breakdown is not None
        assert breakdown["category"] in ("easy", "moderate", "hard", "expert")
        assert 0 <= breakdown["normalized_score"] <= 100

    @respx.mock
    def test_details_exposes_athlete_pr_gap(
        self, client: TestClient, auth_headers: dict
    ):
        """athlete_segment_stats.pr_elapsed_time surfaces as the athlete PR."""
        payload = {**SEGMENT_DETAILS_RESPONSE, "athlete_segment_stats": {"pr_elapsed_time": 905}}
        respx.get(STRAVA_SEGMENT_URL).mock(
            return_value=httpx.Response(200, json=payload)
        )
        response = client.get("/api/segments/12345678", headers=auth_headers)
        assert response.status_code == 200
        kom = response.json()["kom"]
        assert kom["athlete_pr_seconds"] == 905
        assert kom["athlete_pr_time"] == "15:05"
        assert kom["kom_suspicious"] is False

    @respx.mock
    def test_details_cache_is_per_athlete_not_shared(
        self, client: TestClient, make_jwt
    ):
        """Detail cache must be keyed per athlete, never by segment_id alone.

        Regression: the response embeds the requesting athlete's own PR
        (athlete_segment_stats.pr_elapsed_time -> kom.athlete_pr_seconds). With a
        segment-id-only cache key, User A opening a segment poisoned the entry
        with A's PR, so User B opening the same segment within the TTL received
        A's private effort time as their own 'distance from the KOM'.
        """
        body_a = {
            **SEGMENT_DETAILS_RESPONSE,
            "athlete_segment_stats": {"pr_elapsed_time": 905},
        }
        # B has never ridden it: Strava returns no athlete_segment_stats.
        body_b = {k: v for k, v in SEGMENT_DETAILS_RESPONSE.items()}
        route = respx.get(STRAVA_SEGMENT_URL).mock(
            side_effect=[
                httpx.Response(200, json=body_a),
                httpx.Response(200, json=body_b),
            ]
        )

        headers_a = {"Authorization": f"Bearer {make_jwt(athlete_id=111)}"}
        headers_b = {"Authorization": f"Bearer {make_jwt(athlete_id=222)}"}

        resp_a = client.get("/api/segments/12345678", headers=headers_a)
        assert resp_a.status_code == 200
        assert resp_a.json()["kom"]["athlete_pr_seconds"] == 905

        resp_b = client.get("/api/segments/12345678", headers=headers_b)
        assert resp_b.status_code == 200
        # B's own PR is null — it must NOT see A's cached 905.
        kom_b = resp_b.json()["kom"]
        assert kom_b is None or kom_b.get("athlete_pr_seconds") is None
        # A different sub is a cache miss, so B's request reached Strava.
        assert route.call_count == 2

    @respx.mock
    def test_details_cached_per_athlete_single_upstream_call(
        self, client: TestClient, auth_headers: dict
    ):
        """Repeat opens by the SAME athlete hit the cache: one upstream call."""
        route = respx.get(STRAVA_SEGMENT_URL).mock(
            return_value=httpx.Response(200, json=SEGMENT_DETAILS_RESPONSE)
        )
        first = client.get("/api/segments/12345678", headers=auth_headers)
        second = client.get("/api/segments/12345678", headers=auth_headers)

        assert first.status_code == 200
        assert second.status_code == 200
        assert first.json() == second.json()
        # Second open is served from cache — Strava is hit exactly once.
        assert route.call_count == 1

    @respx.mock
    def test_details_flags_suspicious_kom(
        self, client: TestClient, auth_headers: dict
    ):
        """A 490 m run with a 20 s KOM (~88 km/h) is flagged suspicious."""
        payload = {
            **SEGMENT_DETAILS_RESPONSE,
            "distance": 490.0,
            "activity_type": "Run",
            "xoms": {"kom": "0:20", "qom": "0:25", "overall": "0:20"},
        }
        respx.get(STRAVA_SEGMENT_URL).mock(
            return_value=httpx.Response(200, json=payload)
        )
        response = client.get("/api/segments/12345678", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["kom_suspicious"] is True
        assert data["kom"]["kom_suspicious"] is True

    @respx.mock
    def test_details_null_city_state_country_coerced(
        self, client: TestClient, auth_headers: dict
    ):
        """Strava sends null city/state/country for many segments — must not 500."""
        payload = {**SEGMENT_DETAILS_RESPONSE, "city": None, "state": None, "country": None}
        respx.get(STRAVA_SEGMENT_URL).mock(
            return_value=httpx.Response(200, json=payload)
        )
        response = client.get("/api/segments/12345678", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["city"] == ""
        assert data["state"] == ""
        assert data["country"] == ""

    @respx.mock
    def test_details_strava_401_maps_to_api_401(
        self, client: TestClient, auth_headers: dict
    ):
        respx.get(STRAVA_SEGMENT_URL).mock(
            return_value=httpx.Response(401, json={"message": "Unauthorized"})
        )
        response = client.get("/api/segments/12345678", headers=auth_headers)
        assert response.status_code == 401
        assert (
            response.json()["detail"]
            == "Strava authorization failed - please log in again"
        )


class TestGeocode:
    """GET /api/segments/geocode (Nominatim upstream) — autocomplete suggestions."""

    @pytest.fixture(autouse=True)
    def _clear_geocoding_cache(self):
        """
        The geocoding service is an @lru_cache'd singleton, so its in-memory
        ``_cache`` would otherwise leak between tests (a query mocked one way in
        one test could return a cached value in another). Reset it around each
        test so every case starts from a clean, network-backed state.
        """
        from app.api.dependencies import get_geocoding_service

        get_geocoding_service.cache_clear()
        yield
        get_geocoding_service.cache_clear()

    @respx.mock
    def test_geocode_success_returns_results_list(self, client: TestClient):
        respx.get(NOMINATIM_URL).mock(
            return_value=httpx.Response(
                200,
                json=[
                    {
                        "lat": "48.8566",
                        "lon": "2.3522",
                        "display_name": "Paris, Ile-de-France, France",
                        "type": "city",
                    }
                ],
            )
        )
        response = client.get("/api/segments/geocode", params={"query": "Paris"})

        assert response.status_code == 200
        data = response.json()
        assert list(data.keys()) == ["results"]
        assert len(data["results"]) == 1
        first = data["results"][0]
        assert first["latitude"] == 48.8566
        assert first["longitude"] == 2.3522
        assert "Paris" in first["display_name"]
        assert first["type"] == "city"

    @respx.mock
    def test_geocode_multiple_results(self, client: TestClient):
        respx.get(NOMINATIM_URL).mock(
            return_value=httpx.Response(
                200,
                json=[
                    {
                        "lat": "48.8566",
                        "lon": "2.3522",
                        "display_name": "Paris, France",
                        "type": "city",
                    },
                    {
                        "lat": "33.6617",
                        "lon": "-95.5555",
                        "display_name": "Paris, Texas, USA",
                        "type": "city",
                    },
                    {
                        "lat": "38.2098",
                        "lon": "-84.2528",
                        "display_name": "Paris, Kentucky, USA",
                        "type": "town",
                    },
                ],
            )
        )
        response = client.get(
            "/api/segments/geocode", params={"query": "Paris-multi"}
        )

        assert response.status_code == 200
        results = response.json()["results"]
        assert len(results) == 3
        assert all(
            {"latitude", "longitude", "display_name", "type"} <= set(r)
            for r in results
        )
        # Order preserved from Nominatim; lat/lon coerced to floats.
        assert results[1]["latitude"] == 33.6617
        assert results[2]["type"] == "town"

    @respx.mock
    def test_geocode_empty_query_returns_empty_results(self, client: TestClient):
        route = respx.get(NOMINATIM_URL).mock(
            return_value=httpx.Response(200, json=[])
        )
        response = client.get("/api/segments/geocode", params={"query": ""})

        assert response.status_code == 200
        assert response.json() == {"results": []}
        # A blank query must short-circuit and never reach Nominatim.
        assert not route.called

    @respx.mock
    def test_geocode_no_match_returns_empty_results_not_404(
        self, client: TestClient
    ):
        respx.get(NOMINATIM_URL).mock(
            return_value=httpx.Response(200, json=[])
        )
        response = client.get(
            "/api/segments/geocode", params={"query": "zzz-nowhere-zzz"}
        )

        assert response.status_code == 200
        assert response.json() == {"results": []}

    @respx.mock
    def test_geocode_upstream_error_returns_empty_results(
        self, client: TestClient
    ):
        respx.get(NOMINATIM_URL).mock(return_value=httpx.Response(500))
        response = client.get(
            "/api/segments/geocode", params={"query": "err-town"}
        )

        # A Nominatim failure degrades gracefully to an empty list, never 5xx.
        assert response.status_code == 200
        assert response.json() == {"results": []}
