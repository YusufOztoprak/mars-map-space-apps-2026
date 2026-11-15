"""Planetary data and candidate routes for the 3D explorer."""

import io
import json
import math
import re
from functools import lru_cache
from pathlib import Path

import numpy as np
from flask import jsonify, redirect, request, send_file, send_from_directory
from PIL import Image
import rasterio

from dem_utils import terrain_metrics
from routing import astar, build_cost_grid

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "explorer"
RADIUS = 3_396_190.0
CTX = "https://astrogeology.usgs.gov/search/map/mars_2020_science_investigation_ctx_dem_mosaic"
MOLA = "https://pds-geosciences.wustl.edu/missions/mgs/megdr.html"
LOCAL_GEOLOGY = "https://pubs.usgs.gov/publication/sim3464"
GLOBAL_GEOLOGY = "https://pubs.usgs.gov/publication/sim3292"
CTX_SOURCE = {"name": "MRO / CTX · USGS Jezero", "url": CTX, "resolution_m": 20, "scope": "Jezero"}
HIRISE_SOURCE = {"name":"MRO / HiRISE · Jezero stereo DTM",
                 "url":"https://hirise.lpl.arizona.edu/dtm/PSP_002387_1985",
                 "resolution_m":1.02, "scope":"Jezero · HiRISE"}
TERRAIN_FACTORS = {"slope", "roughness"}
CONTEXT_FACTORS = {"geology", "thermal", "temperature", "dust", "radiation"}
SLOPE_LIMIT = 20.0
CAUTION_SLOPE = 15.0


def wrap(lon):
    return (lon + 180) % 360 - 180


def arc_km(lon, lat):
    p = np.radians(lat)
    a = np.sin(np.diff(p) / 2) ** 2 + np.cos(p[:-1]) * np.cos(p[1:]) * np.sin(np.radians(np.diff(lon)) / 2) ** 2
    return 2 * RADIUS / 1000 * np.arcsin(np.sqrt(np.clip(a, 0, 1)))


def coordinates(data):
    if not isinstance(data, dict):
        raise ValueError("Latitude and longitude are required.")
    try:
        lon, lat = data["lon"], data["lat"]
        if any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) for v in (lon, lat)):
            raise ValueError
        if not -90 <= lat <= 90 or not -360 <= lon <= 360:
            raise ValueError
    except (KeyError, ValueError):
        raise ValueError("Latitude must be between −90 and 90, and longitude between −360 and 360.") from None
    return wrap(lon), lat


