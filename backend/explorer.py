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
CTX_SOURCE = {"id":"ctx", "name": "MRO / CTX · USGS Jezero", "url": CTX, "resolution_m": 20, "scope": "Jezero"}
HIRISE_SOURCE = {"id":"hirise", "name":"MRO / HiRISE · Jezero stereo DTM",
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
        return {"id":"mola", "name": f"MGS / MOLA MEGDR · {self.density} px/°", "url": MOLA,
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
        values = self.sample_global(key, lon, lat)
        for min_level, product in ((6,self.ctx),(11,self.hirise)):
            if product:
                local = self.sample_local(product, key, lon, lat)
                values = np.where(np.isfinite(local),local,values)
        return values

    def sample_model(self, key, lon, lat, level, model="auto"):
        if model == "auto":
            return self.sample(key,lon,lat,level)
        if model == "mola":
            return self.sample_global(key,lon,lat)
        return self.sample_local(self.ctx if model == "ctx" else self.hirise,key,lon,lat)

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
            continue  # Long journeys use the global grid instead of rejecting distance.
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
    density = terrain.density
    width = 360*density
    rs, cs = terrain.global_indexes(lx, ly, density)
    cs = [int(cs[0]), int(cs[0] + (cs[1]-cs[0]+width//2) % width - width//2)]
    r0, c0 = max(0, int(min(rs))-22), min(cs)-22
    r1, c1 = min(180*density, int(max(rs))+23), max(cs)+23
    stride=max(1,math.ceil(math.sqrt((r1-r0)*(c1-c0)/80_000)))
    while math.ceil((r1-r0)/stride)*math.ceil((c1-c0)/stride)>80_000:
        stride+=1
    shape=(math.ceil((r1-r0)/stride),math.ceil((c1-c0)/stride))

    def positions(rows, cols):
        return wrap((cols*stride+c0+.5)/density), 90-(rows*stride+r0+.5)/density

    r, c = np.mgrid[:shape[0], :shape[1]]
    lon, lat = positions(r, c)
    grids = {k: terrain.sample_global(k, lon, lat) for k in ("height", "slope", "roughness")}
    snapped=lambda row,col:(min(shape[0]-1,round((int(row)-r0)/stride)),
                            min(shape[1]-1,round((col-c0)/stride)))
    step=RADIUS*math.pi/(180*density)*stride
    source={**terrain.global_source,"routing_step_m":round(step),"sampling_stride":stride,
            "search_cells":shape[0]*shape[1]}
    return (grids,snapped(rs[0],cs[0]),snapped(rs[1],cs[1]),positions,step,source)


def candidate_routes(terrain, start, end, factors, coverage_factors):
    grids, s, e, positions, spacing, source = route_window(terrain, start, end)
    heights, slopes, rough = (grids[key] for key in ("height", "slope", "roughness"))
    blocked = ~np.isfinite(heights) | ~np.isfinite(slopes) | (slopes > SLOPE_LIMIT)
    rough_penalty = np.nan_to_num(rough / spacing, nan=0)
    profiles = {"shortest": (0, 0), "balanced": (1.8, 1.4), "terrain": (7, 5)}
    routes, same_paths = [], {}
    edge_distance=heuristic=None
    if source["scope"]=="Global Mars":
        # Longitude distances vary by row, especially on long/polar routes.
        # A single mean-latitude scale can choose the wrong distance-priority path.
        longitudes=np.radians(positions(np.zeros(heights.shape[1]),np.arange(heights.shape[1]))[0])
        latitudes=np.radians(positions(np.arange(heights.shape[0]),np.zeros(heights.shape[0]))[1])
        cosines=np.cos(latitudes)
        def edge_distance(r,c,nr,nc):
            a=math.sin((latitudes[nr]-latitudes[r])/2)**2+cosines[r]*cosines[nr]*math.sin((longitudes[nc]-longitudes[c])/2)**2
            return 2*RADIUS*math.asin(math.sqrt(min(1,max(0,a))))/spacing
        heuristic=lambda r,c:edge_distance(r,c,*e)
    for name, (slope_weight, rough_weight) in profiles.items():
        penalty = 1.0 + (slope_weight * (slopes / SLOPE_LIMIT)**2 if "slope" in factors else 0)
        if "roughness" in factors:
            penalty = penalty + rough_weight * rough_penalty
        grid = np.where(blocked, np.inf, np.ones_like(slopes) * penalty)
        cos_lat = max(.01, math.cos(math.radians((start[1]+end[1])/2))) if source != CTX_SOURCE else 1.0
        stride=source.get("sampling_stride",1)
        # Search sparsely on long journeys, then validate every intervening native
        # MOLA cell. Reject and reroute coarse edges that cross steep/nodata cells.
        for attempt in range(8):
            path = astar(grid, s, e, h_scale=1, weight=1.0 if name == "shortest" else 1.07,
                         max_expansions=grid.size+1 if source["scope"]=="Global Mars" else 235_000,
                         horizontal_scale=cos_lat,edge_distance=edge_distance,heuristic=heuristic)
            if not path or stride==1 or len(path)==1:
                break
            vertices=np.asarray(path,dtype=float)
            expanded=np.concatenate([a+(b-a)*np.arange(stride)[:,None]/stride
                                     for a,b in zip(vertices[:-1],vertices[1:])]+[vertices[-1:]])
            test_lon,test_lat=positions(expanded[:,0],expanded[:,1])
            checks={k:terrain.sample_global(k,test_lon,test_lat) for k in ("height","slope","roughness")}
            bad=~np.isfinite(checks["height"]) | ~np.isfinite(checks["slope"]) | (checks["slope"]>SLOPE_LIMIT)
            # Native diagonal moves must not cut across blocked adjacent cells.
            for dx,dy in ((1,0),(0,1)):
                side_lon,side_lat=positions(expanded[:-1,0]+dy*np.diff(expanded[:,0]),
                                            expanded[:-1,1]+dx*np.diff(expanded[:,1]))
                side=terrain.sample_global("slope",side_lon,side_lat)
                bad[1:] |= ~np.isfinite(side) | (side>SLOPE_LIMIT)
            if not bad.any():
                break
            for index in np.unique(np.minimum(np.flatnonzero(bad)//stride,len(path)-2)):
                target=path[index+1] if path[index+1]!=e else path[index]
                grid[target]=np.inf
            path=None
        if not path:
            continue
        key = tuple(path)
        if key in same_paths:
            same_paths[key]["profiles"].append(name)
            continue
        if len(path) == 1:
            path = [path[0], path[0]]
        rows, cols = np.asarray(path).T
        if stride>1 and len(set(path))>1:
            vertices=np.asarray(path,dtype=float)
            expanded=np.concatenate([a+(b-a)*np.arange(stride)[:,None]/stride
                                     for a,b in zip(vertices[:-1],vertices[1:])]+[vertices[-1:]])
            rows,cols=expanded.T
        lon, lat = positions(rows, cols)
        lon, lat = np.asarray(lon), np.asarray(lat)
        start_snap = arc_km([start[0],lon[0]],[start[1],lat[0]])[0]
        end_snap = arc_km([end[0],lon[-1]],[end[1],lat[-1]])[0]
        def connector(a,b):
            delta=wrap(b[0]-a[0])
            density=RADIUS*math.pi/180/source['resolution_m']
            count=max(1,math.ceil(max(abs(delta),abs(b[1]-a[1]))*density*2))
            fraction=np.linspace(0,1,count+1)
            return np.column_stack((wrap(a[0]+fraction*delta),a[1]+fraction*(b[1]-a[1])))
        if np.all(lon==lon[0]) and np.all(lat==lat[0]):
            connected=connector(start,end)
        else:
            connected=np.concatenate((connector(start,(lon[0],lat[0]))[:-1],
                np.column_stack((lon,lat)),connector((lon[-1],lat[-1]),end)[1:]))
        lon,lat=connected.T
        if source['id']=='mola':
            values={k:terrain.sample_global(k,lon,lat) for k in grids}
        else:
            product=terrain.hirise if source['id']=='hirise' else terrain.ctx
            values={k:terrain.sample_local(product,k,lon,lat) for k in grids}
        if not np.isfinite(values['height']).all() or not np.isfinite(values['slope']).all() or (values['slope']>SLOPE_LIMIT).any():
            continue
        length = arc_km(lon, lat)
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
                      "estimated_time_hours":round(float((build_cost_grid(values["slope"][1:],1) * length * 1000).sum())/3600, 2),
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
    limits=[]
    if terrain.density:
        values=terrain.globals[terrain.density]
        limits=[float(values.min()),float(values.max())]
    else:
        for product in (terrain.ctx,terrain.hirise):
            if product and product.get('height') is not None and np.isfinite(product['height']).any():
                limits.extend((float(np.nanmin(product['height'])),float(np.nanmax(product['height']))))
        limits=[min(limits),max(limits)] if limits else []
    schemes = {
        "height": ([-9000, -4500, 0, 4500, 10000, 22000],
                   [(45,49,123), (33,112,153), (59,154,136), (226,185,98), (190,87,51), (253,242,220)]),
        "slope": ([0, 5, 10, 15, 20, 30], [(35,81,88), (55,142,136), (234,201,82),
                                             (247,144,54), (233,75,59), (144,23,55)]),
        "roughness": ([0, .5, 2, 10, 200, 1500], [(25,54,81), (62,125,167), (91,205,186),
                                                   (231,206,118), (233,118,80), (253,230,200)])}
    if limits and limits[0]<limits[1]:
        levels=[limits[0],-4500,0,4500,10000,limits[1]] if terrain.density else np.linspace(*limits,6).tolist()
        schemes['height']=(levels,schemes['height'][1])

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
                        "imagery":json_data("imagery.json") or {"layers":[]},
                        "legends":{**{key:{"values":values,"colors":["#%02x%02x%02x" % tuple(c) for c in colors]}
                                   for key,(values,colors) in schemes.items()},
                                   **({"dust":json_data("dust-my34-sol400.json")["legend"]}
                                      if (json_data("dust-my34-sol400.json") or {}).get("legend") else {})},
                        "elevation_reference":"Meters relative to the Martian areoid; MOLA GMM3 degree/order 50 reference.",
                        "elevation_range_m":{"min":limits[0],"max":limits[1],"scope":"Loaded MOLA grid" if terrain.density else "Loaded local DEMs"} if limits else None,
                        "dust_available":(DATA / "dust-my34-sol400.png").is_file() and bool(json_data("dust-my34-sol400.json")),
                        "geology":{i: (DATA / f"{i}-geology.geojson").is_file() for i in ("global","jezero")},
                        "slope_limit":SLOPE_LIMIT, "caution_slope":CAUTION_SLOPE})

    @app.get("/api/explorer/point")
    def explorer_point():
        try:
            lon, lat = coordinates({k: float(request.args[k]) for k in ("lon", "lat")})
        except (KeyError, ValueError):
            return jsonify({"error":"Enter valid latitude and longitude."}), 400
        result = {}
        model=request.args.get("model","auto")
        if model not in {"auto","mola","ctx","hirise"}:
            return jsonify({"error":"Unknown terrain model."}),400
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
            if model != "auto":
                value=float(terrain.sample_model(key,lon_a,lat_a,17,model)[0])
                source={"ctx":CTX_SOURCE,"hirise":HIRISE_SOURCE,"mola":terrain.global_source if terrain.density else None}[model]
            result[key] = {"value": round(value, 2), "source": source} if math.isfinite(value) else None
        return jsonify({"lon":lon, "lat":lat, "terrain":result, "geology":geology_at(lon, lat),
                        "historical_dust":historical_dust(lon,lat),
                        "coverage":{**{k:{"status":"available" if v else "missing","source":v["source"] if v else None}
                                      for k,v in result.items()},
                                    "geology":{"status":"available" if geology_at(lon,lat) else "missing"},
                                    "radiation":{"status":"missing","detail":"No time-matched radiation measurement. Archived RAD data are local to Curiosity; missing is not zero dose."},
                                    "temperature":{"status":"missing","detail":"No time-matched air temperature measurement."},
                                    "thermal":{"status":"context_only","detail":"Colorized TES imagery has no calibrated numeric sampling in this app."},
                                    "dust":{"status":"historical_context" if historical_dust(lon,lat) else "missing"}}})

    @app.post("/api/explorer/heights")
    def explorer_heights():
        """Sample the center height of each archived rover vertex in one request."""
        points = request.get_json(silent=True)
        if not isinstance(points,list) or not 1 <= len(points) <= 100_000:
            return jsonify({"error":"Provide 1 to 100,000 coordinate pairs."}), 400
        if not all(isinstance(p,list) and len(p)==2 and all(
                isinstance(v,(int,float)) and not isinstance(v,bool) and math.isfinite(v) for v in p)
                   for p in points):
            return jsonify({"error":"Each point must contain two finite numeric coordinates."}),400
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
    def raster_tile(kind, z, x, y, model):
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
            values = terrain.sample_model("height" if kind == "relief" else kind, lon, lat, z,model)
            steps, colors = schemes["height" if kind == "relief" else kind]
            rgb = [np.interp(np.nan_to_num(values), steps, channel) for channel in zip(*colors)]
            if kind == "relief":
                # Sample a halo so neighboring tiles use identical edge derivatives.
                step=(np.arange(-1,257)+.5)/256
                hx,hy=np.meshgrid(360*(x+step)/2**(z+1)-180,90-180*(y+step)/2**z)
                heights=terrain.sample_model("height",wrap(hx),hy,z,model)
                dy,dx=np.gradient(heights)
                spacing=RADIUS*math.pi/(2**z*256)
                east=dx[1:-1,1:-1]/(spacing*np.maximum(.001,np.cos(np.radians(lat))))
                north=-dy[1:-1,1:-1]/spacing
                light=np.clip((.5*east-.5*north+math.sqrt(.5))/np.sqrt(1+east**2+north**2),0,1)
                shade=np.nan_to_num(.55+.45*light,nan=1)
                rgb=[channel*shade for channel in rgb]
            rgba = np.dstack((*rgb, np.isfinite(values)*255)).astype(np.uint8)
        out = io.BytesIO()
        Image.fromarray(rgba).save(out, format="PNG")
        return out.getvalue()

    @app.get("/api/explorer/raster/<kind>/<int:z>/<int:x>/<int:y>.png")
    def explorer_raster(kind, z, x, y):
        if kind not in (*schemes, "coverage", "relief") or z > 17:
            return ("", 404)
        model=request.args.get("model","auto")
        if model not in {"auto","mola","ctx","hirise"}:
            return jsonify({"error":"Unknown terrain model."}),400
        image = raster_tile(kind, z, x, y,model)
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
                        "slope_limit":SLOPE_LIMIT, "search_limit":source.get("search_cells",235_000),
                        "applied_factors": sorted(set(factors)),
                        "note":(f"No distance cap. MOLA search step ≈ {source.get('routing_step_m',source['resolution_m'])/1000:.1f} km; native cells along the returned path are checked. Regional planning only." if source["scope"] == "Global Mars"
                               else "This route uses approximately 1 m HiRISE stereo elevation samples." if source == HIRISE_SOURCE
                               else "The 20 m CTX grid cannot resolve small obstacles.")})
