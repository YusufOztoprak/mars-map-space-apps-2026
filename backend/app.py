"""Flask API: POST /route -> GeoJSON LineString."""
import math
import os

import numpy as np
from flask import Flask, request, jsonify
from flask_cors import CORS
from rasterio.transform import rowcol, xy as transform_xy
from werkzeug.exceptions import HTTPException

from dem_utils import load_dem, terrain_metrics
from explorer import register_explorer
from routing import build_cost_grid, astar

app = Flask(__name__)
CORS(app, origins=["http://localhost:8000", "http://127.0.0.1:8000"])

# Real Jezero CTX DEM (20 m/pixel), USGS Mars 2020 Science Investigation CTX
# DEM Mosaic. Projection: equirectangular, Mars 2000 sphere (R=3396190 m),
# standard_parallel_1=18.4663 deg, central_meridian=0 deg (read from the
# GeoTIFF's own CRS via inspect_dem.py).
MARS_RADIUS_M = 3396190.0
STANDARD_PARALLEL_DEG = 18.4663
CENTRAL_MERIDIAN_DEG = 0.0

DEM_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "jezero_dem.tif")
elevation = transform = crs = nodata = slope_deg = roughness = cost_grid = None
cellsize, GRID_HEIGHT, GRID_WIDTH, H_SCALE = 20.0, 0, 0, 0.0
try:
    raw_elevation, transform, crs, nodata = load_dem(DEM_PATH)
    cellsize = transform.a
    elevation, slope_deg, roughness = terrain_metrics(raw_elevation, cellsize, nodata)
    del raw_elevation
    cost_grid = build_cost_grid(slope_deg, cellsize)
    GRID_HEIGHT, GRID_WIDTH = elevation.shape
    finite = cost_grid[np.isfinite(cost_grid)]
    if finite.size:
        H_SCALE = float(finite.min())
    del finite
except (OSError, RuntimeError, ValueError) as exc:
    app.logger.warning("Jezero CTX DEM unavailable: %s", exc)
# Longest straight-line distance we route in one request. A 21 km walk already
# takes ~14 h, so longer requests are not realistic single EVAs, and very long
# searches (~117 km) take over a minute and time out in the frontend.
MAX_ROUTE_KM = 30.0


def lonlat_to_xy(lon, lat):
    """Project geographic lon/lat (degrees) to the DEM's equirectangular x/y (meters)."""
    cos_std = math.cos(math.radians(STANDARD_PARALLEL_DEG))
    x = MARS_RADIUS_M * np.radians(lon - CENTRAL_MERIDIAN_DEG) * cos_std
    y = MARS_RADIUS_M * np.radians(lat)
    return x, y


def xy_to_lonlat(x, y):
    """Inverse of lonlat_to_xy."""
    cos_std = math.cos(math.radians(STANDARD_PARALLEL_DEG))
    lon = CENTRAL_MERIDIAN_DEG + np.degrees(x / (MARS_RADIUS_M * cos_std))
    lat = np.degrees(y / MARS_RADIUS_M)
    return lon, lat


def pixel_to_lonlat(row, col):
    x, y = transform_xy(transform, row, col)
    return xy_to_lonlat(x, y)


def lonlat_to_pixel(lat, lon):
    """Returns (row, col), or None if outside the DEM grid or on a nodata cell."""
    x, y = lonlat_to_xy(lon, lat)
    row, col = rowcol(transform, x, y)
    if not (0 <= row < GRID_HEIGHT and 0 <= col < GRID_WIDTH):
        return None
    if not np.isfinite(elevation[row, col]):
        return None
    return row, col

def surface_distance_km(lat1, lon1, lat2, lon2):
    """Great-circle distance on the Mars 2000 sphere (haversine), in km."""
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = p2 - p1
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * MARS_RADIUS_M * math.asin(math.sqrt(a)) / 1000

def path_stats(path):
    """Compute total distance (km), estimated time (hours), and max slope (deg) along a path.

    Zero-length steps (the repeated cell of a same-cell route) add no distance or time.
    """
    distance_m = 0.0
    time_s = 0.0
    max_slope = float(slope_deg[path[0]])
    for (r0, c0), (r1, c1) in zip(path, path[1:]):
        if (r0, c0) == (r1, c1):
            continue
        diag = 1.4142 if (r1 != r0 and c1 != c0) else 1.0
        distance_m += cellsize * diag
        time_s += cost_grid[r1, c1] * diag
        max_slope = max(max_slope, float(slope_deg[r1, c1]))
    return round(distance_m / 1000, 3), round(float(time_s) / 3600, 3), round(max_slope, 1)
def _as_number(value):
    """Accept only finite JSON numbers (rejects strings, booleans, NaN, inf)."""
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError("coordinate must be a finite JSON number")
    return float(value)


def parse_point(obj):
    """Extract (lat, lon) floats from a {'lat':..,'lon':..} or {'lat':..,'lng':..} dict."""
    lat = _as_number(obj["lat"])
    lon = _as_number(obj.get("lon", obj.get("lng")))
    return lat, lon


@app.route("/route", methods=["POST"])
def route():
    data = request.get_json(silent=True)
    if not isinstance(data, dict) or "start" not in data or "end" not in data:
        return jsonify({"error": "The request must include 'start' and 'end'."}), 400
    if cost_grid is None:
        return jsonify({"error": "Jezero elevation data are unavailable."}), 503

    try:
        start_lat, start_lon = parse_point(data["start"])
        end_lat, end_lon = parse_point(data["end"])
    except (KeyError, TypeError, ValueError):
        return jsonify({"error": "Start and end must contain numeric lat and lon values."}), 400

    start_rc = lonlat_to_pixel(start_lat, start_lon)
    end_rc = lonlat_to_pixel(end_lat, end_lon)
    if start_rc is None or end_rc is None:
        return jsonify({"error": "The coordinates fall outside valid elevation coverage."}), 422



    if surface_distance_km(start_lat, start_lon, end_lat, end_lon) > MAX_ROUTE_KM:
        return jsonify({"error": f"The endpoints are more than {MAX_ROUTE_KM:.0f} km apart. Choose points closer together."}), 422
    path = astar(cost_grid, start_rc, end_rc, h_scale=H_SCALE)
    if path is None:
        return jsonify({"error": "No candidate route meets the slope limit."}), 422

    if len(path) == 1:
        path = [path[0], path[0]]  # degenerate case: start and end in the same cell

    distance_km, estimated_time_hours, max_slope_deg = path_stats(path)
    coordinates = [list(pixel_to_lonlat(r, c)) for r, c in path]

    geojson = {
        "type": "Feature",
        "geometry": {"type": "LineString", "coordinates": coordinates},
        "properties": {
            "distance_km": distance_km,
            "estimated_time_hours": estimated_time_hours,
            "max_slope_deg": max_slope_deg,
        },
    }
    return jsonify(geojson)


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "grid": [GRID_HEIGHT, GRID_WIDTH], "ctx_available": cost_grid is not None})


@app.errorhandler(HTTPException)
def handle_http_exception(e):
    return jsonify({"error": e.description}), e.code


@app.errorhandler(Exception)
def handle_unexpected_error(e):
    app.logger.exception("Unexpected error")
    return jsonify({"error": "A server error occurred. Please try again."}), 500


register_explorer(app, {
    "height": elevation, "slope": slope_deg, "roughness": roughness,
    "transform": transform, "cellsize": cellsize,
    "to_xy": lonlat_to_xy, "to_lonlat": xy_to_lonlat,
})

if __name__ == "__main__":
    app.run(debug=False, port=int(os.environ.get("MARS_PORT", "5000")))
