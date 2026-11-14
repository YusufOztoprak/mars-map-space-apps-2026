"""Time a few routes on the real DEM so the performance numbers can be reproduced.

Run from the backend/ folder:  python bench_routes.py
"""
import time

from app import app

ROUTES = {
    "~3 km": ((18.43, 77.38), (18.46, 77.42)),
    "~4 km, delta front": ((18.44, 77.42), (18.48, 77.37)),
    "~9.5 km": ((18.38, 77.33), (18.48, 77.45)),
    "~21 km": ((18.32, 77.25), (18.55, 77.50)),
}

client = app.test_client()
for name, ((lat1, lon1), (lat2, lon2)) in ROUTES.items():
    body = {"start": {"lat": lat1, "lon": lon1}, "end": {"lat": lat2, "lon": lon2}}
    t0 = time.perf_counter()
    response = client.post("/route", json=body)
    elapsed = time.perf_counter() - t0
    props = response.get_json().get("properties", {})
    print(f"{name:20s} HTTP {response.status_code}  {elapsed:6.2f} s  "
          f"{props.get('distance_km')} km, {props.get('estimated_time_hours')} h, "
          f"max slope {props.get('max_slope_deg')} deg")