class Terrain:
    def __init__(self, ctx):
        self.ctx = ctx
        self.hirise = None
        path = DATA / "hirise-jezero.tif"
        if path.is_file():
            try:
                with rasterio.open(path) as image:
                    projection = image.crs.to_dict()
                    if projection.get("proj") == "eqc" and projection.get("R") == RADIUS and all(
                        projection.get(k,0) == 0 for k in ("lon_0","lat_ts","lat_0","x_0","y_0")
                    ):
                        center_lat = (image.bounds.top+image.bounds.bottom)/(2*RADIUS)
                        h,s,r = terrain_metrics(image.read(1), image.res[1], image.nodata,
                                                image.res[0]*math.cos(center_lat))
                        self.hirise = {"height":h,"slope":s,"roughness":r,"transform":image.transform,
                                       "cellsize":image.res[0],
                                       "to_xy":lambda lon,lat:(RADIUS*np.radians(lon),RADIUS*np.radians(lat)),
                                       "to_lonlat":lambda x,y:(np.degrees(x/RADIUS),np.degrees(y/RADIUS))}
            except (OSError,ValueError,rasterio.errors.RasterioError):
                pass
        self.globals = {}
        for name, density in (("mola16", 16), ("mola", 4)):
            path = DATA / f"{name}.img"
            if path.is_file() and path.stat().st_size == (180 * density) * (360 * density) * 2:
                self.globals[density] = np.memmap(path, dtype=">i2", mode="r", shape=(180 * density, 360 * density))
        self.density = max(self.globals, default=0)

    @property
    def global_source(self):
        return {"name": f"MGS / MOLA MEGDR · {self.density} px/°", "url": MOLA,
                "resolution_m": round(RADIUS * math.pi / 180 / self.density), "scope": "Global Mars"}

    @staticmethod
    def indexes(product, lon, lat):
        x, y = product["to_xy"](lon, lat)
        tr = product["transform"]
        return np.floor((y-tr.f)/tr.e).astype(int), np.floor((x-tr.c)/tr.a).astype(int)

    def sample_local(self, product, key, lon, lat):
        values = np.full(np.shape(lon), np.nan, dtype=np.float32)
        array = product[key] if product else None
        if array is not None:
            row, col = self.indexes(product, lon, lat)
            inside = (row >= 0) & (row < array.shape[0]) & (col >= 0) & (col < array.shape[1])
            values[inside] = array[row[inside], col[inside]]
        return values

    def global_indexes(self, lon, lat, density):
        a = self.globals[density]
        return (np.clip(np.floor((90 - np.asarray(lat)) * density).astype(int), 0, a.shape[0] - 1),
                np.floor(np.asarray(lon) * density).astype(int) % a.shape[1])

    def sample_global(self, key, lon, lat, density=None):
        density = self.density if density is None else density
        if density not in self.globals:
            return np.full(np.shape(lon), np.nan, dtype=np.float32)
        a = self.globals[density]
        r, c = self.global_indexes(lon, lat, density)
        at = lambda y, x: np.asarray(a[np.clip(y, 0, a.shape[0]-1), x % a.shape[1]], dtype=np.float32)
        h = at(r, c)
        if key == "height":
            return h
        west, east, north, south = at(r, c-1), at(r, c+1), at(r-1, c), at(r+1, c)
        if key == "roughness":
            return np.abs(h - (west + east + north + south) / 4)
        spacing = RADIUS * math.pi / (180 * density)
        dx = (east - west) / (2 * spacing * np.cos(np.radians(90 - (r+.5)/density)))
        return np.degrees(np.arctan(np.hypot(dx, (south - north) / (2 * spacing))))

    def sample(self, key, lon, lat, level):
        values = self.sample_global(key, lon, lat, density=4 if level < 4 and 4 in self.globals else self.density)
        for min_level, product in ((6,self.ctx),(11,self.hirise)):
            if product and level >= min_level:
                local = self.sample_local(product, key, lon, lat)
                values = np.where(np.isfinite(local),local,values)
        return values

    @staticmethod
    def bounds(product):
        if not product or product["height"] is None:
            return None
        tr = product["transform"]
        rows, cols = product["height"].shape
        west, north = product["to_lonlat"](tr.c, tr.f)
        east, south = product["to_lonlat"](tr.c + cols*tr.a, tr.f + rows*tr.e)
        return [west, south, east, north]


@lru_cache(maxsize=8)
def json_data(filename):
    try:
        return json.loads((DATA / filename).read_text(encoding="utf8"))
    except (OSError, ValueError):
        return None


def in_ring(ring, lon, lat):
    inside = False
    previous = ring[-1]
    for current in ring:
        x, y = current[:2]
        px, py = previous[:2]
        if (y > lat) != (py > lat) and lon < (px-x)*(lat-y)/(py-y)+x:
            inside = not inside
        previous = current
    return inside


@lru_cache(maxsize=2)
def geology_index(name):
    data = json_data(name)
    index = []
    for feature in (data or {}).get("features", []):
        geometry = feature["geometry"]
        if not geometry:
            continue
        polygons = geometry["coordinates"] if geometry["type"] == "MultiPolygon" else [geometry["coordinates"]]
        for rings in polygons:
            if not rings or not rings[0]:
                continue
            xy = np.asarray(rings[0])
            index.append((xy[:, 0].min(), xy[:, 1].min(), xy[:, 0].max(), xy[:, 1].max(),
                          rings, feature["properties"]))
    return index


def geology_at(lon, lat):
    for name, url, scale in (("jezero-geology.geojson", LOCAL_GEOLOGY, "1:75,000"),
                             ("global-geology.geojson", GLOBAL_GEOLOGY, "1:20,000,000")):
        for west, south, east, north, rings, properties in geology_index(name):
            if west <= lon <= east and south <= lat <= north and in_ring(rings[0], lon, lat):
                if not any(in_ring(hole, lon, lat) for hole in rings[1:]):
                    return {**properties, "url": url, "scale": scale}
    return None


