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
