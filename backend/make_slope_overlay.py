"""Generate a slope-hazard overlay PNG for the frontend from the routing DEM.

Run from the backend/ folder:  python make_slope_overlay.py
Writes frontend/slope_overlay.png and frontend/slope_overlay.json (lat/lon bounds).
Colors come from the same slope grid and slope limit the router uses.
"""
import json
import os

import numpy as np
from PIL import Image
from rasterio.transform import rowcol

from app import slope_deg, elevation, nodata, transform, lonlat_to_xy, xy_to_lonlat
from routing import SAFETY_THRESHOLD_DEG

# Crop to the HiRISE Jezero footprint the map is centered on.
LON_MIN, LON_MAX = 77.2229, 77.5840
LAT_MIN, LAT_MAX = 18.3068, 18.6693

r_top, c_left = (int(v) for v in rowcol(transform, *lonlat_to_xy(LON_MIN, LAT_MAX)))
r_bottom, c_right = (int(v) for v in rowcol(transform, *lonlat_to_xy(LON_MAX, LAT_MIN)))
window = (slice(r_top, r_bottom + 1), slice(c_left, c_right + 1))
slope = slope_deg[window]
valid = np.ones(slope.shape, dtype=bool) if nodata is None else elevation[window] != nodata

# RGBA classes: easy (transparent), moderate (yellow), steep (orange), blocked (red).
rgba = np.zeros(slope.shape + (4,), dtype=np.uint8)
rgba[valid & (slope >= 10) & (slope < 15)] = (250, 204, 21, 110)
rgba[valid & (slope >= 15) & (slope <= SAFETY_THRESHOLD_DEG)] = (249, 115, 22, 150)
rgba[valid & (slope > SAFETY_THRESHOLD_DEG)] = (220, 38, 38, 190)

out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "frontend")
Image.fromarray(rgba).save(os.path.join(out_dir, "slope_overlay.png"), optimize=True)

# Outer pixel edges, as Leaflet bounds [[south, west], [north, east]].
west, north = xy_to_lonlat(transform.c + c_left * transform.a, transform.f + r_top * transform.e)
east, south = xy_to_lonlat(transform.c + (c_right + 1) * transform.a, transform.f + (r_bottom + 1) * transform.e)
meta = {
    "bounds": [[south, west], [north, east]],
    "slope_limit_deg": SAFETY_THRESHOLD_DEG,
    "source": "USGS Mars 2020 CTX DEM mosaic, 20 m/pixel",
}
with open(os.path.join(out_dir, "slope_overlay.json"), "w") as f:
    json.dump(meta, f, indent=2)

print("Overlay size:", slope.shape[1], "x", slope.shape[0], "px")
print("Bounds:", meta["bounds"])
print("Share of cells over the limit: %.1f%%" % (100 * np.mean(slope[valid] > SAFETY_THRESHOLD_DEG)))