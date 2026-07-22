"""
Tests for the segments API routes with the Strava upstream mocked via respx.
"""
import httpx
import respx
from fastapi.testclient import TestClient

STRAVA_EXPLORE_URL = "https://www.strava.com/api/v3/segments/explore"
STRAVA_SEGMENT_URL = "https://www.strava.com/api/v3/segments/12345678"
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"

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
        assert (
            response.json()["detail"]
            == "Strava rate limit exceeded - try again later"
        )

    @respx.mock
    def test_strava_500_maps_to_api_502(self, client: TestClient, auth_headers: dict):
        respx.get(STRAVA_EXPLORE_URL).mock(
            return_value=httpx.Response(500, json={"message": "Server Error"})
        )
        response = client.post(
            "/api/segments/explore", json=EXPLORE_REQUEST, headers=auth_headers
        )
        assert response.status_code == 502


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
    """GET /api/segments/geocode (Nominatim upstream)"""

    @respx.mock
    def test_geocode_success(self, client: TestClient):
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
        assert data["latitude"] == 48.8566
        assert data["longitude"] == 2.3522
        assert "Paris" in data["display_name"]

    @respx.mock
    def test_geocode_not_found_returns_404(self, client: TestClient):
        respx.get(NOMINATIM_URL).mock(
            return_value=httpx.Response(200, json=[])
        )
        response = client.get(
            "/api/segments/geocode", params={"query": "zzz-nowhere-zzz"}
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "Location not found"
