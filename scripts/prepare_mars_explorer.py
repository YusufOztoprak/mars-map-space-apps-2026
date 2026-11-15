"""Build compact browser products from the downloaded source archives."""
import csv
import json
import math
import re
from pathlib import Path

import geopandas as gpd
import numpy as np
from PIL import Image
from pyproj import CRS

project = Path(__file__).resolve().parents[1]
raw = project / "data/raw"
out = project / "data/processed/explorer"
out.mkdir(parents=True, exist_ok=True)
seam = lambda lon: round((float(lon) + 180) % 360 - 180, 6)


def save(name, data):
    (out / name).write_text(json.dumps(data, ensure_ascii=False, allow_nan=False, separators=(",", ":")), encoding="utf-8")


def feature_collection(features):
    return {"type": "FeatureCollection", "features": features}


def read_zip(name):
    return gpd.read_file(f"zip://{(raw / (name + '.zip')).as_posix()}")


def distance(a, b):
    lon1, lat1, lon2, lat2 = map(math.radians, (*a[:2], *b[:2]))
    h = math.sin((lat2-lat1)/2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin((lon2-lon1)/2)**2
    return 6792.38 * math.asin(min(1, math.sqrt(h)))


tile_dir = out / "viking"
tile_dir.mkdir(exist_ok=True)
for index in range(2):
    Image.open(raw / f"viking{index}.png").convert("RGB").save(tile_dir / f"{index}.jpg", quality=94)

gazetteer = []
for row in read_zip("names").itertuples():
    gazetteer.append({"name": str(row.name), "type": str(row.type), "lat": round(row.geometry.y, 6),
                      "lon": seam(row.geometry.x), "source": str(row.link)})
save("gazetteer.json", sorted(gazetteer, key=lambda place: place["name"]))

for rover in ("perseverance", "curiosity", "spirit", "opportunity"):
    features = []
    if rover in {"spirit", "opportunity"}:
        for row in read_zip(rover).itertuples():
            if row.geometry is None:
                continue
            parts = row.geometry.geoms if row.geometry.geom_type == "MultiLineString" else [row.geometry]
            for geom in parts:
                if geom.geom_type == "LineString" and len(geom.coords) > 1:
                    coords = [[seam(v[0]), round(v[1], 6)] for v in geom.coords]
                    features.append({"type": "Feature", "geometry": {"type": "LineString", "coordinates": coords},
                                     "properties": {"sol": int(row.END_SOL)}})
    else:
        nasa = json.loads((raw / f"{rover}.json").read_text(encoding="utf-8-sig"))
        for feature in nasa["features"]:
            geometry = feature.get("geometry")
            if not geometry:
                continue
            parts = geometry["coordinates"] if geometry["type"] == "MultiLineString" else [geometry["coordinates"]]
            for part in parts:
                coords = [[seam(p[0]), round(p[1], 6)] for p in part]
                if len(coords) > 1:
                    value = feature["properties"].get("sol")
                    properties = {"sol": int(value)} if value is not None else {}
                    features.append({"type": "Feature", "geometry": {"type": "LineString", "coordinates": coords},
                                     "properties": properties})
    if not features:
        raise ValueError(f"No confirmed lines for {rover}")
    total = sum(distance(a,b) for f in features for a,b in zip(f["geometry"]["coordinates"], f["geometry"]["coordinates"][1:]))
    sols = [f["properties"]["sol"] for f in features if "sol" in f["properties"]]
    save(f"{rover}.geojson", {**feature_collection(features), "distance_km": round(total, 2),
                             "sol_range": [min(sols), max(sols)] if sols else None,
                             "center": features[len(features)//2]["geometry"]["coordinates"][0]})

gdb = raw / "Nili.gdb"
jezero = gpd.read_file(gdb, layer="GeoUnits_v1", columns=["symbol", "name"]).rename(columns={"symbol":"unit"})
jezero.geometry = jezero.geometry.simplify(20, preserve_topology=True)
jezero = jezero.to_crs(CRS.from_user_input(jezero.crs).geodetic_crs)
data = json.loads(jezero.to_json(drop_id=True))
data.pop("crs", None)
save("jezero-geology.geojson", data)
for candidate in ("global-units.json", "global-geology.json"):
    geo_path = raw / candidate
    if not geo_path.exists():
        continue
    try:
        zones = gpd.read_file(geo_path)
    except Exception:
        continue
    if len(zones) < 1200 or any(abs(x) > 361 for x in zones.total_bounds):
        continue
    print("Global geology", zones.columns.tolist(), len(zones), zones.total_bounds)
    fields = {name.lower(): name for name in zones.columns}
    unit = next(fields[k] for k in ("unit", "unit_sym", "mapunit", "unit_symbol", "unitsymbol") if k in fields)
    title = next((fields[k] for k in ("unit_name", "unitname", "name", "unit_desc") if k in fields), unit)
    zones = zones[[unit, "geometry"]].assign(name=zones[title]).rename(columns={unit: "unit"})
    zones.geometry = zones.geometry.simplify(.045, preserve_topology=True)
    data = json.loads(zones.to_json(drop_id=True))
    data.pop("crs", None)
    save("global-geology.geojson", data)
    break
else:
    if (raw / "global-esri.json").exists():
        from shapely.geometry import mapping
        dataset = raw / "global-esri.json"
        result = json.loads(dataset.read_text(encoding="utf-8"))
        assert result.get("spatialReference", {}).get("wkid") == 104971
        assert len(result["features"]) == 1311 and not result.get("exceededTransferLimit")
        units = gpd.read_file(dataset)
        units.geometry = units.geometry.simplify(.025,preserve_topology=True)
        save("global-geology.geojson", feature_collection([
            {"type":"Feature","geometry":mapping(rec.geometry),"properties":{"unit":rec.Unit,"name":rec.UnitDesc}}
            for rec in units.itertuples() if rec.geometry and not rec.geometry.is_empty]))

observations = []
if (raw / "meda.csv").exists():
    rows = list(csv.DictReader((raw / "meda.csv").open(encoding="utf-8-sig")))
    valid = [r for r in rows if 100 < float(r["ATS_LOCAL_TEMP1"]) < 350]
    sample = valid[0]
    observations.append({"id":"meda", "point":[77.450885,18.444627], "sol":1,
                         "time":sample["LTST"][-8:], "value":round(float(sample["ATS_LOCAL_TEMP1"]) - 273.15, 2),
                         "unit":"°C", "instrument":"Perseverance · MEDA ATS, sensor 1",
                         "source":"https://atmos.nmsu.edu/PDS/data/PDS4/Mars2020/mars2020_meda/data_calibrated_env/sol_0000_0089/sol_0001/",
                         "location":"Jezero landing area · approximate rover location"})
if (raw / "rad-dose.txt").exists():
    with (raw / "rad-dose.txt").open(encoding="utf-8") as stream:
        header, first = (line.strip().split("\t") for line in (next(stream), next(stream)))
    # This export has an extra fractional day-of-year field before the Sol column.
    assert len(first) == len(header) + 1 and "DoseE_filtered" in header[-1]
    observations.append({"id":"radiation", "point":[137.4,-4.7], "sol":round(float(first[-3])),
                         "time":first[0], "value":round(float(first[-2]), 2),
                         "unit":"µGy/day", "instrument":"Curiosity · RAD E detector",
                         "source":"https://doi.org/10.5281/zenodo.20536564",
                         "location":"Gale Crater · regional archive marker with no precise measurement location"})
save("observations.json", observations)
