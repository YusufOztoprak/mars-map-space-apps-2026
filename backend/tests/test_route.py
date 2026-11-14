"""Tests for the /route Flask endpoint against the real Jezero CTX DEM.

These tests need data/jezero_dem.tif (not in git; see README). They are
skipped when the file is missing, so a fresh clone still runs cleanly.
"""
import os
import sys

import pytest

BACKEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
DEM_PATH = os.path.join(BACKEND_DIR, "..", "data", "jezero_dem.tif")
if not os.path.exists(DEM_PATH):
    pytest.skip("real DEM not found at data/jezero_dem.tif", allow_module_level=True)

sys.path.insert(0, BACKEND_DIR)
from app import app  # noqa: E402
from routing import SAFETY_THRESHOLD_DEG  # noqa: E402

START = {"lat": 18.43, "lon": 77.38}
END = {"lat": 18.46, "lon": 77.42}
ONE_CELL_DEG = 0.001  # a 20 m cell is ~0.0004 deg; allow for snapping to the cell center


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def post_route(client, start, end):
    return client.post("/route", json={"start": start, "end": end})


def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.get_json()["status"] == "ok"


def test_valid_route(client):
    response = post_route(client, START, END)
    assert response.status_code == 200
    body = response.get_json()
    assert body["type"] == "Feature"
    assert body["geometry"]["type"] == "LineString"
    coords = body["geometry"]["coordinates"]
    assert len(coords) >= 2
    props = body["properties"]
    assert props["distance_km"] > 0
    assert props["estimated_time_hours"] > 0
    assert 0 <= props["max_slope_deg"] <= SAFETY_THRESHOLD_DEG


def test_route_ends_at_requested_points(client):
    coords = post_route(client, START, END).get_json()["geometry"]["coordinates"]
    (lon0, lat0), (lon1, lat1) = coords[0], coords[-1]
    assert abs(lon0 - START["lon"]) < ONE_CELL_DEG and abs(lat0 - START["lat"]) < ONE_CELL_DEG
    assert abs(lon1 - END["lon"]) < ONE_CELL_DEG and abs(lat1 - END["lat"]) < ONE_CELL_DEG


def test_same_cell_route_has_zero_length(client):
    response = post_route(client, START, START)
    assert response.status_code == 200
    body = response.get_json()
    assert len(body["geometry"]["coordinates"]) == 2
    assert body["properties"]["distance_km"] == 0
    assert body["properties"]["estimated_time_hours"] == 0


def test_lng_alias_accepted(client):
    start = {"lat": START["lat"], "lng": START["lon"]}
    end = {"lat": END["lat"], "lng": END["lon"]}
    assert post_route(client, start, end).status_code == 200


def test_missing_end_returns_400(client):
    assert client.post("/route", json={"start": START}).status_code == 400


def test_missing_body_returns_400(client):
    assert client.post("/route", json={}).status_code == 400


def test_string_coordinates_return_400(client):
    assert post_route(client, {"lat": "18.43", "lon": 77.38}, END).status_code == 400


def test_out_of_bounds_returns_422(client):
    assert post_route(client, {"lat": 0, "lon": 0}, END).status_code == 422


def test_cors_allows_demo_origin_only(client):
    preflight = {"Access-Control-Request-Method": "POST"}
    ok = client.options("/route", headers={"Origin": "http://localhost:8000", **preflight})
    assert ok.headers.get("Access-Control-Allow-Origin") == "http://localhost:8000"
    other = client.options("/route", headers={"Origin": "https://example.com", **preflight})
    assert "Access-Control-Allow-Origin" not in other.headers



def test_too_far_returns_422_quickly(client, monkeypatch):
    import app as backend_app
    monkeypatch.setattr(backend_app, "MAX_ROUTE_KM", 1.0)  # START-END is ~5 km apart
    response = post_route(client, START, END)
    assert response.status_code == 422
    assert "error" in response.get_json()


def test_surface_distance_one_degree_latitude():
    import app as backend_app
    km = backend_app.surface_distance_km(18.0, 77.0, 19.0, 77.0)
    assert abs(km - 59.27) < 0.05  # 1 deg of latitude on Mars (R = 3396.19 km)