def historical_dust(lon, lat):
    product = json_data("dust-my34-sol400.json")
    if not product:
        return None
    row = min(59, max(0, int((90-lat)//3)))
    col = math.floor((lon+181.5)/3) % 120
    number = product["values"][row][col]
    if number is None:
        return None
    return {"value": number, "year": product["year"], "sol": product["sol"],
            "ls": product["ls"], "url": product["url"], "kind": "historical_model"}


def summarize_coverage(lon, lat, factors, metrics):
    """Evaluate actual grid samples; environmental point records have no corridor footprint."""
    entries, gaps = {}, {}
    for factor in sorted(factors):
        if factor in metrics:
            known = np.isfinite(metrics[factor])
            detail = "Digital terrain data are checked at each route sample."
        elif factor == "geology":
            known = np.array([geology_at(float(x), float(y)) is not None for x, y in zip(lon, lat)])
            detail = "Published geologic unit boundaries. Ground strength is outside the scope of this analysis."
        elif factor == "thermal":
            known = np.zeros(len(lon), dtype=bool)
            detail = "Infrared imagery and thermal inertia provide context. Temperature time series are unavailable along this route."
        elif factor == "dust":
            known = np.zeros(len(lon), dtype=bool)
            detail = "The MY34 Sol 400 dust model provides historical context. Dust observations for the route time are unavailable."
        else:
            known = np.zeros(len(lon), dtype=bool)
            detail = "No measurements match the locations and timing of the selected route."
        entries[factor] = {"percent": round(100 * float(np.mean(known)), 1), "detail": detail,
                           "status": "available" if known.all() else "partial" if known.any() else "missing"}
        missing = np.flatnonzero(~known)
        if missing.size:
            groups = np.split(missing, np.flatnonzero(np.diff(missing) > 1) + 1)
            gaps[factor] = [[int(g[0]), int(g[-1])] for g in groups]
    return entries, gaps


def route_window(terrain, start, end):
    lx, ly = np.asarray([start[0], end[0]]), np.asarray([start[1], end[1]])
    for product, source in ((terrain.hirise,HIRISE_SOURCE),(terrain.ctx,CTX_SOURCE)):
        if not np.isfinite(terrain.sample_local(product, "height", lx, ly)).all():
            continue
        grid = product["height"]
        sr, sc = map(int, terrain.indexes(product, *start))
        er, ec = map(int, terrain.indexes(product, *end))
        separation = float(arc_km(lx, ly)[0])
        if separation > 30:
            raise ValueError("Jezero route endpoints must be within 30 km of each other.")
        margin = min(270, max(75, int(math.hypot(er-sr, ec-sc) * .22)))
        r0, c0 = max(0, min(sr, er)-margin), max(0, min(sc, ec)-margin)
        r1, c1 = min(grid.shape[0], max(sr, er)+margin+1), min(grid.shape[1], max(sc, ec)+margin+1)
        window = (slice(r0, r1), slice(c0, c1))
        tr = product["transform"]

        def positions(rows, cols):
            return product["to_lonlat"](tr.c + tr.a*(cols+c0+.5), tr.f + tr.e*(rows+r0+.5))

        return ({k: product[k][window] for k in ("height", "slope", "roughness")},
                (sr-r0, sc-c0), (er-r0, ec-c0), positions, product["cellsize"], source)
    if not terrain.density:
        raise ValueError("No common elevation grid covers both endpoints.")
    if max(abs(start[1]), abs(end[1])) > 87 or arc_km(lx, ly)[0] > 1200:
        raise ValueError("MOLA regional planning supports latitudes within ±87° and endpoints up to 1,200 km apart.")
    density = terrain.density
    width = 360*density
    rs, cs = terrain.global_indexes(lx, ly, density)
    cs = [int(cs[0]), int(cs[0] + (cs[1]-cs[0]+width//2) % width - width//2)]
    r0, c0 = max(0, int(min(rs))-22), min(cs)-22
    r1, c1 = min(180*density, int(max(rs))+23), max(cs)+23
    if (r1-r0)*(c1-c0) > 800_000:
        raise ValueError("The MOLA search area is too large. Choose closer waypoints.")

    def positions(rows, cols):
        return wrap((cols+c0+.5)/density), 90-(rows+r0+.5)/density

    r, c = np.mgrid[:r1-r0, :c1-c0]
    lon, lat = positions(r, c)
    grids = {k: terrain.sample_global(k, lon, lat) for k in ("height", "slope", "roughness")}
    return (grids, (int(rs[0])-r0, cs[0]-c0), (int(rs[1])-r0, cs[1]-c0), positions,
            RADIUS*math.pi/(180*density), terrain.global_source)


def candidate_routes(terrain, start, end, factors, coverage_factors):
    grids, s, e, positions, spacing, source = route_window(terrain, start, end)
    heights, slopes, rough = (grids[key] for key in ("height", "slope", "roughness"))
    blocked = ~np.isfinite(heights) | ~np.isfinite(slopes) | (slopes > SLOPE_LIMIT)
    rough_penalty = np.nan_to_num(rough / spacing, nan=0)
    base_time = build_cost_grid(slopes, spacing)
    profiles = {"shortest": (0, 0), "balanced": (1.8, 1.4), "terrain": (7, 5)}
    routes, same_paths = [], {}
    for name, (slope_weight, rough_weight) in profiles.items():
        penalty = 1.0 + (slope_weight * (slopes / SLOPE_LIMIT)**2 if "slope" in factors else 0)
        if "roughness" in factors:
            penalty = penalty + rough_weight * rough_penalty
        grid = np.where(blocked, np.inf, np.ones_like(slopes) * penalty)
        cos_lat = max(.01, math.cos(math.radians((start[1]+end[1])/2))) if source != CTX_SOURCE else 1.0
        path = astar(grid, s, e, h_scale=1, weight=1.0 if name == "shortest" else 1.07,
                     max_expansions=235_000, horizontal_scale=cos_lat)
        if not path:
            continue
        key = tuple(path)
        if key in same_paths:
            same_paths[key]["profiles"].append(name)
            continue
        if len(path) == 1:
            path = [path[0], path[0]]
        rows, cols = np.asarray(path).T
        lon, lat = positions(rows, cols)
        lon, lat = np.asarray(lon), np.asarray(lat)
        values = {k: v[rows, cols] for k, v in grids.items()}
        length = arc_km(lon, lat)
        start_snap = arc_km([start[0],lon[0]],[start[1],lat[0]])[0]
        end_snap = arc_km([end[0],lon[-1]],[end[1],lat[-1]])[0]
        height_steps = np.diff(values["height"])
        steepness = values["slope"]
        steep = np.flatnonzero(steepness >= CAUTION_SLOPE)
        groups = np.split(steep, np.flatnonzero(np.diff(steep)>1)+1) if steep.size else []
        hazards = [{"from": int(g[0]), "to": int(g[-1]), "at": int(g[np.argmax(steepness[g])]),
                    "type": "slope", "value": round(float(steepness[g].max()), 1), "unit": "°",
                    "threshold": CAUTION_SLOPE,
                    "detail": "The slope in this section approaches the prototype limit."} for g in groups]
        coverage, gaps = summarize_coverage(lon, lat, coverage_factors | {"height", "slope"}, values)
        feature = {"type":"Feature", "geometry":{"type":"LineString",
                    "coordinates": np.round(np.column_stack((lon, lat)), 7).tolist()},
                   "properties":{"profiles":[name], "distance_km":round(float(length.sum()), 3),
                      "start_snap_m":round(float(start_snap)*1000), "end_snap_m":round(float(end_snap)*1000),
                      "ascent_m":round(float(np.maximum(height_steps,0).sum()), 1),
                      "descent_m":round(float(np.maximum(-height_steps,0).sum()), 1),
                      "estimated_time_hours":round(float((base_time[rows[1:], cols[1:]] / spacing * length * 1000).sum())/3600, 2),
                      "max_slope_deg":round(float(steepness.max()), 1),
                      "mean_slope_deg":round(float(steepness.mean()), 1),
                      "mean_roughness_m":round(float(values["roughness"][np.isfinite(values["roughness"])].mean()), 2)
                          if np.isfinite(values["roughness"]).any() else None,
                      "hazards":hazards, "coverage":coverage, "gaps":gaps, "source":source,
                      "elevations_m":np.round(values["height"],2).astype(float).tolist()}}
        routes.append(feature)
        same_paths[key] = feature["properties"]
    return routes, source


def register_explorer(app, ctx):
    terrain = Terrain(ctx)
    schemes = {
        "height": ([-9000, -4500, 0, 4500, 10000, 22000],
                   [(45,49,123), (33,112,153), (59,154,136), (226,185,98), (190,87,51), (253,242,220)]),
        "slope": ([0, 5, 10, 15, 20, 30], [(35,81,88), (55,142,136), (234,201,82),
                                             (247,144,54), (233,75,59), (144,23,55)]),
        "roughness": ([0, .5, 2, 10, 200, 1500], [(25,54,81), (62,125,167), (91,205,186),
                                                   (231,206,118), (233,118,80), (253,230,200)])}

    @app.get("/")
    def explorer_home():
        return redirect("/frontend/index.html")

    @app.get("/frontend/<path:name>")
    def explorer_frontend(name):
        return send_from_directory(ROOT / "frontend", name)

    @app.get("/data/science_points.json")
    def explorer_science():
        return send_from_directory(ROOT / "data", "science_points.json")

    @app.get("/data/explorer/<path:name>")
    def explorer_data(name):
        if not re.fullmatch(r"(?:viking/[01]\.jpg|dust-my34-sol400\.png|[\w-]+\.(?:geojson|json))", name):
            return jsonify({"error":"Data product not found."}), 404
        return send_from_directory(DATA, name)

    @app.get("/api/explorer/meta")
    def explorer_meta():
        ctx_bounds = terrain.bounds(terrain.ctx)
        return jsonify({"ctx_bounds": ctx_bounds, "ctx": CTX_SOURCE if ctx_bounds else None,
                        "hirise_bounds":terrain.bounds(terrain.hirise), "hirise":HIRISE_SOURCE if terrain.hirise else None,
                        "global_dem": terrain.global_source if terrain.density else None,
                        "observations":json_data("observations.json") or [],
                        "dust_available":(DATA / "dust-my34-sol400.png").is_file(),
                        "geology":{i: (DATA / f"{i}-geology.geojson").is_file() for i in ("global","jezero")},
                        "slope_limit":SLOPE_LIMIT, "caution_slope":CAUTION_SLOPE})

    @app.get("/api/explorer/point")
    def explorer_point():
        try:
            lon, lat = coordinates({k: float(request.args[k]) for k in ("lon", "lat")})
        except (KeyError, ValueError):
            return jsonify({"error":"Enter valid latitude and longitude."}), 400
        result = {}
        for key in ("height", "slope", "roughness"):
            lon_a, lat_a = np.array([lon]), np.array([lat])
            value = float(terrain.sample_local(terrain.hirise, key, lon_a, lat_a)[0])
            source = HIRISE_SOURCE
            if not math.isfinite(value):
                value = float(terrain.sample_local(terrain.ctx, key, lon_a, lat_a)[0])
                source = CTX_SOURCE
            if not math.isfinite(value):
                value = float(terrain.sample_global(key, lon_a, lat_a)[0])
                source = terrain.global_source if terrain.density else None
            result[key] = {"value": round(value, 2), "source": source} if math.isfinite(value) else None
        return jsonify({"lon":lon, "lat":lat, "terrain":result, "geology":geology_at(lon, lat),
                        "historical_dust":historical_dust(lon,lat)})

    @app.post("/api/explorer/heights")
    def explorer_heights():
        """Sample the center height of each archived rover vertex in one request."""
        points = request.get_json(silent=True)
        if not isinstance(points,list) or not 1 <= len(points) <= 100_000:
            return jsonify({"error":"Provide 1 to 100,000 coordinate pairs."}), 400
        try:
            lon, lat = np.asarray(points, dtype=float).T
            if not np.isfinite(lon).all() or not np.isfinite(lat).all() or np.any(np.abs(lat)>90):
                raise ValueError
        except (ValueError,TypeError):
            return jsonify({"error":"Longitude and latitude pairs are required."}), 400
        values = terrain.sample("height", wrap(lon), lat, 12)
        return jsonify([round(float(h),2) if np.isfinite(h) else None for h in values])

    def tile_coords(z, x, y, size, edge=False):
        nx, ny = 2**(z+1), 2**z
        if z > 17 or x >= nx or y >= ny:
            return None
        step = np.linspace(0, 1, size) if edge else (np.arange(size)+.5)/size
        return np.meshgrid(360*(x+step)/nx-180, 90-180*(y+step)/ny)

    @lru_cache(maxsize=96)
    def raster_tile(kind, z, x, y):
        coords = tile_coords(z, x, y, 256)
        if coords is None:
            return None
        lon, lat = coords
        if kind == "coverage":
            valid = np.isfinite(terrain.sample_local(terrain.ctx, "height", lon, lat))
            fine = np.isfinite(terrain.sample_local(terrain.hirise, "height", lon, lat))
            rgba = np.zeros((*valid.shape, 4), dtype=np.uint8)
            rgba[valid] = (47,216,197,180)
            rgba[fine] = (188,150,246,205)
        else:
            values = terrain.sample(kind, lon, lat, z)
            steps, colors = schemes[kind]
            rgb = [np.interp(np.nan_to_num(values), steps, channel) for channel in zip(*colors)]
            rgba = np.dstack((*rgb, np.isfinite(values)*255)).astype(np.uint8)
        out = io.BytesIO()
        Image.fromarray(rgba).save(out, format="PNG")
        return out.getvalue()

    @app.get("/api/explorer/raster/<kind>/<int:z>/<int:x>/<int:y>.png")
    def explorer_raster(kind, z, x, y):
        if kind not in (*schemes, "coverage") or z > 17:
            return ("", 404)
        image = raster_tile(kind, z, x, y)
        return send_file(io.BytesIO(image), mimetype="image/png", max_age=3600) if image else ("", 404)

    @lru_cache(maxsize=192)
    def height_tile(z, x, y):
        coords = tile_coords(z, x, y, 33, edge=True)
        if coords is None:
            return None
        lon, lat = coords
        values = terrain.sample("height", lon, lat, z)
        return np.nan_to_num(values, nan=0).astype("<f4").tobytes()

    @app.get("/api/explorer/terrain/<int:z>/<int:x>/<int:y>.bin")
    def explorer_height(z, x, y):
        binary = height_tile(z, x, y) if z <= 17 else None
        return send_file(io.BytesIO(binary), mimetype="application/octet-stream", max_age=3600) if binary else ("", 404)

    @app.post("/api/explorer/routes")
    def explorer_routes():
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            return jsonify({"error":"Send the route request as JSON."}), 400
        try:
            start, end = coordinates(data.get("start")), coordinates(data.get("end"))
            factors, coverage = data.get("factors", ["slope", "roughness"]), data.get("coverage", [])
            if not isinstance(factors, list) or not all(isinstance(k, str) and k in TERRAIN_FACTORS for k in factors):
                raise ValueError("The supported routing factors are slope and roughness.")
            if not isinstance(coverage, list) or not all(isinstance(k, str) and k in TERRAIN_FACTORS | CONTEXT_FACTORS | {"height"} for k in coverage):
                raise ValueError("The data coverage options are invalid.")
        except ValueError as exc:
            return jsonify({"error":str(exc)}), 400
        try:
            entries, source = candidate_routes(terrain, start, end, set(factors), set(coverage) | set(factors))
        except ValueError as exc:
            return jsonify({"error":str(exc)}), 422
        if not entries:
            return jsonify({"error":"No candidate route was found within the search area and slope limit.", "source":source}), 422
        return jsonify({"type":"FeatureCollection", "features":entries, "source":source,
                        "slope_limit":SLOPE_LIMIT, "search_limit":235_000,
                        "applied_factors": sorted(set(factors)),
                        "note":("MOLA results are suitable for regional planning." if source["scope"] == "Global Mars"
                               else "This route uses approximately 1 m HiRISE stereo elevation samples." if source == HIRISE_SOURCE
                               else "The 20 m CTX grid cannot resolve small obstacles.")})
