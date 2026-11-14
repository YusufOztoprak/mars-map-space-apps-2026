"""Tests for the /route Flask endpoint using the synthetic DEM."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.get_json()["status"] == "ok"


def test_valid_route_returns_geojson(client):
    response = client.post("/route", json={
        "start": {"lat": 18.31, "lon": 77.23},
        "end": {"lat": 18.65, "lon": 77.57},
    })
    assert response.status_code == 200
    body = response.get_json()
    assert body["type"] == "Feature"
    assert body["geometry"]["type"] == "LineString"
    assert len(body["geometry"]["coordinates"]) >= 2
    assert "distance_km" in body["properties"]
    assert "estimated_time_hours" in body["properties"]
    assert body["properties"]["max_slope_deg"] <= 28.0  # safety threshold


def test_missing_end_returns_400(client):
    response = client.post("/route", json={"start": {"lat": 18.31, "lon": 77.23}})
    assert response.status_code == 400


def test_missing_body_returns_400(client):
    response = client.post("/route", json={})
    assert response.status_code == 400


def test_out_of_bounds_coordinate_returns_422(client):
    response = client.post("/route", json={
        "start": {"lat": 0, "lon": 0},
        "end": {"lat": 18.65, "lon": 77.57},
    })
    assert response.status_code == 422


def test_invalid_coordinate_type_returns_400(client):
    response = client.post("/route", json={
        "start": {"lat": "not-a-number", "lon": 77.23},
        "end": {"lat": 18.65, "lon": 77.57},
    })
    assert response.status_code == 400


def test_coordinate_order_in_geojson(client):
    """GeoJSON requires [longitude, latitude] order."""
    response = client.post("/route", json={
        "start": {"lat": 18.31, "lon": 77.23},
        "end": {"lat": 18.65, "lon": 77.57},
    })
    lon, lat = response.get_json()["geometry"]["coordinates"][0]
    assert 77.0 < lon < 78.0
    assert 18.0 < lat < 19.0