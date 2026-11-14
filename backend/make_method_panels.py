"""Render the four 'elevation -> slope -> walking time -> route' panels for the slides
from the real DEM and the real router, so the method slide shows our own data.

Run from the backend/ folder:  python make_method_panels.py
Writes docs/figures/method_1_elevation.png ... method_4_route.png
"""
import os

import numpy as np
from PIL import Image, ImageDraw

import app
from routing import SAFETY_THRESHOLD_DEG, tobler_speed_kmh

START = (18.44, 77.42)   # crater floor (lat, lon) - same as the "delta front" benchmark route
END = (18.48, 77.37)     # top of the delta
MARGIN = 40              # cells (20 m each) around the route
SIZE = 900               # output panel size in pixels

out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "docs", "figures")
os.makedirs(out_dir, exist_ok=True)

start_rc = app.lonlat_to_pixel(*START)
end_rc = app.lonlat_to_pixel(*END)
path = app.astar(app.cost_grid, start_rc, end_rc, h_scale=app.H_SCALE)
assert path is not None, "no route found for the chosen points"

rows = [r for r, _ in path]
cols = [c for _, c in path]
r0, r1 = min(rows) - MARGIN, max(rows) + MARGIN
c0, c1 = min(cols) - MARGIN, max(cols) + MARGIN
side = max(r1 - r0, c1 - c0)                      # make the window square
r0, c0 = (r0 + r1 - side) // 2, (c0 + c1 - side) // 2
r0, c0 = max(r0, 0), max(c0, 0)
win = (slice(r0, r0 + side), slice(c0, c0 + side))

elev = app.elevation[win].copy()
slope = app.slope_deg[win]
valid = np.ones_like(elev, dtype=bool) if app.nodata is None else elev != app.nodata
elev[~valid] = np.nan

# Hillshade (light from the north-west) to give every panel the same terrain texture.
gy, gx = np.gradient(np.nan_to_num(elev, nan=np.nanmean(elev)), app.cellsize)
shade = np.clip(0.55 + (-gx + gy) * 0.8, 0, 1)


def to_img(rgb):
    img = Image.fromarray((np.clip(rgb, 0, 1) * 255).astype(np.uint8))
    return img.resize((SIZE, SIZE), Image.NEAREST)


def gradient(t, lo, hi):
    t = np.clip(np.nan_to_num(t), 0, 1)[..., None]
    return np.array(lo) * (1 - t) + np.array(hi) * t


# 1) Elevation: low = blue, high = sand, with hillshade
e = (elev - np.nanmin(elev)) / max(np.nanmax(elev) - np.nanmin(elev), 1e-9)
rgb1 = gradient(e, (0.10, 0.30, 0.42), (0.93, 0.84, 0.66)) * (0.6 + 0.4 * shade[..., None])
to_img(rgb1).save(os.path.join(out_dir, "method_1_elevation.png"))

# 2) Slope classes on grey hillshade (same colours as the hazard overlay)
grey = np.repeat((0.25 + 0.5 * shade)[..., None], 3, axis=2)
rgb2 = grey.copy()
for lo, hi, col in [(10, 15, (0.98, 0.80, 0.08)), (15, SAFETY_THRESHOLD_DEG, (0.98, 0.45, 0.09)),
                    (SAFETY_THRESHOLD_DEG, 90, (0.86, 0.15, 0.15))]:
    mask = valid & (slope >= lo) & (slope < hi if hi < 90 else True)
    rgb2[mask] = rgb2[mask] * 0.3 + np.array(col) * 0.7
to_img(rgb2).save(os.path.join(out_dir, "method_2_slope.png"))

# 3) Walking speed: fast = light teal, slow = dark, blocked = black
speed = tobler_speed_kmh(slope)
s = speed / tobler_speed_kmh(np.array(0.0))
rgb3 = gradient(s, (0.05, 0.20, 0.22), (0.62, 0.93, 0.90)) * (0.75 + 0.25 * shade[..., None])
rgb3[(slope > SAFETY_THRESHOLD_DEG) | ~valid] = 0
to_img(rgb3).save(os.path.join(out_dir, "method_3_walking_speed.png"))

# 4) Route on the slope panel
img4 = to_img(rgb2)
scale = SIZE / side
pts = [((c - c0 + 0.5) * scale, (r - r0 + 0.5) * scale) for r, c in path]
draw = ImageDraw.Draw(img4)
draw.line(pts, fill=(0, 43, 54), width=14, joint="curve")
draw.line(pts, fill=(0, 229, 255), width=7, joint="curve")
for (x, y), col in [(pts[0], (52, 211, 153)), (pts[-1], (239, 68, 68))]:
    draw.ellipse([x - 12, y - 12, x + 12, y + 12], fill=col, outline=(255, 255, 255), width=3)
img4.save(os.path.join(out_dir, "method_4_route.png"))

dist_km, hours, max_slope = app.path_stats(path)
print("window: %d x %d cells (%.1f km wide)" % (side, side, side * app.cellsize / 1000))
print("route: %.2f km, %.2f h, max slope %.1f deg" % (dist_km, hours, max_slope))
print("wrote 4 panels to docs/figures/")
