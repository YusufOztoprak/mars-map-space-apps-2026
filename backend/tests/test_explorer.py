import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app import app
from routing import astar


def test_diagonal_does_not_cross_blocked_corner():
    assert astar(np.array([[1, np.inf], [np.inf, 1]]), (0, 0), (1, 1)) is None


def test_planetocentric_point_and_raster_products():
    with app.test_client() as client:
        meta = client.get("/api/explorer/meta").get_json()
        if not meta["ctx"] or not meta["global_dem"]:
            pytest.skip("CTX and MOLA files are required")
        local = client.get("/api/explorer/point?lat=18.45&lon=77.40").get_json()
        assert local["terrain"]["height"]["source"]["resolution_m"] == 20
        assert local["terrain"]["slope"]["value"] > 0
        assert local["geology"]["unit"] and local["historical_dust"]["kind"] == "historical_model"
        distant = client.get("/api/explorer/point?lat=-4.7&lon=137.4").get_json()
        assert distant["terrain"]["height"]["source"]["scope"] == "Global Mars"
        assert client.get("/api/explorer/raster/height/0/0/0.png").data.startswith(b"\x89PNG")
        assert len(client.get("/api/explorer/terrain/0/0/0.bin").data) == 33 * 33 * 4


def test_jezero_alternatives_disclose_missing_data():
    with app.test_client() as client:
        if not client.get("/api/explorer/meta").get_json()["ctx"]:
            pytest.skip("CTX is required")
        response = client.post("/api/explorer/routes", json={
            "start": {"lon": 77.42, "lat": 18.44}, "end": {"lon": 77.40, "lat": 18.46},
            "factors": ["slope", "roughness"], "coverage": ["radiation", "dust", "temperature"]})
        assert response.status_code == 200
        result = response.get_json()
        assert len(result["features"]) == 3
        assert result["source"]["resolution_m"] == 20
        first, *_, last = (f["properties"] for f in result["features"])
        assert first["distance_km"] < last["distance_km"]
        assert first["max_slope_deg"] > last["max_slope_deg"]
        for feature in result["features"]:
            p = feature["properties"]
            assert p["max_slope_deg"] <= result["slope_limit"]
            assert p["coverage"]["slope"]["percent"] == 100
            assert p["coverage"]["radiation"]["status"] == "missing"
            assert p["gaps"]["radiation"] == [[0, len(feature["geometry"]["coordinates"])-1]]
            assert len(p["elevations_m"]) == len(feature["geometry"]["coordinates"])


def test_global_route_and_invalid_factors():
    with app.test_client() as client:
        if not client.get("/api/explorer/meta").get_json()["global_dem"]:
            pytest.skip("MOLA is required")
        payload = {"start":{"lon":179.8,"lat":10}, "end":{"lon":-179.6,"lat":10},
                   "coverage":["radiation"]}
        response = client.post("/api/explorer/routes", json=payload)
        assert response.status_code == 200
        result = response.get_json()
        assert result["source"]["scope"] == "Global Mars"
        assert result["features"][0]["properties"]["distance_km"] < 100
        bad = client.post("/api/explorer/routes", json={**payload, "factors":["radiation"]})
        assert bad.status_code == 400


def test_hirise_window_selected_automatically():
    with app.test_client() as client:
        meta = client.get("/api/explorer/meta").get_json()
        if not meta["hirise"]:
            pytest.skip("HiRISE stereo window is required")
        point = client.get("/api/explorer/point?lat=18.45&lon=77.41").get_json()
        assert point["terrain"]["height"]["source"]["resolution_m"] == 1.02
        response = client.post("/api/explorer/routes", json={
            "start":{"lat":18.45,"lon":77.41}, "end":{"lat":18.4504,"lon":77.4104},
            "factors":["slope","roughness"]})
        assert response.status_code == 200
        assert response.get_json()["source"]["resolution_m"] == 1.02


def test_explorer_reports_missing_terrain_without_failing(monkeypatch, tmp_path):
    import explorer
    from flask import Flask
    monkeypatch.setattr(explorer, "DATA", tmp_path)
    isolated = Flask(__name__)
    explorer.register_explorer(isolated, {"height":None,"slope":None,"roughness":None})
    with isolated.test_client() as client:
        assert client.get("/api/explorer/meta").get_json()["global_dem"] is None
        point = client.get("/api/explorer/point?lat=18.45&lon=77.41")
        assert point.status_code == 200
        assert all(v is None for v in point.get_json()["terrain"].values())
        route = client.post("/api/explorer/routes",json={"start":{"lat":18.45,"lon":77.41},
                                                        "end":{"lat":18.46,"lon":77.42}})
        assert route.status_code == 422


