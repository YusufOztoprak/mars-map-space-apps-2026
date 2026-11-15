"""Read-only review of an exact Git revision, never merge or rewrite team code."""
import importlib.util
import subprocess
import sys
import os
from pathlib import Path

import pytest

REVISION = 'e880bcc36e7f2b7b6a8bf2c9ec3dd3f92bb73583'  # main at review time
ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope='module')
def backend(tmp_path_factory):
    pytest.importorskip('flask')
    pytest.importorskip('flask_cors')
    pytest.importorskip('numpy')
    pytest.importorskip('rasterio')
    folder = tmp_path_factory.mktemp('backend_snapshot')
    for name in ('app', 'dem_utils', 'routing'):
        if os.environ.get('BACKEND_SNAPSHOT_DIR'):
            (folder / f'{name}.py').write_bytes((Path(os.environ['BACKEND_SNAPSHOT_DIR']) / f'{name}.py').read_bytes())
            continue
        result = subprocess.run(['git', 'show', f'{REVISION}:backend/{name}.py'],
                                cwd=ROOT, capture_output=True)
        if result.returncode:
            pytest.skip(f'Historical Git snapshot {REVISION} is unavailable in this checkout')
        (folder / f'{name}.py').write_bytes(result.stdout)
    saved = {name: sys.modules.pop(name, None) for name in ('dem_utils', 'routing')}
    sys.path.insert(0, str(folder))
    try:
        # Patch only the I/O boundary before app import. Real route, projection,
        # slope and A* code remain untouched. This is NOT a real DEM load test.
        import math
        import numpy as np
        import dem_utils
        from rasterio.transform import from_origin
        x = 3396190 * math.radians(77.39) * math.cos(math.radians(18.4663))
        y = 3396190 * math.radians(18.42)
        with pytest.MonkeyPatch.context() as patch:
            patch.setattr(dem_utils, 'load_dem', lambda path: (
                np.zeros((200, 200)), from_origin(x, y, 20, 20), None, None))
            spec = importlib.util.spec_from_file_location('review_backend', folder / 'app.py')
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
        module.app.config.update(TESTING=True)
        yield module
    finally:
        sys.path.remove(str(folder))
        for name, previous in saved.items():
            sys.modules.pop(name, None)
            if previous is not None:
                sys.modules[name] = previous


@pytest.fixture
def client(backend):
    return backend.app.test_client()


def request_body():
    return {'start': {'lat': 18.4, 'lon': 77.4}, 'end': {'lat': 18.41, 'lon': 77.41}}


def test_actual_success(client):
    from tests.contract_helpers import validate_route
    response = client.post('/route', json=request_body())
    assert response.status_code == 200
    validate_route(response.get_json())


@pytest.mark.parametrize('body', [{}, {'start': {}}, {'end': {}},
    {'start': {'lat': 18.4}, 'end': {'lat': 18.4, 'lon': 77.4}},
    {'start': {'lat': 'bad', 'lon': 77.4}, 'end': {'lat': 18.4, 'lon': 77.4}}])
def test_invalid_request(client, body):
    response = client.post('/route', json=body)
    assert response.status_code == 400
    assert response.get_json()['error']


def test_outside_coverage(client):
    body = request_body()
    body['start']['lon'] = 0
    assert client.post('/route', json=body).status_code == 422


def test_no_path(client, backend, monkeypatch):
    import numpy as np
    monkeypatch.setattr(backend, 'cost_grid', np.full_like(backend.cost_grid, np.inf))
    response = client.post('/route', json=request_body())
    assert response.status_code == 422
    assert response.get_json()['error']


def test_allowed_preflight(client):
    response = client.options('/route', headers={'Origin': 'http://localhost:8000',
        'Access-Control-Request-Method': 'POST', 'Access-Control-Request-Headers': 'Content-Type'})
    assert response.status_code < 400
    assert response.headers.get('Access-Control-Allow-Origin') == 'http://localhost:8000'
    assert 'POST' in response.headers.get('Access-Control-Allow-Methods', '')


def test_unapproved_origin_rejected(client):
    response = client.options('/route', headers={'Origin': 'https://unapproved.example',
        'Access-Control-Request-Method': 'POST'})
    assert 'Access-Control-Allow-Origin' not in response.headers


def test_numeric_strings_rejected(client):
    body = request_body()
    body['start'] = {'lat': '18.4', 'lon': '77.4'}
    assert client.post('/route', json=body).status_code == 400


def test_same_cell_valid_linestring(client):
    from tests.contract_helpers import validate_route
    body = request_body()
    body['end'] = body['start'].copy()
    response = client.post('/route', json=body)
    if response.status_code == 200:
        validate_route(response.get_json())
    else:
        assert response.status_code in (400, 422)


def test_unexpected_error_json(client, backend, monkeypatch):
    def fail(*args, **kwargs):
        raise RuntimeError('injected calculation failure')
    monkeypatch.setattr(backend, 'astar', fail)
    monkeypatch.setitem(backend.app.config, 'PROPAGATE_EXCEPTIONS', False)
    response = client.post('/route', json=request_body())
    assert response.status_code == 500
    assert response.is_json


def test_identical_point_has_zero_travel(client):
    body = request_body()
    body['end'] = body['start'].copy()
    response = client.post('/route', json=body)
    assert response.status_code == 200
    properties = response.get_json()['properties']
    assert properties['distance_km'] == 0
    assert properties['estimated_time_hours'] == 0


@pytest.mark.parametrize('value', [True, False, float('nan'), float('inf'), -float('inf')])
def test_nonfinite_and_bool_rejected(client, value):
    body = request_body()
    body['start']['lat'] = value
    assert client.post('/route', json=body).status_code == 400


def test_twenty_degree_threshold(backend):
    import numpy as np
    routing = sys.modules['routing']
    assert routing.SAFETY_THRESHOLD_DEG == 20
    cost = routing.build_cost_grid(np.array([[19.9, 20., 20.1]]), 20)
    assert np.isfinite(cost[0, :2]).all()
    assert np.isinf(cost[0, 2])


def test_synthetic_grid_alternative_and_blocked(backend):
    import numpy as np
    routing = sys.modules['routing']
    dem = sys.modules['dem_utils']
    # Synthetic ramp: 2m rise per 1m cell, never real Mars data.
    elevation = np.tile(np.arange(5, dtype=float) * 2, (5, 1))
    slope = dem.compute_slope(elevation, 1)
    assert np.all(slope > routing.SAFETY_THRESHOLD_DEG)
    assert np.all(np.isinf(routing.build_cost_grid(slope, 1)))
    slopes = np.zeros((5, 5))
    slopes[:4, 2] = 80
    costs = routing.build_cost_grid(slopes, 25)
    path = routing.astar(costs, (2, 0), (2, 4))
    assert path[0] == (2, 0) and path[-1] == (2, 4)
    assert all(np.isfinite(costs[cell]) for cell in path)
    assert (4, 2) in path
    costs[4, 2] = np.inf
    assert routing.astar(costs, (2, 0), (2, 4)) is None
