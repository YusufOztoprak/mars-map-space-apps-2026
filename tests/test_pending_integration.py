"""Implemented replacements for the former pending requirements.
Browser/device acceptance is tracked in docs/frontend-checklist.md, not fake skipped tests.
"""
import pytest
import numpy as np
from tests.test_backend_snapshot import backend, client

@pytest.mark.parametrize('backend', ['missing', 'corrupt'], indirect=True)
def test_unavailable_dem_returns_503(backend, client):
    response = client.post('/route', json={'start':{'lat':18.44,'lon':77.42},
                                          'end':{'lat':18.46,'lon':77.40}})
    assert response.status_code == 503
    assert response.is_json and response.json['error']

@pytest.mark.parametrize('backend', ['real'], indirect=True)
def test_real_route_stays_on_valid_cells(backend, client):
    response = client.post('/route', json={'start':{'lat':18.44,'lon':77.42},
                                          'end':{'lat':18.46,'lon':77.40}})
    assert response.status_code == 200
    for lon, lat in response.json['geometry']['coordinates']:
        cell = backend.lonlat_to_pixel(lat, lon)
        assert cell is not None
        assert np.isfinite(backend.elevation[cell])
        assert np.isfinite(backend.cost_grid[cell])
        assert backend.slope_deg[cell] <= 20

@pytest.mark.parametrize('backend', ['real'], indirect=True)
def test_projection_against_rasterio_reference(backend):
    from rasterio.warp import transform
    from rasterio.transform import rowcol
    assert backend.crs is not None
    lon, lat = 77.4, 18.45
    x, y = transform('+proj=longlat +R=3396190 +no_defs', backend.crs, [lon], [lat])
    assert backend.lonlat_to_pixel(lat,lon) == rowcol(backend.transform,x[0],y[0])
