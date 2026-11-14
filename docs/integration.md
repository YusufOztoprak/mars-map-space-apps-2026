# Backend Integration Guide — /route Endpoint

## Overview
Flask REST API for Mars surface walking-route computation (Jezero Crater pilot area). Takes two lat/lon points, returns a safety-aware GeoJSON route.

## Endpoint

POST /route

### Request
{
  "start": {"lat": 18.31, "lon": 77.23},
  "end": {"lat": 18.65, "lon": 77.57}
}

- Coordinates are lat/lon in degrees - exactly what Leaflet's click event gives you, no conversion needed on the frontend.
- Current DEM coverage (synthetic test data, same bounds as the real Jezero HiRISE DEM): lon 77.2229331-77.583964, lat 18.3067994-18.669315. Points outside this box return 422.

### Successful response - 200
{
  "type": "Feature",
  "geometry": {
    "type": "LineString",
    "coordinates": [[lon, lat], [lon, lat]]
  },
  "properties": {
    "distance_km": 7.009,
    "estimated_time_hours": 4.917,
    "max_slope_deg": 12.4
  }
}

- Coordinate order is [longitude, latitude] (GeoJSON standard).
- max_slope_deg never exceeds 28.0 - steeper cells are treated as impassable and excluded from the route.

### Error responses
| Status | Meaning |
|---|---|
| 400 | Missing/malformed body (missing start/end, non-numeric lat/lon) |
| 422 | Coordinates outside DEM coverage, or no safe route exists (all paths blocked by >28 deg terrain) |

Error message text is Turkish (internal); only the status code and JSON shape matter for integration.

## Health check
GET /health -> {"status": "ok", "grid": [height, width]}

## Running locally
cd backend
pip install -r requirements.txt
python app.py

Runs on http://localhost:5000. flask-cors is enabled for all origins (fine for a hackathon demo).

## Current data status
Using a synthetic (fake) DEM for now - not real Mars elevation yet. This is intentional, so frontend/integration work doesn't have to wait for the real GeoTIFF. Numbers like distance_km will look physically off until the swap happens.

Swap to the real DEM is a single change in app.py:
# before:
elevation, cellsize = generate_synthetic_dem(width=200, height=200)
# after:
elevation, transform, crs = load_dem("../data/jezero_dem.tif")
cellsize = transform.a

## Tests
backend/tests/test_route.py - 7 pytest cases (200/400/422 + GeoJSON structure/coordinate order).
cd backend
python -m pytest tests/ -v
