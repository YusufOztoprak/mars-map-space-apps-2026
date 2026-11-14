"""Flask API: POST /route -> GeoJSON LineString."""
from flask import Flask, request, jsonify
from flask_cors import CORS
import numpy as np

from dem_utils import generate_synthetic_dem, compute_slope
from routing import build_cost_grid, astar

app = Flask(__name__)
CORS(app)

# TODO: once Veri/Icerik delivers the real DEM, swap this block for:
#   from dem_utils import load_dem
#   elevation, transform, crs = load_dem("../data/jezero_dem.tif")
#   cellsize = transform.a
elevation, cellsize = generate_synthetic_dem(width=200, height=200)
slope_deg = compute_slope(elevation, cellsize)
cost_grid = build_cost_grid(slope_deg, cellsize)
GRID_HEIGHT, GRID_WIDTH = elevation.shape

# Placeholder DEM bounding box (Jezero HiRISE footprint) until the real
# GeoTIFF transform replaces this linear mapping.
LON_MIN, LON_MAX = 77.2229331, 77.583964
LAT_MIN, LAT_MAX = 18.3067994, 18.669315


def pixel_to_lonlat(row, col):
    lon = LON_MIN + (col / GRID_WIDTH) * (LON_MAX - LON_MIN)
    lat = LAT_MIN + (row / GRID_HEIGHT) * (LAT_MAX - LAT_MIN)
    return lon, lat


def lonlat_to_pixel(lat, lon):
    """Returns (row, col) or None if the point falls outside the DEM coverage."""
    if not (LON_MIN <= lon <= LON_MAX and LAT_MIN <= lat <= LAT_MAX):
        return None
    col = int((lon - LON_MIN) / (LON_MAX - LON_MIN) * GRID_WIDTH)
    row = int((lat - LAT_MIN) / (LAT_MAX - LAT_MIN) * GRID_HEIGHT)
    col = min(max(col, 0), GRID_WIDTH - 1)
    row = min(max(row, 0), GRID_HEIGHT - 1)
    return row, col


def path_stats(path):
    """Compute total distance (km), estimated time (hours), and max slope (deg) along a path."""
    distance_m = 0.0
    time_s = 0.0
    max_slope = 0.0
    for i in range(1, len(path)):
        r0, c0 = path[i - 1]
        r1, c1 = path[i]
        diag = 1.4142 if (r1 != r0 and c1 != c0) else 1.0
        distance_m += cellsize * diag
        time_s += cost_grid[r1, c1] * diag
        max_slope = max(max_slope, float(slope_deg[r1, c1]))
    return round(distance_m / 1000, 3), round(time_s / 3600, 3), round(max_slope, 1)


def parse_point(obj):
    """Extract (lat, lon) floats from a {'lat':..,'lon':..} or {'lat':..,'lng':..} dict."""
    lat = float(obj["lat"])
    lon_value = obj.get("lon", obj.get("lng"))
    lon = float(lon_value)
    return lat, lon


@app.route("/route", methods=["POST"])
def route():
    data = request.get_json(silent=True)
    if not data or "start" not in data or "end" not in data:
        return jsonify({"error": "istek gövdesi 'start' ve 'end' içermeli"}), 400

    try:
        start_lat, start_lon = parse_point(data["start"])
        end_lat, end_lon = parse_point(data["end"])
    except (KeyError, TypeError, ValueError):
        return jsonify({"error": "start/end {'lat': float, 'lon': float} formatında olmalı"}), 400

    start_rc = lonlat_to_pixel(start_lat, start_lon)
    end_rc = lonlat_to_pixel(end_lat, end_lon)
    if start_rc is None or end_rc is None:
        return jsonify({"error": "koordinat DEM kapsama alanının dışında"}), 422

    path = astar(cost_grid, start_rc, end_rc)
    if path is None:
        return jsonify({"error": "güvenli rota bulunamadı (çok dik arazi)"}), 422

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
    return jsonify({"status": "ok", "grid": [GRID_HEIGHT, GRID_WIDTH]})


if __name__ == "__main__":
    app.run(debug=True, port=5000)