@pytest.mark.parametrize('start,end',[
    ((67.149373,27.259329),(82.878283,10.875713)),
    ((-140,-35),(30,45)),
    ((10,89),(120,88.5)),
])
def test_distance_and_polar_limits_replaced_by_bounded_sampling(start,end):
    with app.test_client() as client:
        if not client.get('/api/explorer/meta').json['global_dem']:
            pytest.skip('Real MOLA is required')
        response=client.post('/api/explorer/routes',json={
            'start':dict(zip(('lon','lat'),start)), 'end':dict(zip(('lon','lat'),end)),
            'coverage':['radiation']})
        assert response.status_code==200
        result=response.json
        assert result['source']['search_cells']<=80_000
        assert result['source']['routing_step_m']>=result['source']['resolution_m']
        for feature in result['features']:
            assert feature['properties']['max_slope_deg']<=20
            assert feature['properties']['coverage']['radiation']['status']=='missing'
            assert np.isfinite(np.asarray(feature['geometry']['coordinates'])).all()


def test_coarse_search_checks_barrier_between_native_nodes(monkeypatch):
    import explorer
    source={'id':'mola','scope':'Global Mars','resolution_m':1,'sampling_stride':3}
    class Terrain:
        def sample_global(self,key,lon,lat):
            values=np.zeros(np.shape(lon),dtype=float)
            if key=='slope':
                values[(np.isclose(lon,1)) & (np.isclose(lat,0))]=30
            return values
    grids={k:np.zeros((5,5)) for k in ('height','slope','roughness')}
    monkeypatch.setattr(explorer,'route_window',lambda *args:
        (grids,(0,0),(0,2),lambda r,c:(np.asarray(c)*3,np.asarray(r)*3),3,source))
    routes,_=explorer.candidate_routes(Terrain(),(0,0),(6,0),{'slope'},{'height'})
    assert routes
    for route in routes:
        coordinates=route['geometry']['coordinates']
        assert [1.0,0.0] not in coordinates
        assert route['properties']['max_slope_deg']==0


def test_coverage_cross_checks_point_and_categorical_raster():
    import io
    from PIL import Image

    locations = [(137.44, -4.59, "mola", 6), (77.40, 18.45, "ctx", 10),
                 (77.41, 18.45, "hirise", 12), (179.95, 9.9, "mola", 7),
                 (-179.95, 9.9, "mola", 7)]
    with app.test_client() as client:
        meta = client.get("/api/explorer/meta").json
        if not all(meta[name] for name in ("global_dem", "ctx", "hirise")):
            pytest.skip("MOLA, CTX and HiRISE are required")
        for lon, lat, expected, z in locations:
            size = 2**z * 256
            col = int((lon + 180) * size / 180)
            row = int((90 - lat) * size / 180)
            pixel_lon = (col + .5) * 180 / size - 180
            pixel_lat = 90 - (row + .5) * 180 / size
            point = client.get(f"/api/explorer/point?lat={pixel_lat}&lon={pixel_lon}&model=mola").json
            coverage = point["elevation_coverage"]
            assert coverage["source"]["id"] == expected
            if pixel_lon < 0:
                wrapped = client.get(f"/api/explorer/point?lat={pixel_lat}&lon={pixel_lon + 360}").json
                assert wrapped["elevation_coverage"] == coverage
                assert wrapped["terrain"]["height"] == point["terrain"]["height"]
            prefix = f"/api/explorer/raster/coverage/{z}/{col // 256}/{row // 256}.png"
            response = client.get(prefix)
            assert client.get(prefix + "?model=ctx").data == response.data
            color = meta["elevation_coverage"]["colors"][coverage["id"]]
            with Image.open(io.BytesIO(response.data)) as image:
                assert image.getpixel((col % 256, row % 256)) == (*bytes.fromhex(color[1:]), 255)


def test_coverage_indicates_missing_and_interpolated_cells(monkeypatch, tmp_path):
    import explorer
    from rasterio.transform import from_origin

    monkeypatch.setattr(explorer, "DATA", tmp_path)
    local = {
        "height": np.array([[42, np.nan], [np.nan, np.nan]]),
        "transform": from_origin(0, 2, 1, 1),
        "to_xy": lambda lon, lat: (lon, lat),
    }
    terrain = explorer.Terrain(local)
    lon, lat = np.array([.5, 1.5, 2.5]), np.array([1.5, 1.5, 1.5])
    assert [tuple(explorer.COVERAGE_COLORS)[i] for i in terrain.elevation_coverage(lon, lat)] == [
        "ctx", "missing", "missing"
    ]
    terrain.density = 4
    terrain.globals[4] = np.full((720, 1440), 10, dtype=np.int16)
    terrain.observation_counts = np.zeros((720, 1440), dtype=np.int16)
    terrain.observation_counts[354, 6] = 3
    assert [tuple(explorer.COVERAGE_COLORS)[i] for i in terrain.elevation_coverage(lon, lat)] == [
        "ctx", "mola_measured", "mola_interpolated"
    ]
